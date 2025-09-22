-- scripts/001_init.sql  (hoặc file .sql mới nếu bạn đã có 001)
CREATE TABLE IF NOT EXISTS users (
  id            BIGSERIAL PRIMARY KEY,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT       NOT NULL,
  role          TEXT       NOT NULL CHECK (role IN ('admin','reporter','reader')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
  id         BIGSERIAL PRIMARY KEY,
  slug       TEXT UNIQUE NOT NULL,
  name       TEXT        NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news (
  id            BIGSERIAL PRIMARY KEY,
  category_id   BIGINT NOT NULL REFERENCES categories(id),
  author_id     BIGINT NOT NULL REFERENCES users(id),
  title         TEXT   NOT NULL,
  summary       TEXT   NOT NULL,             -- mô tả ngắn
  content       TEXT   NOT NULL,
  published_at  TIMESTAMPTZ NOT NULL,
  status        TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft','published','deleted')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Chỉ mục cho sắp xếp & lọc
CREATE INDEX IF NOT EXISTS idx_news_published_at_desc ON news (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news (category_id);
CREATE INDEX IF NOT EXISTS idx_news_author ON news (author_id);

-- (Tùy chọn) FTS fallback ở Postgres nếu OpenSearch lỗi
CREATE INDEX IF NOT EXISTS idx_news_fts ON news
USING GIN (to_tsvector('simple', title || ' ' || summary || ' ' || content));
