import os

from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AWSSettings:
    region: str
    bucket: str
    profile: str | None
    
def get_aws_settings() -> AWSSettings:
    """Fetch AWS settings from environment variables and return an AWSSettings object.

    Returns:
        AWSSettings: An object of AWSSettings class containing bucket name, region and profile (optional).
    """
    bucket=os.getenv("CLOUDRAG_BUCKET")
    
    if not bucket:
        raise ValueError("CLOUDRAG_BUCKET is not configured")
    
    return AWSSettings(
        region=os.getenv("AWS_REGION", "ap-south-1"),
        bucket=bucket,
        profile=os.getenv("AWS_PROFILE"),
    )