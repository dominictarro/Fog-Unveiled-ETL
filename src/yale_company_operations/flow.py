"""

"""
import json
from datetime import datetime

import requests
from prefect import task, flow
from prefect.filesystems import S3

from src.config import config
from src.utils import gzip_compress_bytes
from src.yale_company_operations.transform.yale_parser import parse_page

bucket: S3 = S3.load("yale-company-operations-storage")


ENCODING: str = 'utf-8'
URL: str = "https://som.yale.edu/story/2022/over-1000-companies-have-curtailed-operations-russia-some-remain"


@task(retries=config.download_task_retries, retry_delay_seconds=config.download_task_retry_delay_seconds)
def get(url: str, *args, **kwds) -> requests.Response:
    r: requests.Response = requests.get(url, *args, **kwds)
    r.raise_for_status()
    return r


@task
def encode_response(r: requests.Response, encoding: str = ENCODING) -> bytes:
    return r.text.encode(encoding)


@task
def get_flow_run_meta() -> dict:
    """Generates a metadata document.
    """
    now = datetime.utcnow()
    meta = dict(
            created_at=now.isoformat(),
            date=now.strftime(r"%Y-%m-%d")
    )
    return meta


@task
def convert_data_to_bytes(data: dict) -> bytes:
    """Encodes a dictionary into bytes.

    :param data:    Dictionary to encoded
    :return:        Dictionary encoded in bytes with the pipeline's standard encoding
    """
    return json.dumps(data).encode(ENCODING)


@flow
def yale_company_operations_flow():
    """Prefect flow
    """
    runtime_meta: dict = get_flow_run_meta()
    r: requests.Response = get(URL)
    page: bytes = encode_response(r)

    # Upload a copy of pulled page
    compressed_page = gzip_compress_bytes(page, compresslevel=9)
    page_key = f"raw/{runtime_meta['date']}.html.gzip"
    bucket.write_path(page_key, content=compressed_page)

    parsed_data: dict = parse_page(page=page)
    data: dict = {
        'meta': runtime_meta,
        'data': parsed_data
    }

    data_bytes: bytes = convert_data_to_bytes(data)
    compressed_data = gzip_compress_bytes(data_bytes, compresslevel=9)

    # Archive
    archive_key: str = f"archive/{runtime_meta['date']}.json.gzip"
    bucket.write_path(archive_key, compressed_data)

    # Latest result
    bucket.write_path("latest.json.gzip", compressed_data)
