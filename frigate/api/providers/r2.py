import logging

import boto3
from botocore.client import Config

logger = logging.getLogger(__name__)

from frigate.api.providers.base import (
    FileMetadata,
    FileResult,
    FileUploaderProvider,
    SignedUrlExpirationTime,
)


def get_r2_client(
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def build_key(m: FileMetadata) -> str:
    return f"videos/{m.station_id}/{m.camera_id}/{m.date}/{m.name}"


class R2Provider(FileUploaderProvider):
    """R2 file uploader provider."""

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ):
        self.client = get_r2_client(endpoint_url, access_key_id, secret_access_key)
        self.bucket_name = bucket_name

    def presigned_url(self, metadata: FileMetadata) -> FileResult:
        result = FileResult()

        object_key = build_key(metadata)
        metadata = {
            "max_size_mb": metadata.max_size_mb,
            "station_id": metadata.station_id,
            "camera_id": metadata.camera_id,
        }

        try:
            presigned_url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=SignedUrlExpirationTime,
                HttpMethod="PUT",
            )

            result.url = presigned_url

        except Exception as e:
            print(e)
            logger.error(f"error pre-signing url for file upload due to: {e}")
            result.url = ""

        return result
