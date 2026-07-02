[Thiết bị IoT] 
      │ (Gửi dữ liệu thô liên tục)
      ▼
[Tổng kho đệm: Kafka / Kinesis] (Hứng tải, xếp hàng dữ liệu)
      │
      ▼
[Băng chuyền: Spark / Flink] (Lọc rác, xử lý, tính toán ngầm)
      │
      ├───► [Kho 1: Database] ────► [Backend] ──► [Giao diện App] (Người dùng xem)
      ├───► [Kho 2: Data Warehouse] ────────────► [BI Dashboard] (Sếp xem báo cáo)
      └───► [Kho 3: Data Lake] ─────────────────► [AI / Machine Learning] (Dự đoán)


