"""
Container class for loading the pipeline's configuration.
"""
import dataclasses
import os

import marshmallow_dataclass
from prefect.filesystems import S3


@dataclasses.dataclass
class Config:
    download_task_retries: int
    download_task_retry_delay_seconds: int
    upload_task_retries: int
    upload_task_retry_delay_seconds: int


config: Config = Config(
    download_task_retries=os.getenv('DOWNLOAD_TASK_RETRIES', 5),
    download_task_retry_delay_seconds=os.getenv('DOWNLOAD_TASK_RETRY_DELAY_SECONDS', 60),
    upload_task_retries=os.getenv('UPLOAD_TASK_RETRIES', 5),
    upload_task_retry_delay_seconds=os.getenv('UPLOAD_TASK_RETRY_DELAY_SECONDS', 60)
)

# Shared Blocks from Prefect Cloud
prefect_fs = S3.load("fog-unveiled-bucket")
