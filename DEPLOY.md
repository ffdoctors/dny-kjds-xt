# Python FastAPI 版本 - Railway 部署

## 快速部署

### 1. 创建 PostgreSQL 数据库

1. 进入 Railway Dashboard
2. 点击 **New Project** → **Empty Project**
3. 点击 **Add Database** → **PostgreSQL**
4. 等待数据库创建完成
5. 复制 **Connection URL**

### 2. 部署 API 服务

1. 点击 **New Project** → **Deploy from GitHub**
2. 选择仓库
3. 设置构建命令：
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. 添加环境变量：

```
DATABASE_URL = postgresql://user:pass@host:5432/dbname
JWT_SECRET = any-secure-random-string
ALLOWED_ORIGINS = *
```

### 3. 获取 API 地址

Settings → Domains 查看你的 URL

---

## 本地运行

```bash
cd ecommerce-enterprise-py

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
uvicorn main:app --reload
```

访问 http://localhost:8000

---

## 测试账号

- admin / admin123
- demo / demo123
