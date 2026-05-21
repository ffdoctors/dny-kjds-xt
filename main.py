"""
东南亚跨境电商数据分析系统 - 完整版
"""
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt
from passlib.context import CryptContext
import xlsxwriter
from io import BytesIO
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")
JWT_SECRET = os.getenv("JWT_SECRET", "ecommerce-secret-2024")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="free")
    status = Column(String(50), default="active")

class User(Base):
    __tablename__ = "users"
    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(50), default="user")
    status = Column(String(50), default="active")
    last_login = Column(DateTime)

class SalesData(Base):
    __tablename__ = "sales_data"
    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), nullable=False)
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token无效")
    except:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return {"userId": user.id, "username": user.username, "role": user.role, "tenantId": user.tenant_id, "tenantName": "默认租户", "plan": "enterprise"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Tenant).filter(Tenant.code == "default").first()
        if not existing:
            tenant = Tenant(id=str(uuid.uuid4()), name="默认租户", code="default", plan="enterprise")
            db.add(tenant)
            db.flush()
            
            admin = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username="admin", password=pwd_context.hash("admin123"), email="admin@example.com", role="admin")
            db.add(admin)
            
            demo = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username="demo", password=pwd_context.hash("demo123"), email="demo@example.com", role="user")
            db.add(demo)
            
            platforms = ["Shopee", "Lazada", "TikTok"]
            countries = ["泰国", "马来西亚"]
            products = ["蓝牙耳机", "智能手环", "移动电源", "数据线", "手机壳", "无线充电器", "便携音箱", "运动相机"]
            
            for i in range(29, -1, -1):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                for p in platforms:
                    for c in countries:
                        for pr in products:
                            sale = SalesData(
                                id=str(uuid.uuid4()), tenant_id=tenant.id, date=date, platform=p, country=c, product=pr,
                                gmv=5000 + (hash(p + c + pr) % 15000),
                                gsv=5000 + (hash(p + c + pr) % 15000) * 1.05,
                                refund_amount=100 + (hash(p + c + pr) % 500),
                                ad_cost=500 + (hash(p + c + pr) % 1000),
                                roi=2 + (hash(p + c + pr) % 400) / 100,
                                orders_count=50 + (hash(p + c + pr) % 200)
                            )
                            db.add(sale)
            db.commit()
            print("系统初始化完成: admin/admin123, demo/demo123")
        else:
            print("系统已就绪")
    except Exception as e:
        print(f"初始化错误: {e}")
        db.rollback()
    finally:
        db.close()
    yield

app = FastAPI(title="电商数据分析系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": "ok", "message": "东南亚跨境电商数据分析系统", "docs": "/docs"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.status == "active").first()
    if not user or not pwd_context.verify(req.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    token = jwt.encode({"userId": user.id, "username": user.username, "role": user.role, "tenantId": user.tenant_id, "tenantName": "默认租户", "plan": "enterprise"}, JWT_SECRET, algorithm="HS256")
    
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "tenantId": user.tenant_id, "tenantName": "默认租户", "plan": "enterprise"}}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/dashboard/summary")
async def get_summary(period: str = "30", platform: str = "all", country: str = "all", db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sales = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"]).all()
    total_gmv = sum(s.gmv for s in sales) if sales else 0
    total_orders = sum(s.orders_count for s in sales) if sales else 0
    total_ad_cost = sum(s.ad_cost for s in sales) if sales else 0
    avg_roi = sum(s.roi for s in sales) / len(sales) if sales else 0
    return {"totalGmv": round(total_gmv, 2), "totalGsv": round(total_gmv * 1.05, 2), "totalRefund": round(sum(s.refund_amount for s in sales) if sales else 0, 2), "totalAdCost": round(total_ad_cost, 2), "totalOrders": total_orders, "avgRoi": round(avg_roi, 2), "gmvChange": 0}

@app.get("/api/dashboard/platform-stats")
async def get_platform_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    results = db.query(SalesData.platform, func.sum(SalesData.gmv).label("gmv"), func.sum(SalesData.orders_count).label("orders")).filter(SalesData.tenant_id == current_user["tenantId"]).group_by(SalesData.platform).all()
    return [{"platform": r[0], "gmv": float(r[1] or 0), "orders": r[2] or 0} for r in results]

@app.get("/api/dashboard/daily")
async def get_daily(period: str = "30", platform: str = "all", country: str = "all", db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sales = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"]).order_by(SalesData.date.desc()).limit(50).all()
    return [{"id": s.id, "date": s.date, "platform": s.platform, "country": s.country, "product": s.product, "gmv": s.gmv, "gsv": s.gsv, "refund_amount": s.refund_amount, "refund_rate": s.refund_rate, "ad_cost": s.ad_cost, "roi": s.roi, "orders_count": s.orders_count} for s in sales]

@app.get("/api/sales")
async def get_sales(page: int = 1, limit: int = 50, platform: str = None, country: str = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"])
    if platform: query = query.filter(SalesData.platform == platform)
    if country: query = query.filter(SalesData.country == country)
    total = query.count()
    sales = query.order_by(SalesData.date.desc()).offset((page-1)*limit).limit(limit).all()
    return {"data": [{"id": s.id, "date": s.date, "platform": s.platform, "country": s.country, "product": s.product, "gmv": s.gmv, "gsv": s.gsv, "refund_amount": s.refund_amount, "ad_cost": s.ad_cost, "roi": s.roi, "orders_count": s.orders_count} for s in sales], "total": total, "page": page, "limit": limit}

class SalesCreate(BaseModel):
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

@app.post("/api/sales")
async def create_sale(data: SalesCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sale = SalesData(id=str(uuid.uuid4()), tenant_id=current_user["tenantId"], date=data.date, platform=data.platform, country=data.country, product=data.product, gmv=data.gmv, gsv=data.gsv, refund_amount=data.refund_amount, ad_cost=data.ad_cost, roi=data.roi, orders_count=data.orders_count)
    db.add(sale)
    db.commit()
    return {"id": sale.id, "message": "创建成功"}

@app.delete("/api/sales/{sale_id}")
async def delete_sale(sale_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sale = db.query(SalesData).filter(SalesData.id == sale_id, SalesData.tenant_id == current_user["tenantId"]).first()
    if sale:
        db.delete(sale)
        db.commit()
    return {"message": "删除成功"}

@app.get("/api/export/sales")
async def export_sales(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sales = db.query(SalesData).filter(SalesData.tenant_id == current_user["tenantId"]).all()
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    ws = workbook.add_worksheet('销售数据')
    headers = ['日期', '平台', '国家', '产品', 'GMV', 'GSV', '退款', '广告', 'ROI', '订单']
    for i, h in enumerate(headers): ws.write(0, i, h)
    for i, s in enumerate(sales, 1):
        ws.write(i, 0, s.date); ws.write(i, 1, s.platform); ws.write(i, 2, s.country)
        ws.write(i, 3, s.product); ws.write(i, 4, s.gmv); ws.write(i, 5, s.gsv)
        ws.write(i, 6, s.refund_amount); ws.write(i, 7, s.ad_cost); ws.write(i, 8, s.roi); ws.write(i, 9, s.orders_count)
    workbook.close()
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=sales.xlsx"})

@app.get("/api/users")
async def get_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    users = db.query(User).filter(User.tenant_id == current_user["tenantId"]).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role, "status": u.status} for u in users]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
