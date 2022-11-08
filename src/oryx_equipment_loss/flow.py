"""
Prefect Flow for Oryx equipment loss data.
"""
import json
from datetime import datetime
from typing import List

import requests
from prefect import flow, task
from prefect.filesystems import S3

from src.config import config
from src.oryx_equipment_loss.transform.oryx_parser import parse
from src.utils import gzip_compress_bytes


bucket: S3 = S3.load("oryx-equipment-loss-storage")

ENCODING = 'utf-8'
BELLIGERENTS = dict(
    russia="https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html",
    ukraine="https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html"
)


@task(retries=config.download_task_retries, retry_delay_seconds=config.download_task_retry_delay_seconds)
def download_page_bytes(url: str) -> bytes:
    """Downloads a web page and returns it in bytes.

    :param url: URL to download
    :return:    Web page in bytes
    """
    r: requests.Response = requests.get(url)
    r.raise_for_status()
    return r.text.encode(ENCODING)


@task
def parse_page(belligerent: str, page: bytes) -> List[dict]:
    """Parses a belligerent's page bytes into a list of equipment loss case documents.

    :param belligerent: Belligerent the page belongs to
    :param page:        Web page as bytes
    :return:            Equipment loss cases
    """
    return list(parse(belligerent, page))


@task
def union_equipment_loss_sets(sets: List[List[dict]]) -> List[dict]:
    """Unions the datasets of the belligerents and inserts them into a document.

    :param sets: _description_
    :return: _description_
    """
    data = []
    for subset in sets:
        data.extend(subset)
    return data


@task
def convert_data_to_bytes(data: dict) -> bytes:
    """Encodes a dictionary into bytes.

    :param data:    Dictionary to encoded
    :return:        Dictionary encoded in bytes with the pipeline's standard encoding
    """
    return json.dumps(data).encode(ENCODING)


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


@flow
def oryx_equipment_loss_flow():
    """Prefect flow
    """
    runtime_meta: dict = get_flow_run_meta()
    parsed_data: List[dict] = []
    for belligerent, url in BELLIGERENTS.items():
        page = download_page_bytes.submit(url)

        # Upload copy of pulled page
        compressed_page = gzip_compress_bytes(page, compresslevel=9)
        page_key = f"raw/{runtime_meta['date']}_{belligerent}.html.gzip"
        bucket.write_path(page_key, content=compressed_page)

        # Parse
        subset:  List[dict] = parse_page.submit(belligerent, page)
        parsed_data.append(subset)

    # Union all parsed data sets
    dataset = union_equipment_loss_sets(parsed_data)
    data: dict = {
        'meta': runtime_meta,
        'data': dataset
    }
    data_bytes: bytes = convert_data_to_bytes(data)
    compressed_bytes: bytes = gzip_compress_bytes(data_bytes, compresslevel=9)

    # Archive
    archive_key: str = f"archive/{runtime_meta['date']}.json.gzip"
    bucket.write_path(archive_key, compressed_bytes)

    # Latest result
    bucket.write_path("latest.json.gzip", compressed_bytes)


if __name__ == "__main__":
    oryx_equipment_loss_flow()
