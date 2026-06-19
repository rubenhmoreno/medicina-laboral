# backend/app/core/storage.py
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
