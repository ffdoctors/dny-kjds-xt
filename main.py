"""
东南亚跨境电商数据分析系统 - Railway 稳定部署版
"""
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==================== FastAPI 应用 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="东南亚跨境电商数据分析系统",
    version="1.0.0",
    lifespan=lifespan
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路由（解决Railway 404报错）
@app.get("/")
async def root():
    return {
        "status": "✅ 服务运行成功",
        "message": "东南亚跨境电商系统部署完成",
        "接口文档": "/docs",
        "健康检查": "/api/health"
    }

# 健康检查（Railway 专用）
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# ==================== 服务启动（适配Railway端口） ====================
if __name__ == "__main__":
    import uvicorn
    # 自动读取Railway端口，无则使用8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)