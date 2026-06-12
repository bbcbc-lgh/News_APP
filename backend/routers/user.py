from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
import uuid
import os
import base64
from config.database_conf import get_db
from config.env import get
from utils.response import success_response
from utils.security import auth_rate_limit, get_current_user
from crud.users import (
    get_user_by_username,
    create_user,
    create_token,
    delete_token,
    update_user,
    update_password,
)
from schemas.users import UserRegister, UserLogin, UserUpdate, UserPasswordChange, AvatarUpload

router = APIRouter(prefix="/api/user", tags=["user"])

# 哈希密码
def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# 验证密码是否匹配哈希值
def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# 注册新用户（限流：每 IP 每分钟最多 10 次）
@router.post("/register")
async def register(body: UserRegister, db: AsyncSession = Depends(get_db), _=Depends(auth_rate_limit)):
    existing = await get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    password_hash = _hash(body.password)
    user = await create_user(db, body.username, password_hash)
    token = await create_token(db, user.id)
    return success_response({
            "token": token,
            "userInfo": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
            },
        }, "注册成功")

# 用户登录（限流：每 IP 每分钟最多 10 次，防止暴力破解）
@router.post("/login")
async def login(body: UserLogin, db: AsyncSession = Depends(get_db), _=Depends(auth_rate_limit)):
    user = await get_user_by_username(db, body.username)
    if not user or not _verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = await create_token(db, user.id)
    return success_response({
            "token": token,
            "userInfo": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "bio": user.bio,
            },
        }, "登录成功")

# 获取当前用户信息
@router.get("/info")
async def get_info(current_user=Depends(get_current_user)):
    return success_response({
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "avatar": current_user.avatar,
            "gender": current_user.gender,
            "bio": current_user.bio,
        }, "获取成功")

# 更新用户信息
@router.put("/update")
async def update_info(
    body: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_fields = {k: v for k, v in body.model_dump().items() if v is not None}
    user = await update_user(db, current_user.id, **update_fields)
    return success_response({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "gender": user.gender,
            "bio": user.bio,
        }, "更新成功")

# 修改用户密码
@router.put("/password")
async def change_password(
    body: UserPasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(body.oldPassword, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    new_hash = _hash(body.newPassword)
    await update_password(db, current_user.id, new_hash)
    return success_response(message="密码修改成功")


# 用户登出，使当前 token 立即失效
@router.post("/logout")
async def logout(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    await delete_token(db, authorization)
    return success_response(message="退出登录成功")


# 头像上传：接收 base64 编码的图片数据，解码后保存到本地，返回可访问的 URL
# 前端需将图片转为 data:image/xxx;base64,<data> 格式提交
@router.post("/avatar")
async def upload_avatar(
    body: AvatarUpload,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 解析 data URI 格式：data:image/png;base64,xxxxx
    if "," not in body.image:
        raise HTTPException(status_code=400, detail="图片格式错误，需要 base64 编码的 data URI")

    header, encoded = body.image.split(",", 1)
    # 从 header 中提取 MIME 类型，如 data:image/png;base64
    mime_type = header.split(":")[1].split(";")[0] if ":" in header else ""
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if mime_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、GIF、WEBP 格式的图片")

    # 解码 base64 数据
    try:
        content = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=400, detail="base64 数据解码失败")

    # 限制文件大小：最大 5MB
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    # 根据 MIME 类型确定扩展名
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
    ext = ext_map.get(mime_type, ".jpg")

    # 用 UUID 生成唯一文件名，防止文件名冲突
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(os.path.dirname(__file__), "..", "static", "avatars")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    with open(save_path, "wb") as f:
        f.write(content)

    # 构造可访问的头像 URL
    base_url = get("BASE_URL", "http://localhost:8000")
    avatar_url = f"{base_url}/static/avatars/{filename}"

    # 更新用户头像字段
    await update_user(db, current_user.id, avatar=avatar_url)
    return success_response({"avatar": avatar_url}, "头像上传成功")
