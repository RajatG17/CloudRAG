import hashlib

import pytest
from botocore.exceptions import ClientError

from app.cloud.s3_storage import  (
    S3DocumentStorage,
    make_object_key
)

class FakeS3Client:
    
    def __init__(self):
        self.objects = {}
        
    def put_object(self, **kwargs):
        key = kwargs["Key"]
        
        if key in self.objects:
            raise ClientError(
                {
                    "Error": {
                        "Code": "PreconditionFailed",
                        "Message": "Object already exists",
                    }
                },
                "PutObject",
            )
        
        self.objects[key] = kwargs
        
        return {"VersionId": "test-version"}

    def head_object(self, **kwargs):
        obj = self.objects[kwargs["Key"]]
        
        return {
            "ContentLength": len(obj["Body"]),
            "ContentType": obj["ContentType"],
            "Metadata": obj["Metadata"],
            "VersionId": "test-version",
            "ServerSideEncryption": "AES256",
        }
        
class FakeSession:
    
    def __init__(self):
        self.s3=FakeS3Client()
    
    def client(self, service_name):
        assert service_name == "s3"
        return self.s3
    
def test_object_key_deterministic():
    
    digest = hashlib.sha256(b"example").hexdigest()
    
    key1 = make_object_key(
        "demo", "test.txt", digest
    )
    
    key2 = make_object_key(
        "demo", "test.txt", digest
    )
    
    assert key1 == key2
    assert key1.startswith("uploads/demo/")
    
def test_invalid_tenant_rejected():
    digest = hashlib.sha256(b"example").hexdigest()
    
    with pytest.raises(ValueError):
        make_object_key(
            "../another-tenant",
            "text.txt",
            digest
        )
        
def test_unsupported_extension_rejected():
    
    digest = hashlib.sha256(b"example").hexdigest()
    
    with pytest.raises(ValueError):
        make_object_key(
            "demo",
            "script.exe",
            digest
        )
        
def test_duplicate_upload(tmp_path):

    file_path = tmp_path / "example.txt"

    file_path.write_text(
        "CloudRAG test document",
        encoding="utf-8",
    )

    storage = S3DocumentStorage(
        bucket="test-bucket",
        session=FakeSession(),
    )

    first = storage.upload_document(
        file_path,
        tenant_id="demo",
    )

    second = storage.upload_document(
        file_path,
        tenant_id="demo",
    )

    assert first.status == "uploaded"
    assert second.status == "already_exists"
    assert first.key == second.key


def test_cross_tenant_key_rejected():

    storage = S3DocumentStorage(
        bucket="test-bucket",
        session=FakeSession(),
    )

    with pytest.raises(ValueError):
        storage.get_document_metadata(
            key="uploads/other/document.pdf",
            tenant_id="demo",
        )