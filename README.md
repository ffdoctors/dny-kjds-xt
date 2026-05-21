# 🛒 东南亚跨境电商数据分析系统 - Python FastAPI 企业版

基于 Python FastAPI 构建的企业级电商数据分析平台。

## ✨ 功能特性

- 🔐 JWT 认证 + RBAC 权限控制
- 📊 数据仪表盘（销售趋势、平台统计、产品排行）
- 💰 销售数据管理（CRUD）
- 📢 广告花费追踪
- 📦 库存管理
- 📥 Excel/CSV 数据导入
- 📤 Excel 数据导出
- 📋 审计日志
- 👥 多用户支持
- 🏢 多租户隔离

## 🚀 快速开始

### 本地运行

```bash
# 1. 进入目录
cd ecommerce-enterprise-py

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行服务
uvicorn main:app --reload

# 5. 访问
# API: http://localhost:8000
# 文档: http://localhost:8000/docs
```

### Railway 部署

详见 [DEPLOY.md](DEPLOY.md)

## 🔑 测试账号

| 用户名 | 密码 | 角色 |
|-------|------|------|
| admin | admin123 | 管理员 |
| demo | demo123 | 普通用户 |

## 📁 项目结构

```
ecommerce-enterprise-py/
├── main.py              # FastAPI 应用主文件
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 配置
├── DEPLOY.md           # 部署指南
└── README.md           # 本文件
```

## 🛠 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | PostgreSQL / SQLite |
| ORM | SQLAlchemy |
| 认证 | JWT + bcrypt |
| 数据处理 | Pandas |
| Excel | xlsxwriter |

## 📡 API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 数据导入格式

Excel/CSV 文件应包含以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| 日期 | 销售日期 | 2026-05-20 |
| 平台 | 电商平台 | Shopee |
| 国家 | 销售国家 | 泰国 |
| 产品 | 产品名称 | 蓝牙耳机 |
| GMV | 商品交易额 | 10000 |
| 广告消耗 | 广告花费 | 500 |
| ROI | 投资回报率 | 3.5 |

## 📝 许可证

MIT License
