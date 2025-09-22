# backend/api/config.py
import os

class Config:
    # Database (Postgres)
    POSTGRES_DSN = os.getenv(
        "POSTGRES_DSN",
        "dbname=news user=postgres password=postgres host=localhost port=5432"
    )

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenSearch
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
    OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "changeme")
    INDEX_NAME = os.getenv("INDEX_NAME", "news")

    # Khởi tạo DB (chỉ chạy 1 lần để seed dữ liệu)
    INIT_DB = os.getenv("INIT_DB", "0") == "1"
