import boto3
import datetime

class S3Connector:
    def __init__(self, bucket_name: str, split_by_day: bool = False):
        self.bucket_name = bucket_name
        self.split_by_day = split_by_day
        self.s3 = boto3.client('s3')

    def export(self, file_path: str, exported_metric: str, output_name: str):
        full_out_path = f"{exported_metric}/{output_name}"
        
        if self.split_by_day:
            full_out_path = f"{exported_metric}/{datetime.datetime.now().strftime('%Y-%m-%d')}/{output_name}"

        with open(file_path, "rb") as f:
            self.s3.put_object(Bucket=self.bucket_name, Key=full_out_path, Body=f)
        print(f"{file_path} uploaded to: {self.bucket_name}/{exported_metric}/{full_out_path}")