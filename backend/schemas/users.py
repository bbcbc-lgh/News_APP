from typing import Optional
from pydantic import BaseModel, Field

# 用户注册请求体模型
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=30)

# 用户登录请求体模型
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=30)

# 用户信息更新请求体模型
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

# 用户密码修改请求体模型
class UserPasswordChange(BaseModel):
    oldPassword: str
    newPassword: str = Field(..., min_length=6, max_length=30)

# 用户信息响应模型
class UserInfoResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


# 头像上传请求体：前端将图片转为 base64 data URI 后提交
class AvatarUpload(BaseModel):
    image: str  # 格式：data:image/png;base64,xxxxx
