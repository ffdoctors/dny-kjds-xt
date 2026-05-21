"""
东南亚跨境电商数据分析系统 - Python FastAPI 后端
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from jose import JWTError, jwt
from passlib.context import CryptContext
import pandas as pd
import xlsxwriter
from io import BytesIO

# ==================== 配置 ====================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")
JWT_SECRET = os.getenv("JWT_SECRET", "ecommerce-secret-2024")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ==================== 数据库 ====================

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 模型 ====================

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="free")
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
    sales_data = relationship("SalesData", back_populates="tenant")
    inventory = relationship("Inventory", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(50), default="user")
    status = Column(String(50), default="active")
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="users")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="audit_logs")


class SalesData(Base):
    __tablename__ = "sales_data"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    date = Column(String(10), nullable=False)
    platform = Column(String(50), nullable=False)
    country = Column(String(50), nullable=False)
    product = Column(String(255), nullable=False)
    gmv = Column(Float, default=0)
    gsv = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    refund_rate = Column(Float, default=0)
    ad_cost = Column(Float, default=0)
    roi = Column(Float, default=0)
    orders_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="sales_data")


class AdData(Base):
    __tablename__ = "ad_data"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    date = Column(String(10), nullable=False)
    platform = Column(String(50), nullable=False)
    campaign_name = Column(String(255))
    spend = Column(Float, default=0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0)
    cpc = Column(Float, default=0)
    conversions = Column(Integer, default=0)
    roas = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sku = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)
    platform = Column(String(50))
    warehouse = Column(String(100))
    quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=10)
    max_stock = Column(Integer, default=1000)
    status = Column(String(50), default="normal")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="inventory")


class FilterConfig(Base):
    __tablename__ = "filter_configs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    config_type = Column(String(50), nullable=False)
    config_name = Column(String(100), nullable=False)
    config_value = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Pydantic 模型 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    tenantId: str
    tenantName: str
    plan: str


class DashboardSummary(BaseModel):
    totalGmv: float
    totalGsv: float
    totalRefund: float
    totalAdCost: float
    totalOrders: int
    avgRoi: float
    gmvChange: float


class SalesDataCreate(BaseModel):
    date: str
    platform: str
    country: str
    product: str
    gmv: float = 0
    gsv: float = 0
    refund_amount: float = 0
    ad_cost: float = 0
    roi: float = 0
    orders_count: int = 0


# ==================== 依赖 ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权访问")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    
    return {
        "userId": str(user.id),
        "username": user.username,
        "role": user.role,
        "tenantId": str(user.tenant_id),
        "tenantName": user.tenant.name,
        "plan": user.tenant.plan
    }


# ==================== 审计日志 ====================

def create_audit_log(db: Session, user_data: dict, action: str, resource: str, resource_id: str = None, details: dict = None):
    log = AuditLog(
        tenant_id=user_data.get("tenantId"),
        user_id=user_data.get("userId"),
        username=user_data.get("username"),
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details
    )
    db.add(log)
    db.commit()


# ==================== 初始化数据 ====================

def init_default_data(db: Session):
    """初始化默认租户和用户"""
    # 检查是否已有租户
    existing_tenant = db.query(Tenant).filter(Tenant.code == "default").first()
    
    if not existing_tenant:
        # 创建默认租户
        tenant = Tenant(
            id=uuid.uuid4(),
            name="默认租户",
            code="default",
            plan="enterprise",
            status="active"
        )
        db.add(tenant)
        db.flush()
        
        # 创建管理员
        admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="admin",
            password=pwd_context.hash("admin123"),
            email="admin@example.com",
            role="admin",
            status="active"
        )
        db.add(admin)
        
        # 创建演示用户
        demo = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="demo",
            password=pwd_context.hash("demo123"),
            email="demo@example.com",
            role="user",
            status="active"
        )
        db.add(demo)
        
        db.commit()
        print("✅ 默认租户和管理员创建完成")
        return tenant.id
    
    return existing_tenant.id


def seed_demo_data(db: Session, tenant_id: uuid.UUID):
    """填充演示数据"""
    # 检查是否已有数据
    existing = db.query(SalesData).filter(SalesData.tenant_id == tenant_id).first()
    if existing:
        print("📊 数据已存在，跳过填充")
        return
    
    print("🌱 填充演示数据...")
    
    platforms = ["Shopee", "Lazada", "TikTok"]
    countries = ["泰国", "马来西亚"]
    products = [
        "蓝牙耳机 TWS-01", "智能手环 Band-Pro", "移动电源 20000mAh",
        "数据线 Type-C 3条装", "手机壳 透明防摔", "无线充电器 15W",
        "便携音箱 Mini", "运动相机 CAM-4K"
    ]
    
    count = 0
    for i in range(29, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for platform in platforms:
            for country in countries:
                for product in products:
                    base_gmv = 5000 + (hash(product + date + platform) % 15000)
                    gsv = base_gmv * (1 + (hash(date) % 100) / 500)
                    refund_rate = (hash(product) % 800) / 100
                    refund_amount = base_gmv * refund_rate / 100
                    ad_cost = base_gmv * (0.1 + (hash(country) % 15) / 100)
                    roi = 2 + (hash(product + country) % 400) / 100
                    
                    sale = SalesData(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        date=date,
                        platform=platform,
                        country=country,
                        product=product,
                        gmv=round(base_gmv, 2),
                        gsv=round(gsv, 2),
                        refund_amount=round(refund_amount, 2),
                        refund_rate=round(refund_rate, 2),
                        ad_cost=round(ad_cost, 2),
                        roi=round(roi, 2),
                        orders_count=50 + (hash(product) % 200)
                    )
                    db.add(sale)
                    count += 1
    
    db.commit()
    print(f"✅ 销售数据: {count} 条")


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_default_data(db)
        tenant_id = db.query(Tenant).filter(Tenant.code == "default").first().id
        seed_demo_data(db, tenant_id)
    finally:
        db.close()
    yield
    # 关闭时清理

app = FastAPI(
    title="东南亚跨境电商数据分析系统",
    description="企业级电商数据分析 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 认证接口 ====================

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == request.username,
        User.status == "active"
    ).first()
    
    if not user or not pwd_context.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 更新最后登录
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 审计日志
    create_audit_log(db, {"userId": str(user.id), "username": user.username, "tenantId": str(user.tenant_id)}, "LOGIN", "auth")
    
    # 生成Token
    token = jwt.encode({
        "userId": str(user.id),
        "username": user.username,
        "role": user.role,
        "tenantId": str(user.tenant_id),
        "tenantName": user.tenant.name,
        "plan": user.tenant.plan
    }, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenantId": str(user.tenant_id),
            "tenantName": user.tenant.name,
            "plan": user.tenant.plan
        }
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)


# ==================== 仪表盘接口 ====================

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    period: str = "30",
    platform: str = "all",
    country: str = "all",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"])
    
    if period != "all":
        days = int(period)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = query.filter(SalesData.date >= start_date)
    
    if platform != "all":
        query = query.filter(SalesData.platform == platform)
    
    if country != "all":
        query = query.filter(SalesData.country == country)
    
    sales = query.all()
    
    total_gmv = sum(s.gmv for s in sales)
    total_gsv = sum(s.gsv for s in sales)
    total_refund = sum(s.refund_amount for s in sales)
    total_ad_cost = sum(s.ad_cost for s in sales)
    total_orders = sum(s.orders_count for s in sales)
    avg_roi = sum(s.roi for s in sales) / len(sales) if sales else 0
    
    return DashboardSummary(
        totalGmv=round(total_gmv, 2),
        totalGsv=round(total_gsv, 2),
        totalRefund=round(total_refund, 2),
        totalAdCost=round(total_ad_cost, 2),
        totalOrders=total_orders,
        avgRoi=round(avg_roi, 2),
        gmvChange=0
    )


@app.get("/api/dashboard/sales-trend")
async def get_sales_trend(
    period: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    start_date = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")
    
    results = db.query(
        SalesData.date,
        db.func.sum(SalesData.gmv).label("gmv"),
        db.func.sum(SalesData.orders_count).label("orders")
    ).filter(
        SalesData.tenant_id == current_user["tenantId"],
        SalesData.date >= start_date
    ).group_by(SalesData.date).order_by(SalesData.date).all()
    
    return [{"date": r.date, "gmv": float(r.gmv), "orders": r.orders} for r in results]


@app.get("/api/dashboard/platform-stats")
async def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = db.query(
        SalesData.platform,
        db.func.sum(SalesData.gmv).label("gmv"),
        db.func.sum(SalesData.orders_count).label("orders")
    ).filter(
        SalesData.tenant_id == current_user["tenantId"]
    ).group_by(SalesData.platform).all()
    
    return [{"platform": r.platform, "gmv": float(r.gmv), "orders": r.orders} for r in results]


@app.get("/api/dashboard/country-stats")
async def get_country_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = db.query(
        SalesData.country,
        db.func.sum(SalesData.gmv).label("gmv"),
        db.func.count(SalesData.product.distinct()).label("product_count")
    ).filter(
        SalesData.tenant_id == current_user["tenantId"]
    ).group_by(SalesData.country).all()
    
    return [{"country": r.country, "gmv": float(r.gmv), "product_count": r.product_count} for r in results]


@app.get("/api/dashboard/product-rank")
async def get_product_rank(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = db.query(
        SalesData.product,
        db.func.sum(SalesData.gmv).label("gmv"),
        db.func.sum(SalesData.orders_count).label("orders")
    ).filter(
        SalesData.tenant_id == current_user["tenantId"]
    ).group_by(SalesData.product).order_by(db.func.sum(SalesData.gmv).desc()).limit(10).all()
    
    return [{"product": r.product, "gmv": float(r.gmv), "orders": r.orders} for r in results]


@app.get("/api/dashboard/daily")
async def get_daily_data(
    period: str = "30",
    platform: str = "all",
    country: str = "all",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"])
    
    if period != "all":
        days = int(period)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = query.filter(SalesData.date >= start_date)
    
    if platform != "all":
        query = query.filter(SalesData.platform == platform)
    
    if country != "all":
        query = query.filter(SalesData.country == country)
    
    sales = query.order_by(SalesData.date.desc()).limit(200).all()
    
    return [
        {
            "date": s.date,
            "platform": s.platform,
            "country": s.country,
            "product": s.product,
            "gmv": s.gmv,
            "gsv": s.gsv,
            "refund_amount": s.refund_amount,
            "refund_rate": s.refund_rate,
            "ad_cost": s.ad_cost,
            "roi": s.roi
        }
        for s in sales
    ]


# ==================== 销售数据接口 ====================

@app.get("/api/sales")
async def get_sales(
    page: int = 1,
    limit: int = 50,
    platform: str = None,
    country: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"])
    
    if platform:
        query = query.filter(SalesData.platform == platform)
    if country:
        query = query.filter(SalesData.country == country)
    if date_from:
        query = query.filter(SalesData.date >= date_from)
    if date_to:
        query = query.filter(SalesData.date <= date_to)
    
    total = query.count()
    sales = query.order_by(SalesData.date.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "data": [
            {
                "id": str(s.id),
                "date": s.date,
                "platform": s.platform,
                "country": s.country,
                "product": s.product,
                "gmv": s.gmv,
                "gsv": s.gsv,
                "refund_amount": s.refund_amount,
                "refund_rate": s.refund_rate,
                "ad_cost": s.ad_cost,
                "roi": s.roi,
                "orders_count": s.orders_count
            }
            for s in sales
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@app.post("/api/sales")
async def create_sales(
    data: SalesDataCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    refund_rate = (data.refund_amount / data.gmv * 100) if data.gmv > 0 else 0
    
    sale = SalesData(
        id=uuid.uuid4(),
        tenant_id=current_user["tenantId"],
        date=data.date,
        platform=data.platform,
        country=data.country,
        product=data.product,
        gmv=data.gmv,
        gsv=data.gsv,
        refund_amount=data.refund_amount,
        refund_rate=round(refund_rate, 2),
        ad_cost=data.ad_cost,
        roi=data.roi,
        orders_count=data.orders_count
    )
    db.add(sale)
    db.commit()
    
    create_audit_log(db, current_user, "CREATE_SALE", "sales", str(sale.id))
    
    return {"id": str(sale.id), "message": "创建成功"}


@app.delete("/api/sales/{sale_id}")
async def delete_sales(
    sale_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    sale = db.query(SalesData).filter(
        SalesData.id == sale_id,
        SalesData.tenant_id == current_user["tenantId"]
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="数据不存在")
    
    db.delete(sale)
    db.commit()
    
    create_audit_log(db, current_user, "DELETE_SALE", "sales", sale_id)
    
    return {"message": "删除成功"}


# ==================== 广告数据接口 ====================

@app.get("/api/ads")
async def get_ads(
    page: int = 1,
    limit: int = 50,
    platform: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(AdData).filter(AdData.tenant_id == current_user["tenantId"])
    
    if platform:
        query = query.filter(AdData.platform == platform)
    
    ads = query.order_by(AdData.date.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "data": [
            {
                "id": str(a.id),
                "date": a.date,
                "platform": a.platform,
                "campaign_name": a.campaign_name,
                "spend": a.spend,
                "impressions": a.impressions,
                "clicks": a.clicks,
                "ctr": a.ctr,
                "cpc": a.cpc,
                "conversions": a.conversions,
                "roas": a.roas
            }
            for a in ads
        ],
        "total": len(ads),
        "page": page,
        "limit": limit
    }


# ==================== 库存接口 ====================

@app.get("/api/inventory")
async def get_inventory(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    items = db.query(Inventory).filter(Inventory.tenant_id == current_user["tenantId"]).order_by(Inventory.sku).all()
    
    return [
        {
            "id": str(i.id),
            "sku": i.sku,
            "product_name": i.product_name,
            "platform": i.platform,
            "warehouse": i.warehouse,
            "quantity": i.quantity,
            "min_stock": i.min_stock,
            "max_stock": i.max_stock,
            "status": i.status
        }
        for i in items
    ]


@app.post("/api/inventory")
async def create_inventory(
    sku: str = Form(...),
    product_name: str = Form(...),
    platform: str = Form(""),
    warehouse: str = Form(""),
    quantity: int = Form(100),
    min_stock: int = Form(20),
    max_stock: int = Form(500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    existing = db.query(Inventory).filter(
        Inventory.tenant_id == current_user["tenantId"],
        Inventory.sku == sku
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="SKU已存在")
    
    status = "low" if quantity < min_stock else ("high" if quantity > max_stock else "normal")
    
    item = Inventory(
        id=uuid.uuid4(),
        tenant_id=current_user["tenantId"],
        sku=sku,
        product_name=product_name,
        platform=platform,
        warehouse=warehouse,
        quantity=quantity,
        min_stock=min_stock,
        max_stock=max_stock,
        status=status
    )
    db.add(item)
    db.commit()
    
    create_audit_log(db, current_user, "CREATE_INVENTORY", "inventory", str(item.id))
    
    return {"id": str(item.id), "message": "创建成功"}


# ==================== 筛选配置接口 ====================

@app.get("/api/filters")
async def get_filters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    items = db.query(FilterConfig).filter(FilterConfig.tenant_id == current_user["tenantId"]).all()
    
    return [
        {
            "id": str(i.id),
            "config_type": i.config_type,
            "config_name": i.config_name,
            "config_value": i.config_value,
            "is_default": i.is_default
        }
        for i in items
    ]


@app.post("/api/filters")
async def create_filter(
    config_type: str = Form(...),
    config_name: str = Form(...),
    config_value: str = Form(...),
    is_default: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = FilterConfig(
        id=uuid.uuid4(),
        tenant_id=current_user["tenantId"],
        config_type=config_type,
        config_name=config_name,
        config_value=config_value,
        is_default=is_default
    )
    db.add(item)
    db.commit()
    
    create_audit_log(db, current_user, "CREATE_FILTER", "filters", str(item.id))
    
    return {"id": str(item.id), "message": "创建成功"}


@app.delete("/api/filters/{filter_id}")
async def delete_filter(
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = db.query(FilterConfig).filter(
        FilterConfig.id == filter_id,
        FilterConfig.tenant_id == current_user["tenantId"]
    ).first()
    
    if item:
        db.delete(item)
        db.commit()
        create_audit_log(db, current_user, "DELETE_FILTER", "filters", filter_id)
    
    return {"message": "删除成功"}


# ==================== 审计日志接口 ====================

@app.get("/api/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看审计日志")
    
    query = db.query(AuditLog).filter(AuditLog.tenant_id == current_user["tenantId"])
    total = query.count()
    
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "data": [
            {
                "id": str(log.id),
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


# ==================== 用户管理接口 ====================

@app.get("/api/users")
async def get_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看用户列表")
    
    users = db.query(User).filter(User.tenant_id == current_user["tenantId"]).all()
    
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@app.post("/api/users")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可创建用户")
    
    existing = db.query(User).filter(
        User.tenant_id == current_user["tenantId"],
        User.username == username
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = User(
        id=uuid.uuid4(),
        tenant_id=current_user["tenantId"],
        username=username,
        password=pwd_context.hash(password),
        email=email,
        role=role,
        status="active"
    )
    db.add(user)
    db.commit()
    
    create_audit_log(db, current_user, "CREATE_USER", "users", str(user.id))
    
    return {"id": str(user.id), "message": "创建成功"}


# ==================== 数据导入导出 ====================

@app.post("/api/import/sales")
async def import_sales(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="只支持 Excel 或 CSV 文件")
    
    content = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")
    
    imported = 0
    for _, row in df.iterrows():
        try:
            date = str(row.get('日期', row.get('date', datetime.now().strftime("%Y-%m-%d")))
            platform = str(row.get('平台', row.get('platform', 'Shopee')))
            country = str(row.get('国家', row.get('country', '泰国')))
            product = str(row.get('产品', row.get('product', '未知产品')))
            gmv = float(row.get('GMV', row.get('gmv', 0)))
            gsv = float(row.get('GSV', row.get('gsv', 0)))
            refund_amount = float(row.get('退款金额', row.get('refund_amount', 0)))
            ad_cost = float(row.get('广告消耗', row.get('ad_cost', 0)))
            roi = float(row.get('ROI', row.get('roi', 0)))
            orders_count = int(row.get('订单数', row.get('orders_count', 0)))
            refund_rate = (refund_amount / gmv * 100) if gmv > 0 else 0
            
            sale = SalesData(
                id=uuid.uuid4(),
                tenant_id=current_user["tenantId"],
                date=date,
                platform=platform,
                country=country,
                product=product,
                gmv=gmv,
                gsv=gsv,
                refund_amount=refund_amount,
                refund_rate=round(refund_rate, 2),
                ad_cost=ad_cost,
                roi=roi,
                orders_count=orders_count
            )
            db.add(sale)
            imported += 1
        except Exception:
            continue
    
    db.commit()
    
    create_audit_log(db, current_user, "IMPORT_SALES", "sales", details={"imported": imported})
    
    return {"imported": imported, "message": f"成功导入 {imported} 条数据"}


@app.get("/api/export/sales")
async def export_sales(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    sales = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"]).order_by(SalesData.date.desc()).all()
    
    if not sales:
        raise HTTPException(status_code=404, detail="无数据可导出")
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('销售数据')
    
    # 表头
    headers = ['日期', '平台', '国家', '产品', 'GMV', 'GSV', '退款金额', '退款率', '广告消耗', 'ROI', '订单数']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # 数据
    for row, sale in enumerate(sales, 1):
        worksheet.write(row, 0, sale.date)
        worksheet.write(row, 1, sale.platform)
        worksheet.write(row, 2, sale.country)
        worksheet.write(row, 3, sale.product)
        worksheet.write(row, 4, sale.gmv)
        worksheet.write(row, 5, sale.gsv)
        worksheet.write(row, 6, sale.refund_amount)
        worksheet.write(row, 7, sale.refund_rate)
        worksheet.write(row, 8, sale.ad_cost)
        worksheet.write(row, 9, sale.roi)
        worksheet.write(row, 10, sale.orders_count)
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=sales_data_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )


# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
