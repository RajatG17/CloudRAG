import hashlib
import mimetypes
import os
import re
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError

MAX_FILE_SIZE = 20*1024*1024 # 20 MB

ALLOWED_EXTENSIONS = {".pdf", ".txt"}

@dataclass(frozen=True)
class UploadResult:
    """Dataclass to hold the result of an upload operation."""
    bucket: str
    key: str
    sha256: str
    version_id: str | None
    status: str

def validate_tenant_id(tenant_id: str) -> None:
    if not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{0,62}",
        tenant_id
    ):
        raise ValueError(
            "Invalid tenant_id."
        )

def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_object_key(
    tenant_id: str,
    filename: str,
    sha256: str,
) -> str:
    """Generate a unique S3 object key based on tenant_id, filename, and SHA256 hash.

    Args:
        tenant_id (str): The tenant ID.
        filename (str): The name of the file.
        sha256 (str): The SHA256 hash of the file content.

    Returns:
        str: A unique S3 object key.
    """
    validate_tenant_id(tenant_id)
    
    # Extract the file extension
    _, ext = os.path.splitext(filename)
    
    # Ensure the extension is in lowercase
    ext = ext.lower()
    
    # Validate the file extension
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file extension '{ext}'. Allowed extensions are: {ALLOWED_EXTENSIONS}"
        )
        
    safe_filename = re.sub(r"[^A-Za-z0-9._-]","_",Path(filename).name,)
   
    
    # Construct the object key
    object_key = f"uploads/{tenant_id}/{sha256[:2]}/{sha256}/{safe_filename}"

    return object_key

class S3DocumentStorage:
    
    def __init__(
        self,
        bucket: str,
        session: Any,
        
    ):
        
        if not bucket:
            raise ValueError("Bucket name is required")
        
        self.bucket = bucket
        self.client = session.client("s3")
        
    @staticmethod
    def _validate_Key(
        key: str,
        tenant_id: str,
    ) -> None:
        validate_tenant_id(tenant_id)
        
        expected_prefix = f"uploads/{tenant_id}"
        
        if not key.startswith(expected_prefix):
            raise ValueError(
                "Object key does not belong to this tenant"
            )
    
    def upload_document(
        self,
        file_path: str | Path,
        tenant_id: str,
    ) -> UploadResult:
        """Upload a document to S3.

        Args:
            file_path (str | Path): The path to the file to be uploaded.
            tenant_id (str): The tenant ID.

        Returns:
            UploadResult: An object containing details of the upload operation.
        """
        validate_tenant_id(tenant_id)
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension '{file_path.suffix}'. Allowed extensions are: {ALLOWED_EXTENSIONS}"
            )
        
        if file_path.stat().st_size==0 or file_path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(f"File size must be between 1 and {MAX_FILE_SIZE} bytes")
        
        with file_path.open("rb") as f:
            data = f.read()
        
        sha256_hash = calculate_sha256(data)
        
        object_key = make_object_key(
            tenant_id=tenant_id,
            filename=file_path.name,
            sha256=sha256_hash,
        )
        
        content_type = (
            mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        )
        
        try:
            response = self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=data,
                ContentType=content_type,
                Metadata={
                    "tenant_id": tenant_id,
                    "sha256": sha256_hash
                },
                IfNoneMatch="*",
                ChecksumAlgorithm="SHA256",
            )
            
            version_id = response.get("VersionId")
            
            return UploadResult(
                bucket=self.bucket,
                key=object_key,
                sha256=sha256_hash,
                version_id=version_id,
                status="uploaded",
            )
            
        except ClientError as e:
            
            code = e.response["Error"]["Code"]
            
            if code not in {"412", "PreconditionFailed"}:
                raise
        
            metadata = self.get_document_metadata(object_key, tenant_id,)
            
            if metadata["sha256"] != sha256_hash:
                raise RuntimeError(
                    "Existing object hash mismatch. Upload aborted."
                )
                
            return UploadResult(
                bucket=self.bucket,
                key=object_key,
                sha256=sha256_hash,
                version_id=metadata.get("version_id"),
                status="already_exists",
            )
        
    def get_document_metadata(
        self, 
        key: str,
        tenant_id: str,
    ) -> dict:
        """Retrieve metadata for a document stored in S3.

        Args:
            key (str): The S3 object key.
            tenant_id (str): The tenant ID.

        Returns:
            dict: A dictionary containing the document's metadata.
        """
        self._validate_Key(key, tenant_id)
        
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            
            metadata = response.get("Metadata", {})
            
            return {
                    "key": key,
                    "size_bytes": response.get("ContentLength"),
                    "content_type": response.get("ContentType"),
                    "sha256": metadata.get("sha256"),
                    "version_id": response.get("VersionId"),
                    "encryption": response.get("ServerSideEncryption"),
                    }
            
        except ClientError as e:
            code = e.response["Error"]["Code"]
            
            if code == "404":
                raise FileNotFoundError(f"Object not found: {key}")
            
            raise
        
    def download_document(
        self,
        key: str,
        destination: str | Path,
        tenant_id: str,
    ) -> Path:
        """Download a document from S3.

        Args:
            key (str): The S3 object key.
            destination (str | Path): The local path where the file will be saved.
            tenant_id (str): The tenant ID.

        Returns:
            Path: The local path where the file was saved.
        """
        self._validate_Key(key, tenant_id)
        
        metadata = self.get_document_metadata(key, tenant_id)
        
        expected_hash = metadata.get("sha256")
        
        if not expected_hash:
            raise ValueError("SHA256 hash not found in metadata. Cannot verify integrity.")

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(prefix=".cloudrag-",
                                         dir=str(destination.parent),)
        
        os.close(fd)
        
        try:
            extra_args = []
            
            if metadata["version_id"]:
                extra_args.append({"VersionId": metadata["version_id"]})
            
            self.client.download_file(
                self.bucket,
                key,
                temp_name,
                ExtraArgs=extra_args
            )
            
            downloaded_data = Path(temp_name).read_bytes()
            
            actual_hash = calculate_sha256(downloaded_data)
            
            if actual_hash != expected_hash:
                raise ValueError(
                    "Downloaded file hash mismatch"
                )
                
                os.replace(
                    temp_name,
                    destination,
                )
                
        finally:
            Path(temp_name).unlink(missing_ok=True)
            
        return destination