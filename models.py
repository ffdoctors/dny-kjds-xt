"""
数据库模型 - 销售/广告/库存数据统一管理
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class UploadRecord(Base):
    """上传记录表"""
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    data_type = Column(String(20), nullable=False)   # sales/ads/inventory
    country = Column(String(20), nullable=True)     # TH/MY
    product_line = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    row_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=func.now())
    remark = Column(Text, nullable=True)


class SaleRecord(Base):
    """销售记录表"""
    __tablename__ = "sale_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    country = Column(String(20), nullable=False)
    platform = Column(String(50), nullable=True)
    product_name = Column(String(200), nullable=True)
    product_id = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    gmv = Column(Float, default=0)
    revenue = Column(Float, default=0)
    ad_spend = Column(Float, default=0)
    roi = Column(Float, default=0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0)
    conversion = Column(Integer, default=0)
    upload_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class AdRecord(Base):
    """广告记录表"""
    __tablename__ = "ad_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    country = Column(String(20), nullable=False)
    platform = Column(String(50), nullable=True)
    ad_type = Column(String(50), nullable=True)      # 短视频/商品卡
    product_name = Column(String(200), nullable=True)
    product_id = Column(String(50), nullable=True)
    ad_spend = Column(Float, default=0)
    revenue = Column(Float, default=0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0)
    conversion = Column(Integer, default=0)
    roi = Column(Float, default=0)
    video_views = Column(Integer, default=0)
    cpm = Column(Float, default=0)
    cpc = Column(Float, default=0)
    upload_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class InventoryRecord(Base):
    """库存记录表"""
    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    country = Column(String(20), nullable=False)
    product_name = Column(String(200), nullable=True)
    product_id = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    unit_cost = Column(Float, default=0)
    total_value = Column(Float, default=0)
    upload_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class FilterConfig(Base):
    """筛选配置表"""
    __tablename__ = "filter_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    config_type = Column(String(20), nullable=False)
    values = Column(Text, nullable=True)
    is_default = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)
    data_type = Column(String(20), nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
