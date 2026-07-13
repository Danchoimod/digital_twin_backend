uvicorn src.main:app --reload
python etl_pipeline.py --runner=DirectRunner --project=automatic-vent-443012-g2 --temp_location=gs://dataflow-staging-asia-northeast1-952300570255/temp --input_subscription=projects/automatic-vent-443012-g2/subscriptions/digital_twin_sub --output_table=automatic-vent-443012-g2:test.device_telemetry
