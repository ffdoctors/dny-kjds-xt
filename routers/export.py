"""
数据导出 API
"""
import io
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import SaleRecord, AdRecord, InventoryRecord
import pandas as pd

router = APIRouter()


@router.get("/export/sales")
async def export_sales(
    country: str = Query(None),
    platform: str = Query(None),
    category: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    db = next(get_db())
    query = db.query(SaleRecord)

    if country:
        query = query.filter(SaleRecord.country == country)
    if platform:
        query = query.filter(SaleRecord.platform == platform)
    if category:
        query = query.filter(SaleRecord.category == category)
    if date_from:
        query = query.filter(SaleRecord.date >= date_from)
    if date_to:
        query = query.filter(SaleRecord.date <= date_to)

    data = query.order_by(desc(SaleRecord.date)).all()

    records = [{
        "日期": r.date, "国家": r.country, "平台": r.platform,
        "产品名称": r.product_name, "产品ID": r.product_id, "类目": r.category,
        "GMV": r.gmv, "总收入": r.revenue, "广告消耗": r.ad_spend,
        "ROI": r.roi, "曝光数": r.impressions, "点击数": r.clicks,
        "点击率": r.ctr, "转化数": r.conversion
    } for r in data]

    df = pd.DataFrame(records)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sales_export.xlsx"}
    )


@router.get("/export/ads")
async def export_ads(
    country: str = Query(None),
    ad_type: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    db = next(get_db())
    query = db.query(AdRecord)

    if country:
        query = query.filter(AdRecord.country == country)
    if ad_type:
        query = query.filter(AdRecord.ad_type == ad_type)
    if date_from:
        query = query.filter(AdRecord.date >= date_from)
    if date_to:
        query = query.filter(AdRecord.date <= date_to)

    data = query.order_by(desc(AdRecord.date)).all()

    records = [{
        "日期": r.date, "国家": r.country, "平台": r.platform, "广告类型": r.ad_type,
        "产品名称": r.product_name, "产品ID": r.product_id,
        "广告消耗": r.ad_spend, "总收入": r.revenue,
        "曝光数": r.impressions, "点击数": r.clicks, "点击率": r.ctr,
        "转化数": r.conversion, "ROI": r.roi, "视频播放数": r.video_views
    } for r in data]

    df = pd.DataFrame(records)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ads_export.xlsx"}
    )
