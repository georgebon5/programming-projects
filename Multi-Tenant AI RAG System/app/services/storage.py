"""
File storage abstraction — pluggable backends for local filesystem and S3.

In development (default) files are stored on local disk.
Set STORAGE_BACKEND=s3 and configure S3_* environment variables for production.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract interface for file storage."""

    @abstractmethod
    def save(self, tenant_id: UUID, filename: str, content: bytes) -> str:
        """Save file content and return the storage path/key."""
        ...

    @abstractmethod
    def read(self, path: str) -> bytes:
        """Read file content by path/key."""
        ...

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete a file by path/key."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a file exists."""
        ...


class LocalStorageBackend(StorageBackend):
    """Store files on local disk under UPLOAD_DIR."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.upload_dir)

    def save(self, tenant_id: UUID, filename: str, content: bytes) -> str:
        tenant_dir = self.base_dir / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_dir / filename
        file_path.write_bytes(content)
        return str(file_path)

    def read(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def delete(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()

    def exists(self, path: str) -> bool:
        return Path(path).is_file()


class S3StorageBackend(StorageBackend):
    """Store files in an S3-compatible bucket (AWS S3, MinIO, DigitalOcean Spaces, etc.)."""

    def __init__(self) -> None:
        import boto3

        session_kwargs: dict = {}
        if settings.s3_access_key_id:
            session_kwargs["aws_access_key_id"] = settings.s3_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key

        client_kwargs: dict = {"region_name": settings.s3_region}
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url

        self._client = boto3.client("s3", **session_kwargs, **client_kwargs)
        self._bucket = settings.s3_bucket_name

    def _key(self, tenant_id: UUID, filename: str) -> str:
        return f"uploads/{tenant_id}/{filename}"

    def save(self, tenant_id: UUID, filename: str, content: bytes) -> str:
        key = self._key(tenant_id, filename)
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content)
        logger.info("S3 upload: s3://%s/%s (%d bytes)", self._bucket, key, len(content))
        return key

    def read(self, path: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=path)
        return response["Body"].read()

    def delete(self, path: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=path)
        logger.info("S3 delete: s3://%s/%s", self._bucket, path)

    def exists(self, path: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=path)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise


def get_storage_backend() -> StorageBackend:
    """Factory — returns the configured storage backend."""
    if settings.storage_backend == "s3":
        return S3StorageBackend()
    return LocalStorageBackend()
