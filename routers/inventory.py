"""
库存数据 API
"""
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import InventoryRecord

router = APIRouter()


@router.get("/inventory")
async def get_inventory(
    country: str = Query(None),
    category: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    db = next(get_db())
    query = db.query(InventoryRecord)

    if country:
        query = query.filter(InventoryRecord.country == country)
    if category:
        query = query.filter(InventoryRecord.category == category)
    if date_from:
        query = query.filter(InventoryRecord.date >= date_from)
    if date_to:
        query = query.filter(InventoryRecord.date <= date_to)

    total = query.count()
    data = query.order_by(desc(InventoryRecord.date)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [
            {
                "id": r.id,
                "date": str(r.date),
                "country": r.country,
                "product_name": r.product_name,
                "product_id": r.product_id,
                "category": r.category,
                "stock_quantity": r.stock_quantity,
                "reserved_quantity": r.reserved_quantity,
                "available_quantity": r.available_quantity,
                "unit_cost": r.unit_cost,
                "total_value": r.total_value
            } for r in data
        ]
    }


@router.delete("/inventory/{record_id}")
async def delete_inventory(record_id: int):
    db = next(get_db())
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功", "success": True}


@router.get("/inventory/stats/overview")
async def get_inventory_overview(country: str = Query(None)):
    db = next(get_db())
    query = db.query(InventoryRecord)
    if country:
        query = query.filter(InventoryRecord.country == country)

    all_data = query.all()
    return {
        "total_records": len(all_data),
        "total_value": round(sum(i.total_value or 0 for i in all_data), 2),
        "total_stock": sum(i.stock_quantity or 0 for i in all_data),
        "total_available": sum(i.available_quantity or 0 for i in all_data)
    }
