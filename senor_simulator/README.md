# IoT Sensor Simulator & GCP Pub/Sub Bridge

Dự án này chứa bộ mã nguồn giả lập thiết bị IoT gửi dữ liệu cảm biến đến MQTT Broker local, xác thực token động thông qua API Backend, và chuyển tiếp các gói tin hợp lệ lên Google Cloud Pub/Sub.

---

## 🛠️ Yêu cầu hệ thống
- Python 3.10 trở lên
- Docker Desktop (để chạy MQTT Broker Mosquitto cục bộ)

---

## ⚙️ Cài đặt & Cấu hình

### Bước 1: Cài đặt thư viện Python
Mở terminal tại thư mục `senor_simulator/` hoặc thư mục gốc và chạy:
```bash
pip install -r requirements.txt
```

### Bước 2: Cài đặt biến môi trường
Tạo tệp `.env` dựa trên mẫu `.env.example` và thiết lập các thông số sau:
```ini
# MQTT Broker (Chạy trên Docker cục bộ)
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC=iot/data/phupham

# Cấu hình thiết bị giả lập (phải khớp thông tin đã đăng ký trong Backend DB)
DEVICE_ID=4324234
DEVICE_TOKEN=dev_tok_947953e60e985ebf4c9ebfad32ee3f9a
SEND_INTERVAL_SECONDS=5

# Google Cloud Platform (GCP)
GCP_PROJECT_ID=automatic-vent-443012-g2
GCP_PUBSUB_TOPIC=digital_twin
GCP_CREDENTIALS_PATH=automatic-vent-443012-g2-288bd683bf67.json

# Địa chỉ API Backend dùng để xác thực Token của thiết bị
BACKEND_VERIFY_URL=http://localhost:8000/api/v1/devices/verify
```

---

## 🚀 Hướng dẫn khởi chạy (Theo đúng luồng hoạt động)

### Bước 1: Khởi động MQTT Broker (Mosquitto)
Đảm bảo đã bật **Docker Desktop**. Tại thư mục `senor_simulator/`, khởi chạy container Mosquitto:
```bash
docker-compose up -d
```
*Lệnh này sẽ chạy MQTT Broker trên cổng mặc định `1883` cục bộ và cho phép kết nối.*

### Bước 2: Khởi động API Backend (Để thực hiện xác thực)
Ở một terminal riêng biệt, di chuyển đến thư mục dự án gốc `Backend_twin` và bật Backend lên:
```bash
uvicorn src.main:app --reload
```
*Backend sẽ cung cấp API xác thực token tại `http://localhost:8000/api/v1/devices/verify`.*

### Bước 3: Khởi động Cầu nối (MQTT to GCP Pub/Sub Bridge)
Mở một terminal mới và chạy file cầu nối:
```bash
python mqtt_pubsub_bridge.py
```
*Cầu nối sẽ kết nối vào Broker local, chờ nhận tin nhắn từ thiết bị, gọi API xác thực, rồi đẩy lên Google Cloud Pub/Sub.*

### Bước 4: Khởi động Thiết bị giả lập (Device Simulator)
Mở một terminal mới nữa và chạy trình giả lập cảm biến:
```bash
python device_simulator.py
```
*Thiết bị sẽ bắt đầu gửi dữ liệu cảm biến định kỳ lên Broker.*

---

## 🔍 Kiểm tra kết quả
- Xem log ở terminal chạy **Bridge** để kiểm tra trạng thái xác thực (`API verification PASSED`) và trạng thái gửi lên GCP (`Published successfully`).
- Muốn lắng nghe xem tin nhắn đã thực sự về Subscription trên GCP chưa (yêu cầu tài khoản Service Account có quyền `Pub/Sub Subscriber`), chạy tệp tin:
  ```bash
  python gcp_subscriber.py
  ```
