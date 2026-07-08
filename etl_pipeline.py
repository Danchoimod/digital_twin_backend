import json
import logging
import argparse
from datetime import datetime, timezone
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Pipeline")

class ParseAndTransformFn(beam.DoFn):
    """
    DoFn nhận gói tin từ Pub/Sub, kiểm tra tính hợp lệ.
    Đẩy dữ liệu chuẩn qua luồng chính, dữ liệu lỗi qua luồng phụ (Dead Letter Queue).
    """
    # Tag cho dữ liệu lỗi
    TAG_DEAD_LETTER = 'dead_letter'

    def process(self, message_bytes):
        raw_message = ""
        try:
            raw_message = message_bytes.decode('utf-8')
            payload = json.loads(raw_message)
        except Exception as e:
            # Lỗi 1: Không parse được JSON thô
            error_msg = f"Failed to parse JSON: {str(e)}"
            logger.error(error_msg)
            yield beam.pvalue.TaggedOutput(self.TAG_DEAD_LETTER, {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "raw_payload": raw_message,
                "error_reason": error_msg
            })
            return

        # 2. Validate các trường bắt buộc
        required_fields = ["observation_id", "timestamp", "station_id", "sensor_type", "metrics"]
        for field in required_fields:
            if field not in payload:
                error_msg = f"Missing required field: '{field}'"
                logger.warning(error_msg)
                yield beam.pvalue.TaggedOutput(self.TAG_DEAD_LETTER, {
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "raw_payload": raw_message,
                    "error_reason": error_msg
                })
                return

        # 3. Chuẩn hóa dữ liệu thành công
        try:
            bq_row = {
                "observation_id": payload["observation_id"],
                "timestamp": payload["timestamp"],
                "station_id": payload["station_id"],
                "sensor_type": payload["sensor_type"],
                "metrics": json.dumps(payload["metrics"]),
                "raw_payload": json.dumps(payload.get("raw_payload", {}))
            }
            yield bq_row
        except Exception as e:
            error_msg = f"Transformation error: {str(e)}"
            logger.error(error_msg)
            yield beam.pvalue.TaggedOutput(self.TAG_DEAD_LETTER, {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "raw_payload": raw_message,
                "error_reason": error_msg
            })

def run(argv=None):
    """Điểm khởi chạy Dataflow Pipeline"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_subscription',
        required=True,
        help='Tên subscription Pub/Sub đầu vào. Định dạng: projects/<PROJECT_ID>/subscriptions/<SUB_NAME>'
    )
    parser.add_argument(
        '--output_table',
        required=True,
        help='Tên bảng BigQuery đích. Định dạng: <PROJECT_ID>:<DATASET>.<TABLE>'
    )
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Định dạng bảng Dead Letter tự động dựa trên bảng đích chính
    # VD: dataset.device_telemetry -> dataset.device_telemetry_dead_letter
    output_table_base = known_args.output_table
    dead_letter_table = f"{output_table_base}_dead_letter"

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    pipeline_options.view_as(beam.options.pipeline_options.StandardOptions).streaming = True

    logger.info("Starting Dataflow Streaming Pipeline with DLQ...")
    
    with beam.Pipeline(options=pipeline_options) as p:
        # 1. Đọc dữ liệu từ Pub/Sub
        pubsub_data = p | "Read from PubSub" >> beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
        
        # 2. Xử lý & Phân luồng dữ liệu (Sử dụng với Side Outputs)
        results = (
            pubsub_data 
            | "Transform Telemetry" >> beam.ParDo(ParseAndTransformFn()).with_outputs(
                ParseAndTransformFn.TAG_DEAD_LETTER,
                main='valid_data'
            )
        )
        
        # Luồng dữ liệu HỢP LỆ -> Ghi vào bảng chính
        (
            results.valid_data
            | "Write to BigQuery" >> beam.io.WriteToBigQuery(
                table=known_args.output_table,
                schema="observation_id:STRING,timestamp:TIMESTAMP,station_id:STRING,sensor_type:STRING,metrics:JSON,raw_payload:JSON",
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )
        
        # Luồng dữ liệu LỖI (DLQ) -> Ghi vào bảng Dead Letter
        (
            results[ParseAndTransformFn.TAG_DEAD_LETTER]
            | "Write to DLQ Table" >> beam.io.WriteToBigQuery(
                table=dead_letter_table,
                schema="timestamp:TIMESTAMP,raw_payload:STRING,error_reason:STRING",
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )

if __name__ == '__main__':
    run()
