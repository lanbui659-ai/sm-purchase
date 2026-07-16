# SM Mobility Purchase Request System

## Chức năng
- Nhân viên tạo và theo dõi yêu cầu mua hàng.
- Sếp xem toàn bộ yêu cầu và duyệt, từ chối hoặc hoàn thành.
- Dữ liệu dùng PostgreSQL khi deploy trên Render.
- Có `render.yaml` để triển khai theo Blueprint.

## Cách tạo link công khai

### Bước 1 — Tạo GitHub repository
1. Đăng nhập GitHub.
2. Chọn **New repository**.
3. Đặt tên: `sm-purchase`.
4. Chọn **Private** nếu chỉ muốn lưu mã nguồn riêng.
5. Upload toàn bộ nội dung trong thư mục này lên repository.

### Bước 2 — Deploy bằng Render Blueprint
1. Đăng nhập Render bằng GitHub.
2. Chọn **New +** → **Blueprint**.
3. Chọn repository `sm-purchase`.
4. Render sẽ đọc file `render.yaml`.
5. Nhập hai biến bí mật khi được yêu cầu:
   - `MANAGER_PASSWORD`
   - `EMPLOYEE_PASSWORD`
6. Chọn **Apply**.

Sau khi deploy xong, Render cấp một link dạng:
`https://sm-purchase.onrender.com`

Tên chính xác phụ thuộc việc tên dịch vụ còn khả dụng hay không.

## Tài khoản
Tên đăng nhập mặc định:
- Sếp: `sep`
- Nhân viên: `nhanvien`

Mật khẩu được nhập trong Render khi triển khai, không lưu trong GitHub.

## Chạy thử trên máy tính
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Mở `http://127.0.0.1:5000`.

## Lưu ý trước khi dùng chính thức
- Không dùng mật khẩu `123456`.
- Tạo thêm chức năng quản trị tài khoản trước khi áp dụng cho toàn công ty.
- Nên dùng gói cơ sở dữ liệu có sao lưu nếu dữ liệu là hồ sơ chính thức.
- Không lưu báo giá bí mật trên dịch vụ công cộng nếu chưa kiểm tra chính sách bảo mật.
