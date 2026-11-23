import os
from functools import lru_cache
from urllib.parse import urlparse

import boto3
from dotenv import load_dotenv
from opensearchpy import (
    AWSV4SignerAuth,
    OpenSearch,
    RequestsHttpConnection,
)

load_dotenv()

@lru_cache(maxsize=1)
def get_opensearch_client() -> OpenSearch:
    
    endpoint = os.environ["AOSS_ENDPOINT"]
    
    region = os.getenv(
        "AWS_REGION",
        "ap-south-1",
    )
    
    profile = os.getenv("AWS_PROFILE") or None
    
    parsed = urlparse(endpoint)
    
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.path not in {"", "/"}
    ): 
        raise ValueError(
            "AOSS_ENDPOINT must be an HTTPS collection endpoint" 
        )
        
    session = boto3.Session(
        profile_name=profile,
        region_name=region,
    )
    
    credentials = session.get_credentials()
    
    if credentials is None:
        raise RuntimeError("No AWS credentials available")
    
    auth = AWSV4SignerAuth(
        credentials,
        region,
        "aoss",
    )
    
    return OpenSearch(
        hosts=[
            {
                "host": parsed.hostname,
                "port": 443,
            }
        ],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=int(
            os.getenv("AOSS_TIMEOUT_SECONDS", "90")
        ),
        max_retries=int(
            os.getenv("AOSS_MAX_RETRIES", "2")
        ),
        retry_on_timeout=False,
        pool_maxsize=10,
    )