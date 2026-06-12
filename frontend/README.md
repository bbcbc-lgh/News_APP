# Vue + FastAPI 项目

## 项目结构
- d:\FastAPI - Python FastAPI 后端
- d:\Vue - Vue.js 前端

## API 接口约定
- 后端地址: `http://localhost:8000`
- API 前缀: `/api/v1`
- 响应格式:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {}
  }
  ```

## 开发脚本
- 后端启动: `cd d:/FastAPI && uvicorn main:app --reload`
- 前端启动: `cd d:/Vue && npm run dev`