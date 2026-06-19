# backend/app/core/storage.py
import hashlib
from datetime import timedelta
from io import BytesIO

from minio import Minio

from app.core.settings import Settings


def minio_client(settings: Settings) -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password.get_secret_value(),
        secure=settings.minio_use_ssl,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put_object(
    client: Minio,
    bucket: str,
    key: str,
    data: bytes,
    content_type: str,
) -> None:
    client.put_object(bucket, key, BytesIO(data), len(data), content_type=content_type)


def presigned_get(client: Minio, bucket: str, key: str, ttl_minutes: int = 5) -> str:
    return client.presigned_get_object(bucket, key, expires=timedelta(minutes=ttl_minutes))
