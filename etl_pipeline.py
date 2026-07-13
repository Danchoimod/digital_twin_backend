import os
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

        # 3. Chuẩn hóa dữ liệu & Kiểm định chất lượng (Data Quality Rules Engine)
        try:
            metrics = payload.get("metrics", {})
            quality_flag = "VALID"

            # Rule 1: pH value must be between 0 and 14
            ph_val = metrics.get("ph") if "ph" in metrics else metrics.get("pH")
            if ph_val is not None:
                try:
                    ph_float = float(ph_val)
                    if not (0.0 <= ph_float <= 14.0):
                        quality_flag = "INVALID"
                except ValueError:
                    quality_flag = "INVALID"

            # Rule 2: Water temperature cannot be negative or abnormally high (>60°C)
            temp_val = metrics.get("temperature_c") if "temperature_c" in metrics else metrics.get("temperature")
            if temp_val is not None:
                try:
                    temp_float = float(temp_val)
                    if temp_float < 0.0:
                        quality_flag = "INVALID"
                    elif temp_float > 60.0:
                        quality_flag = "SUSPECT"
                except ValueError:
                    quality_flag = "INVALID"

            # Rule 3: Turbidity cannot be negative
            turb_val = metrics.get("turbidity_ntu") if "turbidity_ntu" in metrics else metrics.get("turbidity")
            if turb_val is not None:
                try:
                    turb_float = float(turb_val)
                    if turb_float < 0.0:
                        quality_flag = "INVALID"
                except ValueError:
                    quality_flag = "INVALID"

            # Rule 4: Water level cannot be negative
            level_val = metrics.get("water_level_m") if "water_level_m" in metrics else metrics.get("water_level")
            if level_val is not None:
                try:
                    lvl_float = float(level_val)
                    if lvl_float < 0.0:
                        quality_flag = "INVALID"
                except ValueError:
                    quality_flag = "INVALID"

            bq_row = {
                "observation_id": payload["observation_id"],
                "timestamp": payload["timestamp"],
                "station_id": payload["station_id"],
                "sensor_type": payload["sensor_type"],
                "metrics": json.dumps(payload["metrics"]),
                "raw_payload": json.dumps(payload.get("raw_payload", {})),
                "quality_flag": quality_flag
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
    parser.add_argument(
        '--gcs_output_path',
        required=False,
        default='gs://dataflow-staging-asia-northeast1-952300570255/raw-telemetry/archive',
        help='Đường dẫn thư mục lưu trữ raw JSON trên GCS'
    )
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Định dạng bảng Dead Letter tự động dựa trên bảng đích chính
    # VD: dataset.device_telemetry -> dataset.device_telemetry_dead_letter
    output_table_base = known_args.output_table
    dead_letter_table = f"{output_table_base}_dead_letter"

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    pipeline_options.view_as(beam.options.pipeline_options.StandardOptions).streaming = True

    # Set project environment variable to support local DirectRunner
    from apache_beam.options.pipeline_options import GoogleCloudOptions
    gcp_opts = pipeline_options.view_as(GoogleCloudOptions)
    if gcp_opts.project:
        os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_opts.project

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
                schema="observation_id:STRING,timestamp:TIMESTAMP,station_id:STRING,sensor_type:STRING,metrics:JSON,raw_payload:JSON,quality_flag:STRING",
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
        
        # Luồng ghi lưu trữ dữ liệu thô (raw JSON) lên Google Cloud Storage (GCS)
        if known_args.gcs_output_path:
            (
                pubsub_data
                | "Decode for GCS" >> beam.Map(lambda x: x.decode('utf-8'))
                | "Window for GCS" >> beam.WindowInto(beam.window.FixedWindows(60))
                | "Write to GCS" >> beam.io.WriteToText(
                    file_path_prefix=known_args.gcs_output_path,
                    file_name_suffix=".json",
                    num_shards=1
                )
            )

if __name__ == '__main__':
    run()
