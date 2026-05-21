"""
Excel/CSV 解析服务
支持中文列头映射
"""
import pandas as pd
import io
from datetime import datetime
from models import SaleRecord, AdRecord, InventoryRecord

# 列名映射 - 中文列头 → 标准化字段
SALES_COLUMNS = {
    "日期": "date",
    "平台": "platform",
    "国家": "country",
    "产品名称": "product_name",
    "产品ID": "product_id",
    "类目": "category",
    "GMV": "gmv",
    "总收入": "revenue",
    "广告消耗": "ad_spend",
    "ROI": "roi",
    "曝光数": "impressions",
    "点击数": "clicks",
    "点击率": "ctr",
    "转化数": "conversion",
}

ADS_COLUMNS = {
    "日期": "date",
    "平台": "platform",
    "国家": "country",
    "广告类型": "ad_type",
    "创意作品类型": "ad_type",
    "产品名称": "product_name",
    "产品ID": "product_id",
    "成本": "ad_spend",
    "总收入": "revenue",
    "商品广告曝光数": "impressions",
    "曝光数": "impressions",
    "点击数": "clicks",
    "点击率": "ctr",
    "转化数": "conversion",
    "ROI": "roi",
    "视频播放数": "video_views",
    "千次曝光成本": "cpm",
    "单次点击成本": "cpc",
}

INVENTORY_COLUMNS = {
    "日期": "date",
    "国家": "country",
    "产品名称": "product_name",
    "产品ID": "product_id",
    "类目": "category",
    "库存数量": "stock_quantity",
    "预留数量": "reserved_quantity",
    "可用数量": "available_quantity",
    "单位成本": "unit_cost",
    "总价值": "total_value",
}


def parse_date(val):
    """解析各种日期格式"""
    if pd.isna(val):
        return datetime.today().date()
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except:
                pass
    return datetime.today().date()


def safe_float(val):
    try:
        v = float(val)
        return v if not pd.isna(v) else 0.0
    except:
        return 0.0


def safe_int(val):
    try:
        v = int(float(val))
        return v if not pd.isna(v) else 0
    except:
        return 0


def rename_columns(df, column_map):
    """将中文列名重命名为标准字段"""
    rename_dict = {}
    for col in df.columns:
        col_clean = str(col).strip()
        if col_clean in column_map:
            rename_dict[col] = column_map[col_clean]
    df = df.rename(columns=rename_dict)
    # 只保留已知列
    keep_cols = list(column_map.values())
    df = df[[c for c in df.columns if c in keep_cols]]
    return df


async def parse_sales_file(content: bytes, db, upload_id, country=None, product_line=None):
    """解析销售数据"""
    try:
        if content.startswith(b'<?xml') or content[:2] == b'PK':
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except:
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8-sig')

    df = rename_columns(df, SALES_COLUMNS)

    if 'date' not in df.columns:
        raise ValueError("未找到日期列，请检查文件格式")

    records = []
    for _, row in df.iterrows():
        try:
            record = SaleRecord(
                date=parse_date(row.get('date')),
                country=str(country or row.get('country', 'TH')).strip(),
                platform=str(row.get('platform', '')).strip() if pd.notna(row.get('platform')) else None,
                product_name=str(row.get('product_name', '')).strip() if pd.notna(row.get('product_name')) else None,
                product_id=str(row.get('product_id', '')).strip() if pd.notna(row.get('product_id')) else None,
                category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None,
                gmv=safe_float(row.get('gmv')),
                revenue=safe_float(row.get('revenue')),
                ad_spend=safe_float(row.get('ad_spend')),
                roi=safe_float(row.get('roi')),
                impressions=safe_int(row.get('impressions')),
                clicks=safe_int(row.get('clicks')),
                ctr=safe_float(row.get('ctr')),
                conversion=safe_int(row.get('conversion')),
                upload_id=upload_id
            )
            records.append(record)
        except:
            continue

    db.add_all(records)
    db.commit()
    return len(records)


async def parse_ads_file(content: bytes, db, upload_id, country=None, product_line=None):
    """解析广告数据"""
    try:
        if content.startswith(b'<?xml') or content[:2] == b'PK':
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except:
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8-sig')

    df = rename_columns(df, ADS_COLUMNS)

    if 'date' not in df.columns:
        raise ValueError("未找到日期列，请检查文件格式")

    records = []
    for _, row in df.iterrows():
        try:
            ad_spend = safe_float(row.get('ad_spend'))
            revenue = safe_float(row.get('revenue'))
            roi = revenue / ad_spend if ad_spend > 0 else 0

            record = AdRecord(
                date=parse_date(row.get('date')),
                country=str(country or row.get('country', 'TH')).strip(),
                platform=str(row.get('platform', '')).strip() if pd.notna(row.get('platform')) else None,
                ad_type=str(row.get('ad_type', '')).strip() if pd.notna(row.get('ad_type')) else None,
                product_name=str(row.get('product_name', '')).strip() if pd.notna(row.get('product_name')) else None,
                product_id=str(row.get('product_id', '')).strip() if pd.notna(row.get('product_id')) else None,
                ad_spend=ad_spend,
                revenue=revenue,
                impressions=safe_int(row.get('impressions')),
                clicks=safe_int(row.get('clicks')),
                ctr=safe_float(row.get('ctr')),
                conversion=safe_int(row.get('conversion')),
                roi=roi,
                video_views=safe_int(row.get('video_views')),
                cpm=safe_float(row.get('cpm')),
                cpc=safe_float(row.get('cpc')),
                upload_id=upload_id
            )
            records.append(record)
        except:
            continue

    db.add_all(records)
    db.commit()
    return len(records)


async def parse_inventory_file(content: bytes, db, upload_id, country=None, product_line=None):
    """解析库存数据"""
    try:
        if content.startswith(b'<?xml') or content[:2] == b'PK':
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except:
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8-sig')

    df = rename_columns(df, INVENTORY_COLUMNS)

    if 'date' not in df.columns:
        raise ValueError("未找到日期列，请检查文件格式")

    records = []
    for _, row in df.iterrows():
        try:
            record = InventoryRecord(
                date=parse_date(row.get('date')),
                country=str(country or row.get('country', 'TH')).strip(),
                product_name=str(row.get('product_name', '')).strip() if pd.notna(row.get('product_name')) else None,
                product_id=str(row.get('product_id', '')).strip() if pd.notna(row.get('product_id')) else None,
                category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None,
                stock_quantity=safe_int(row.get('stock_quantity')),
                reserved_quantity=safe_int(row.get('reserved_quantity')),
                available_quantity=safe_int(row.get('available_quantity')),
                unit_cost=safe_float(row.get('unit_cost')),
                total_value=safe_float(row.get('total_value')),
                upload_id=upload_id
            )
            records.append(record)
        except:
            continue

    db.add_all(records)
    db.commit()
    return len(records)
