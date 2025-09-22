# News Search – Kiến trúc & luồng hoạt động

## 1. Thành phần chính
- **Postgres**: CSDL lưu tin tức thô và thông tin metadata.  
- **Redis**: Cache để tăng tốc truy vấn, giảm tải Postgres/OpenSearch.  
- **OpenSearch**: Search engine, dùng để đánh chỉ mục (index) và tìm kiếm tin tức.  
- **API service**: Xử lý request từ người dùng, trả dữ liệu sau khi truy vấn DB + OpenSearch.  
- **Indexer service**: Lấy dữ liệu mới từ Postgres, build mapping/index và đồng bộ với OpenSearch.  
- **Nginx (frontend)**: Cung cấp file tĩnh (HTML, JS) và proxy request đến API.  

---

## 2. Luồng hoạt động

### 2.1. Khởi tạo hệ thống
1. `docker-compose up` → khởi động **Postgres, Redis, OpenSearch, API, Indexer, Nginx**.  
2. API và Indexer chờ đến khi Postgres, Redis, OpenSearch **healthy**.  
3. Indexer đọc file `mapping.json` để tạo index `news` trong OpenSearch (nếu chưa tồn tại).  
4. Postgres chạy script trong thư mục `scripts/` để tạo bảng và dữ liệu mẫu (nếu có).  

---

### 2.2. Quy trình thêm dữ liệu mới
1. Dữ liệu tin tức được thêm vào Postgres.  
2. Indexer lắng nghe sự kiện hoặc cron job → đọc tin mới từ Postgres.  
3. Indexer gửi dữ liệu sang OpenSearch để đánh chỉ mục.  
4. Redis có thể cache kết quả truy vấn phổ biến.  

---

### 2.3. Quy trình tìm kiếm
1. Người dùng nhập từ khóa trên giao diện web (served by Nginx).  
2. Request → API service.  
3. API kiểm tra cache Redis:  
   - Nếu có cache → trả kết quả ngay.  
   - Nếu không có → truy vấn OpenSearch.  
4. Kết quả được trả về và đồng thời lưu vào Redis.  
5. Frontend hiển thị kết quả cho người dùng.  

---

## 3. Lợi ích của kiến trúc
- **Tách biệt trách nhiệm**: API chuyên xử lý request, Indexer chuyên đánh chỉ mục.  
- **Khả năng mở rộng**: Có thể scale riêng từng service khi tải cao.  
- **Hiệu năng**: Redis tăng tốc, OpenSearch hỗ trợ full-text search nhanh chóng.  
- **Triển khai đồng bộ**: `docker-compose` đảm bảo tất cả thành phần khởi động đúng thứ tự.  

---

## 4. Sơ đồ kiến trúc (mô tả logic)
[Frontend (Nginx)]
|
v
[ API ]
|
+----+----+
| |
[Redis] [Postgres] <---> [Indexer] --> [OpenSearch]
