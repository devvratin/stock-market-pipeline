"""Idempotent uploader from local Medallion folders (Bronze/Silver/Gold) to Azure Data Lake."""

from pathlib import Path

from azure.storage.blob import BlobServiceClient

from stress.common import config
from stress.common.logging_setup import get_logger

logger = get_logger(__name__)


def upload_directory_to_adls(
    local_dir: Path,
    container_name: str,
    prefix: str,
    blob_service_client: BlobServiceClient,
) -> list[str]:
    """Upload all files under local_dir to ADLS Gen2 with overwrite=True (idempotent)."""
    if not local_dir.exists():
        logger.warning("Local directory does not exist, skipping: %s", local_dir)
        return []

    container_client = blob_service_client.get_container_client(container_name)
    uploaded_blobs: list[str] = []

    for file_path in sorted(local_dir.rglob("*")):
        if not file_path.is_file():
            continue

        relative_posix = file_path.relative_to(local_dir).as_posix()
        blob_name = f"{prefix.strip('/')}/{relative_posix}"

        with file_path.open("rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)

        uploaded_blobs.append(blob_name)
        logger.info("Uploaded %s -> %s/%s", file_path, container_name, blob_name)

    return uploaded_blobs


def sync_medallion_to_adls(
    data_dir: Path = config.DATA_DIR,
    connection_string: str = config.AZURE_STORAGE_CONNECTION_STRING,
    container_name: str = config.AZURE_CONTAINER_NAME,
    blob_service_client: BlobServiceClient | None = None,
) -> dict[str, int]:
    """Sync local bronze/, silver/, and gold/ directories into ADLS Gen2."""
    if blob_service_client is None:
        if not connection_string:
            raise ValueError("Missing AZURE_STORAGE_CONNECTION_STRING in .env")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    counts: dict[str, int] = {}
    for layer in ("bronze", "silver", "gold"):
        uploaded = upload_directory_to_adls(
            local_dir=data_dir / layer,
            container_name=container_name,
            prefix=layer,
            blob_service_client=blob_service_client,
        )
        counts[layer] = len(uploaded)

    logger.info("ADLS sync complete: %s", counts)
    return counts