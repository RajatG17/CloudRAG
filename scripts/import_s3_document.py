import argparse

from pathlib import Path

import boto3

from app.cloud.config import get_aws_settings
from app.cloud.s3_storage import S3DocumentStorage
from app.ingestion.pipeline import process_document

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"

def main():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--key",
        required=True,
        help="S3 object key"
    )
    
    parser.add_argument(
        "--tenant",
        default="demo",
    )
    
    args = parser.parse_args()
    
    settings = get_aws_settings()
    
    session = boto3.Session(
        profile_name=settings.profile,
        region_name=settings.region,
    )
    
    storage = S3DocumentStorage(
        bucket=settings.bucket,
        session=session,
    )
    
    filename = Path(args.key).name
    
    local_path = (
        RAW_DIR / "s3_imports" / filename
    )
    
    print("Downloading document from S3")
    
    storage.download_document(
        key=args.key,
        destination=local_path,
        tenant_id=args.tenant,
    )
    
    print("Running local ingestion pipeline")
    
    chunk_count = process_document(
        local_path
    )
    
    print(
        f"Completed processing: "
        f"{chunk_count} chunks created"
    )
    
if __name__ == "__main__":
    main() 