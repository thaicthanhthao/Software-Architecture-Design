import psycopg2
from opensearchpy import OpenSearch
from config import Config

# =====================
# Kết nối Postgres
# =====================
def seed_postgres():
    conn = psycopg2.connect(Config.POSTGRES_DSN)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        );
    """)

    sample_news = [
        ("OpenSearch 2.14 Released", "OpenSearch has released version 2.14 with new features."),
        ("Postgres Tips", "Learn how to optimize queries in PostgreSQL."),
        ("Redis Caching", "Redis is a fast in-memory cache widely used in microservices."),
    ]

    for title, content in sample_news:
        cur.execute("INSERT INTO news (title, content) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (title, content))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Seed dữ liệu Postgres xong!")


# =====================
# Kết nối OpenSearch
# =====================
def seed_opensearch():
    client = OpenSearch(
        hosts=[Config.OPENSEARCH_URL],
        http_auth=(Config.OPENSEARCH_USER, Config.OPENSEARCH_PASS),
        use_ssl=False,
        verify_certs=False
    )

    # Tạo index nếu chưa có
    if not client.indices.exists(index=Config.INDEX_NAME):
        client.indices.create(index=Config.INDEX_NAME, body={
            "settings": {"number_of_shards": 1},
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"}
                }
            }
        })

    # Insert dữ liệu mẫu
    sample_news = [
        {"title": "OpenSearch 2.14 Released", "content": "OpenSearch has released version 2.14 with new features."},
        {"title": "Postgres Tips", "content": "Learn how to optimize queries in PostgreSQL."},
        {"title": "Redis Caching", "content": "Redis is a fast in-memory cache widely used in microservices."},
    ]

    for doc in sample_news:
        client.index(index=Config.INDEX_NAME, body=doc)

    print("✅ Seed dữ liệu OpenSearch xong!")


if __name__ == "__main__":
    print("🚀 Bắt đầu seed dữ liệu...")
    seed_postgres()
    seed_opensearch()
    print("🎉 Hoàn tất seed dữ liệu!")
