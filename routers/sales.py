"""
销售数据 API
"""
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import SaleRecord

router = APIRouter()


@router.get("/sales")
async def get_sales(
    country: str = Query(None),
    platform: str = Query(None),
    category: str = Query(None),
    product_id: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    db = next(get_db())
    query = db.query(SaleRecord)

    if country:
        query = query.filter(SaleRecord.country == country)
    if platform:
        query = query.filter(SaleRecord.platform == platform)
    if category:
        query = query.filter(SaleRecord.category == category)
    if product_id:
        query = query.filter(SaleRecord.product_id == product_id)
    if date_from:
        query = query.filter(SaleRecord.date >= date_from)
    if date_to:
        query = query.filter(SaleRecord.date <= date_to)

    total = query.count()
    data = query.order_by(desc(SaleRecord.date)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [
            {
                "id": r.id,
                "date": str(r.date),
                "country": r.country,
                "platform": r.platform,
                "product_name": r.product_name,
                "product_id": r.product_id,
                "category": r.category,
                "gmv": r.gmv,
                "revenue": r.revenue,
                "ad_spend": r.ad_spend,
                "roi": r.roi,
                "impressions": r.impressions,
                "clicks": r.clicks,
                "ctr": r.ctr,
                "conversion": r.conversion
            } for r in data
        ]
    }


@router.delete("/sales/{record_id}")
async def delete_sale(record_id: int):
    db = next(get_db())
    record = db.query(SaleRecord).filter(SaleRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功", "success": True}


@router.get("/sales/stats/overview")
async def get_sales_overview(country: str = Query(None), date_from: str = Query(None), date_to: str = Query(None)):
    db = next(get_db())
    query = db.query(SaleRecord)
    if country:
        query = query.filter(SaleRecord.country == country)
    if date_from:
        query = query.filter(SaleRecord.date >= date_from)
    if date_to:
        query = query.filter(SaleRecord.date <= date_to)

    all_data = query.all()
    total_ad = sum(s.ad_spend or 0 for s in all_data)
    return {
        "total_records": len(all_data),
        "total_gmv": round(sum(s.gmv or 0 for s in all_data), 2),
        "total_revenue": round(sum(s.revenue or 0 for s in all_data), 2),
        "total_ad_spend": round(total_ad, 2),
        "avg_roi": round(sum(s.revenue or 0 for s in all_data) / total_ad, 2) if total_ad > 0 else 0
    }
