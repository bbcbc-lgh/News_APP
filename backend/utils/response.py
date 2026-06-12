"""
统一响应格式工具
- success_response: 成功响应，固定 code=200
- http_exception_handler: HTTPException 统一错误格式
- validation_exception_handler: 参数校验失败（422）统一格式
"""
from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse


def success_response(data=None, message="success"):
    """成功响应，统一返回 {code, message, data} 结构"""
    return {"code": 200, "message": message, "data": data}


async def http_exception_handler(request: Request, exc: HTTPException):
    """将 HTTPException 转为与成功响应一致的 {code, message, data} 结构"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验失败时提取第一条错误信息作为 message，保持格式统一"""
    first_error = exc.errors()[0] if exc.errors() else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "参数错误")
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": f"{field}: {msg}", "data": None},
    )
