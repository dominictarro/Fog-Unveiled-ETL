"""

"""
from __future__ import annotations
import gzip

from prefect import task


@task
def gzip_compress_bytes(data: bytes, compresslevel: int = 9) -> bytes:
    return gzip.compress(data, compresslevel=compresslevel)
