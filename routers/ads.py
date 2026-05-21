"""
广告数据 API
"""
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import AdRecord

router = APIRouter()


@router.get("/ads")
async def get_ads(
    country: str = Query(None),
    platform: str = Query(None),
    ad_type: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    db = next(get_db())
    query = db.query(AdRecord)

    if country:
        query = query.filter(AdRecord.country == country)
    if platform:
        query = query.filter(AdRecord.platform == platform)
    if ad_type:
        query = query.filter(AdRecord.ad_type == ad_type)
    if date_from:
        query = query.filter(AdRecord.date >= date_from)
    if date_to:
        query = query.filter(AdRecord.date <= date_to)

    total = query.count()
    data = query.order_by(desc(AdRecord.date)).offset((page - 1) * page_size).limit(page_size).all()

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
                "ad_type": r.ad_type,
                "product_name": r.product_name,
                "product_id": r.product_id,
                "ad_spend": r.ad_spend,
                "revenue": r.revenue,
                "impressions": r.impressions,
                "clicks": r.clicks,
                "ctr": r.ctr,
                "conversion": r.conversion,
                "roi": r.roi,
                "video_views": r.video_views,
                "cpm": r.cpm,
                "cpc": r.cpc
            } for r in data
        ]
    }


@router.delete("/ads/{record_id}")
async def delete_ad(record_id: int):
    db = next(get_db())
    record = db.query(AdRecord).filter(AdRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功", "success": True}


@router.get("/ads/stats/overview")
async def get_ads_overview(country: str = Query(None), date_from: str = Query(None), date_to: str = Query(None)):
    db = next(get_db())
    query = db.query(AdRecord)
    if country:
        query = query.filter(AdRecord.country == country)
    if date_from:
        query = query.filter(AdRecord.date >= date_from)
    if date_to:
        query = query.filter(AdRecord.date <= date_to)

    all_data = query.all()
    total_ad = sum(a.ad_spend or 0 for a in all_data)
    return {
        "total_records": len(all_data),
        "total_ad_spend": round(total_ad, 2),
        "total_revenue": round(sum(a.revenue or 0 for a in all_data), 2),
        "total_impressions": sum(a.impressions or 0 for a in all_data),
        "avg_roi": round(sum(a.revenue or 0 for a in all_data) / total_ad, 2) if total_ad > 0 else 0
    }
