"""
数据上传 API
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import get_db
from models import UploadRecord, SaleRecord, AdRecord, InventoryRecord
from services.parser_service import parse_sales_file, parse_ads_file, parse_inventory_file
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    data_type: str = Form(...),
    country: str = Form(None),
    product_line: str = Form(None),
    remark: str = Form(None)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持 {ext}，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件超过 {MAX_FILE_SIZE_MB}MB")

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    db = next(get_db())

    try:
        record = UploadRecord(
            filename=file.filename,
            data_type=data_type,
            country=country,
            product_line=product_line,
            file_path=unique_name,
            file_size=len(content),
            row_count=0,
            remark=remark
        )
        db.add(record)
        db.flush()

        if data_type == "sales":
            row_count = await parse_sales_file(content, db, record.id, country, product_line)
        elif data_type == "ads":
            row_count = await parse_ads_file(content, db, record.id, country, product_line)
        elif data_type == "inventory":
            row_count = await parse_inventory_file(content, db, record.id, country, product_line)
        else:
            raise HTTPException(status_code=400, detail="data_type 必须是 sales/ads/inventory")

        record.row_count = row_count
        db.commit()

        return {"message": f"上传成功，解析 {row_count} 条数据", "success": True, "upload_id": record.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads")
async def get_uploads(data_type: str = None):
    db = next(get_db())
    query = db.query(UploadRecord)
    if data_type:
        query = query.filter(UploadRecord.data_type == data_type)
    records = query.order_by(UploadRecord.uploaded_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "data_type": r.data_type,
            "country": r.country,
            "product_line": r.product_line,
            "row_count": r.row_count,
            "uploaded_at": str(r.uploaded_at),
            "remark": r.remark
        } for r in records
    ]


@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: int):
    db = next(get_db())
    upload = db.query(UploadRecord).filter(UploadRecord.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")

    if upload.data_type == "sales":
        db.query(SaleRecord).filter(SaleRecord.upload_id == upload.id).delete()
    elif upload.data_type == "ads":
        db.query(AdRecord).filter(AdRecord.upload_id == upload.id).delete()
    elif upload.data_type == "inventory":
        db.query(InventoryRecord).filter(InventoryRecord.upload_id == upload.id).delete()

    db.delete(upload)
    db.commit()
    return {"message": "删除成功", "success": True}
