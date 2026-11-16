import os 

from functools import lru_cache

import boto3

from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

@lru_cache(maxsize=1)
def get_bedrock_runtime_client():
    
    profile = os.getenv("AWS_PROFILE") or None
    
    region = os.getenv("AWS_REGION", "ap-south-1")
    
    session = boto3.Session(
        profile_name=profile,
        region_name=region,
    )
    
    config = Config(
        connect_timeout=5,
        read_timeout=90,
        
        retries = {
            "mode": "standard", 
            "total_max_attempts": 3,
        },
        max_pool_connections=10,
    )
    
    return session.client(
        "bedrock-runtime",
        config=config,
    )
    
    