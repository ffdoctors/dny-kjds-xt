"""
仪表盘统计 API
"""
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import SaleRecord

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    country: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    db = next(get_db())

    query = db.query(SaleRecord)
    if country:
        query = query.filter(SaleRecord.country == country)
    if date_from:
        query = query.filter(SaleRecord.date >= date_from)
    if date_to:
        query = query.filter(SaleRecord.date <= date_to)

    all_data = query.all()

    total_gmv = sum(s.gmv or 0 for s in all_data)
    total_revenue = sum(s.revenue or 0 for s in all_data)
    total_ad_spend = sum(s.ad_spend or 0 for s in all_data)
    total_impressions = sum(s.impressions or 0 for s in all_data)
    total_clicks = sum(s.clicks or 0 for s in all_data)
    total_conversion = sum(s.conversion or 0 for s in all_data)
    avg_roi = total_revenue / total_ad_spend if total_ad_spend > 0 else 0
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

    summary = {
        "total_gmv": round(total_gmv, 2),
        "total_revenue": round(total_revenue, 2),
        "total_ad_spend": round(total_ad_spend, 2),
        "avg_roi": round(avg_roi, 2),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversion": total_conversion,
        "avg_ctr": round(avg_ctr, 2)
    }

    # 趋势数据
    trends_query = query.with_entities(
        SaleRecord.date,
        func.sum(SaleRecord.gmv).label('gmv'),
        func.sum(SaleRecord.revenue).label('revenue'),
        func.sum(SaleRecord.ad_spend).label('ad_spend')
    ).group_by(SaleRecord.date).order_by(SaleRecord.date).limit(30).all()

    trends = [
        {
            "date": str(t.date),
            "gmv": round(float(t.gmv or 0), 2),
            "revenue": round(float(t.revenue or 0), 2),
            "ad_spend": round(float(t.ad_spend or 0), 2)
        } for t in trends_query
    ]

    # Top 产品
    top_query = query.with_entities(
        SaleRecord.product_name,
        SaleRecord.product_id,
        SaleRecord.category,
        func.sum(SaleRecord.gmv).label('gmv'),
        func.sum(SaleRecord.revenue).label('revenue'),
        func.sum(SaleRecord.roi).label('roi')
    ).group_by(
        SaleRecord.product_name, SaleRecord.product_id, SaleRecord.category
    ).order_by(func.sum(SaleRecord.gmv).desc()).limit(10).all()

    top_products = [
        {
            "product_name": p.product_name or "未知",
            "product_id": p.product_id or "",
            "category": p.category or "",
            "gmv": round(float(p.gmv or 0), 2),
            "revenue": round(float(p.revenue or 0), 2),
            "roi": round(float(p.roi or 0), 2)
        } for p in top_query
    ]

    # 国家分布
    country_q = query.with_entities(
        SaleRecord.country,
        func.sum(SaleRecord.gmv).label('gmv'),
        func.sum(SaleRecord.revenue).label('revenue')
    ).group_by(SaleRecord.country).all()

    country_breakdown = {
        c.country: {"gmv": round(float(c.gmv or 0), 2), "revenue": round(float(c.revenue or 0), 2)}
        for c in country_q
    }

    return {"summary": summary, "trends": trends, "top_products": top_products, "country_breakdown": country_breakdown}
