# Tài liệu API Dịch vụ Tin tức

## Tổng quan
API Dịch vụ Tin tức cung cấp các chức năng để tạo, đọc, cập nhật, xóa và tìm kiếm bài viết tin tức. API được xây dựng bằng **FastAPI** và sử dụng **OpenSearch** làm công cụ tìm kiếm.

## Các Endpoint API

1. GET /health
Kiểm tra trạng thái của API và OpenSearch.

Phản hồi:
```json
{
  "status": "ok",
  "cluster": "tên_cluster"
}
2. POST /news
Tạo mới một bài tin tức.

Yêu cầu Body:

json
Sao chép mã
{
  "title": "Tiêu đề của bài viết",
  "summary": "Tóm tắt của bài viết",
  "content": "Nội dung chi tiết của bài viết",
  "category": "Danh mục của bài viết",
  "published_at": "2025-09-01T10:00:00"
}
Phản hồi:

json
Sao chép mã
{
  "id": "id_tin_tuc",
  "result": "created"
}
3. PUT /news/{id}
Cập nhật một bài tin tức đã tồn tại.

Yêu cầu Body:

json
Sao chép mã
{
  "title": "Tiêu đề đã cập nhật",
  "summary": "Tóm tắt đã cập nhật",
  "content": "Nội dung đã cập nhật",
  "category": "Danh mục đã cập nhật",
  "published_at": "2025-09-01T12:00:00"
}
Phản hồi:

json
Sao chép mã
{
  "id": "id_bài_tin",
  "result": "updated"
}
4. GET /news/{id}
Lấy thông tin chi tiết của một bài tin tức theo ID.

Phản hồi:

json
Sao chép mã
{
  "id": "id_bài_tin",
  "title": "Tiêu đề bài viết",
  "summary": "Tóm tắt bài viết",
  "content": "Nội dung bài viết",
  "category": "Danh mục bài viết",
  "published_at": "2025-09-01T10:00:00"
}
5. DELETE /news/{id}
Xóa một bài tin tức theo ID.

Phản hồi:

json
Sao chép mã
{
  "deleted": "id_bài_tin"
}
6. GET /news
Lấy danh sách các bài tin tức với khả năng lọc theo danh mục (tuỳ chọn).
Tham số truy vấn:
category: Lọc theo danh mục (tuỳ chọn).
size: Số lượng bài tin mỗi lần trả về (mặc định: 50, tối đa: 200).
from: Vị trí bắt đầu phân trang (mặc định: 0).
Phản hồi:

json
Sao chép mã
[
  {
    "id": "id_bài_tin",
    "source": {
      "title": "Tiêu đề bài viết",
      "summary": "Tóm tắt bài viết",
      "content": "Nội dung bài viết",
      "category": "Danh mục bài viết",
      "published_at": "2025-09-01T10:00:00"
    }
  }
]
7. GET /news/counters
Lấy số lượng bài tin theo từng danh mục và tổng số bài.

Phản hồi:

json
Sao chép mã
{
  "total": 100,
  "by_category": {
    "Thế giới": 30,
    "Việt Nam": 20,
    "Công nghệ": 50
  }
}
8. GET /search
Tìm kiếm bài tin theo từ khoá.

Tham số truy vấn:
q: Từ khoá tìm kiếm (tuỳ chọn).
category: Lọc theo danh mục (tuỳ chọn).
size: Số lượng bài tin mỗi lần trả về (mặc định: 10).
from: Vị trí bắt đầu phân trang (mặc định: 0).
Phản hồi:

json
Sao chép mã
{
  "total": 100,
  "hits": [
    {
      "id": "id_bài_tin",
      "score": 1.2,
      "source": {
        "title": "Tiêu đề bài viết",
        "summary": "Tóm tắt bài viết",
        "content": "Nội dung bài viết",
        "category": "Danh mục bài viết",
        "published_at": "2025-09-01T10:00:00"
      }
    }
  ]
}
Xác thực
API sử dụng xác thực Bearer Token. Để xác thực, bạn cần bao gồm token hợp lệ trong header Authorization cho mỗi yêu cầu.

Ví dụ:

bash
Sao chép mã
Authorization: Bearer <your_token>
Các công nghệ sử dụng
FastAPI: Framework web để xây dựng API.
OpenSearch: Công cụ tìm kiếm để lập chỉ mục và truy vấn các bài tin.
Pydantic: Kiểm tra dữ liệu cho các request và response.
Docker: Công cụ container hóa cho ứng dụng.

Cách chạy
Clone kho mã nguồn:

bash
Sao chép mã
git clone <repository_url>
cd <repository_directory>
Xây dựng và chạy container (Docker cần được cài đặt):

bash
Sao chép mã
docker-compose up --build
API sẽ có sẵn tại http://localhost:8080.