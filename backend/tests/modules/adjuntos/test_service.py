import pytest
from minio import Minio
from testcontainers.minio import MinioContainer

from app.core.settings import get_settings
from app.modules.adjuntos.service import upload_adjunto
from app.shared.exceptions import ValidationError


@pytest.fixture(scope="module")
def minio_container():
    with MinioContainer() as mc:
        yield mc


@pytest.fixture
def minio_client_with_bucket(minio_container):
    cfg = minio_container.get_config()
    client = Minio(cfg["endpoint"], access_key=cfg["access_key"], secret_key=cfg["secret_key"], secure=False)
    bucket = "test-bucket"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    return client, bucket


@pytest.mark.asyncio
async def test_rejects_invalid_mime(db_session, minio_client_with_bucket):
    mc, bucket = minio_client_with_bucket
    settings = get_settings()
    settings.__dict__["minio_bucket"] = bucket  # override for this test
    import uuid
    with pytest.raises(ValidationError):
        await upload_adjunto(
            db_session, mc=mc, settings=settings, licencia_id=uuid.uuid4(),
            nombre_original="x.exe", mime_type="application/x-msdownload",
            payload=b"x", usuario_id=None,
        )
