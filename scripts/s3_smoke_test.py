from pathlib import Path

import boto3

from app.cloud.config import get_aws_settings
from app.cloud.s3_storage import (
    S3DocumentStorage,
    calculate_sha256,
)

ROOT = Path(__file__).resolve().parents[1]

def main():
    
    settings = get_aws_settings()
    
    session = boto3.Session(
        profile_name=settings.profile,
        region_name=settings.region,
    )
    
    storage = S3DocumentStorage(
        bucket=settings.bucket,
        session=session,
    )
    
    source = (
        ROOT
        / "data"
        / "raw"
        / "payment_architecture.txt"
    )
    
    if not source.exists():
        raise FileNotFoundError(source)
    
    print("\n[1] Uploading document")
    
    first = storage.upload_document(
        source,
        tenant_id="demo",
    )
    
    print(f"Status: {first.status}")
    print(f"Key: {first.key}")
    print(f"Version: {first.version_id}")
    
    print("\n[2] Testing duplicate upload")
    
    second = storage.upload_document(
        source,
        tenant_id="demo",
    )
    
    assert second.status == "already_exists"
    assert second.key == first.key
    
    print("Duplicate upload prevented")
    
    print("\n[3] Fetching object metadata")
    
    metadata = storage.get_document_metadata(
        first.key,
        tenant_id="demo",   
    )
    
    print(metadata)
    
    assert metadata["sha256"] == first.sha256
    
    print("\n[4] Downloading document")

    destination = (
        ROOT
        / "data"
        / "downloaded"
        / source.name
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    storage.download_document(
        first.key,
        destination,
        tenant_id="demo",
    )
    
    original_hash = calculate_sha256(
        source.read_bytes()
    )
    
    downloaded_hash = calculate_sha256(
        destination.read_bytes()
    )
    
    assert original_hash == downloaded_hash
    
    print("SHA256 integrity check passed")
    
    print("\nM2.2 S3 smoke test PASSED")
    

if __name__ == "__main__":
    main()
    
    