"""
东南亚跨境电商数据分析系统 - Railway 稳定部署版
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import BASE_DIR
from database import engine, Base
from models import (
    UploadRecord, SaleRecord, AdRecord,
    InventoryRecord, FilterConfig, AuditLog
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 创建所有数据库表
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="东南亚跨境电商数据分析系统",
    version="1.0.0",
    lifespan=lifespan
)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from routers import dashboard, sales, ads, inventory, upload, export

app.include_router(dashboard.router, prefix="/api", tags=["仪表盘"])
app.include_router(sales.router, prefix="/api", tags=["销售数据"])
app.include_router(ads.router, prefix="/api", tags=["广告数据"])
app.include_router(inventory.router, prefix="/api", tags=["库存数据"])
app.include_router(upload.router, prefix="/api", tags=["数据上传"])
app.include_router(export.router, prefix="/api", tags=["数据导出"])


@app.get("/")
async def root():
    return {
        "status": "✅ 服务运行成功",
        "message": "东南亚跨境电商系统部署完成",
        "接口文档": "/docs",
        "健康检查": "/api/health"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
