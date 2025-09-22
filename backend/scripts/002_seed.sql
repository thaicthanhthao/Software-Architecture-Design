-- Seed users (password_hash giả sử bcrypt, bạn đổi sau)
INSERT INTO users (email, password_hash, role)
VALUES
  ('admin@example.com', '$2b$12$adminhash', 'admin'),
  ('reporter@example.com', '$2b$12$reporterhash', 'reporter');

-- Seed categories
INSERT INTO categories (slug, name)
VALUES
  ('the-thao', 'Thể thao'),
  ('cong-nghe', 'Công nghệ'),
  ('xa-hoi', 'Xã hội');

-- Seed news
INSERT INTO news (category_id, author_id, title, summary, content, published_at)
VALUES
  (2, 2, 'OpenSearch 2.14 Released',
   'Phiên bản mới của OpenSearch',
   'OpenSearch 2.14 mang lại cải tiến hiệu suất và sửa lỗi.',
   '2025-09-01T00:00:00Z');
