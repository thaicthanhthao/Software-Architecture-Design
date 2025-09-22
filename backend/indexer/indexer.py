# backend/indexer/indexer.py
import os
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from opensearchpy import OpenSearch, helpers
from urllib.parse import urlparse
from pathlib import Path

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "dbname=news user=postgres password=postgres host=postgres port=5432")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "admin")
INDEX_NAME = os.getenv("INDEX_NAME", "news")
BATCH_SIZE = int(os.getenv("INDEXER_BATCH_SIZE", "1000"))
SLEEP_SEC = int(os.getenv("INDEXER_INTERVAL_SEC", "30"))
CHECKPOINT_FILE = os.getenv("INDEXER_CHECKPOINT_FILE", "/tmp/indexer_checkpoint.txt")

def make_os_client():
    u = urlparse(OPENSEARCH_URL)
    host = u.hostname or "opensearch"
    port = u.port or 9200
    use_ssl = (u.scheme == "https")
    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
        use_ssl=use_ssl,
        verify_certs=False,  # dev
    )

def ensure_index(client: OpenSearch):
    if not client.indices.exists(INDEX_NAME):
        # tạo index đơn giản nếu chưa có (nếu bạn đã có mapping.json thì có thể bỏ phần này)
        body = {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "author": {"type": "keyword"},
                    "published_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"}
                }
            }
        }
        client.indices.create(index=INDEX_NAME, body=body, ignore=400)

def get_checkpoint() -> datetime | None:
    p = Path(CHECKPOINT_FILE)
    if not p.exists():
        return None
    s = p.read_text().strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def save_checkpoint(dt: datetime):
    Path(CHECKPOINT_FILE).write_text(dt.isoformat())

def index_batch(os_client, rows):
    def gen():
        for r in rows:
            # hàng: (id, title, content, author, published_at) hoặc dict nếu dùng RealDictCursor
            if isinstance(r, dict):
                doc_id = str(r["id"])
                pub = r["published_at"]
                title = r["title"]
                content = r["content"]
                author = r["author"]
            else:
                doc_id, title, content, author, pub = r
                doc_id = str(doc_id)
            pub_iso = pub.isoformat() if hasattr(pub, "isoformat") else str(pub)
            yield {
                "_op_type": "index",
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": {
                    "title": title,
                    "content": content,
                    "author": author,
                    "published_at": pub_iso,
                },
            }
    if rows:
        helpers.bulk(os_client, gen())

def run_once(os_client):
    # kết nối DB mỗi lần chạy để tránh idle timeout
    conn = psycopg2.connect(POSTGRES_DSN, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    last = get_checkpoint()
    params = []
    where = ""
    if last:
        where = "WHERE published_at > %s"
        params.append(last)

    # phân trang
    offset = 0
    max_pub = last
    while True:
        q = f"""
            SELECT id, title, content, author, published_at
            FROM articles
            {where}
            ORDER BY published_at ASC
            LIMIT %s OFFSET %s
        """
        cur.execute(q, params + [BATCH_SIZE, offset])
        rows = cur.fetchall()
        if not rows:
            break

        index_batch(os_client, rows)

        # cập nhật checkpoint tạm trong lần chạy
        latest_in_batch = max(r["published_at"] for r in rows)
        if (max_pub is None) or (latest_in_batch > max_pub):
            max_pub = latest_in_batch

        offset += BATCH_SIZE

    cur.close()
    conn.close()

    if max_pub and (last is None or max_pub > last):
        save_checkpoint(max_pub)

def main():
    os_client = make_os_client()
    ensure_index(os_client)
    print(f"Indexer started. Index: {INDEX_NAME}. Batch={BATCH_SIZE}, interval={SLEEP_SEC}s")

    while True:
        try:
            run_once(os_client)
            time.sleep(SLEEP_SEC)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
