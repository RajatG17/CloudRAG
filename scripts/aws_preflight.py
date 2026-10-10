import os

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)

AWS_PROFILE = os.getenv(
    "AWS_PROFILE",
    "cloudrag-dev",
)

AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-south-1",
)

def create_session() -> boto3.Session:
    """_summary_

    Returns:
        boto3.Session: _description_
    """
    
    return boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION,
    )
    
def verify_identity(session: boto3.Session):
    """ Verify AWS authentication using STS."""
    
    client = session.client("sts")
    
    response = client.get_caller_identity()
    
    print("\nAWS Identity")
    
    print(f"Account: {response['Account']}")
    print(f"Principal: {response['Arn']}")

    return response

def verify_s3(session: boto3.Session):
    """
    Verify permission to list S3 buckets.
    """

    client = session.client("s3")

    response = client.list_buckets()

    buckets = response.get("Buckets", [])

    print("\nAmazon S3")

    print("Connection successful")
    print(f"Existing buckets: {len(buckets)}")


def verify_bedrock(session: boto3.Session):
    """
    Check embedding model availability.
    """

    client = session.client("bedrock")

    response = client.list_foundation_models(
        byOutputModality="EMBEDDING",
    )

    models = response.get(
        "modelSummaries",
        [],
    )

    model_ids = {
        model["modelId"]
        for model in models
    }

    target_model = (
        "amazon.titan-embed-text-v2:0"
    )

    print("\nAmazon Bedrock")

    print(f"Embedding models found: {len(models)}")

    print(
        f"Titan Embeddings V2 available: "
        f"{target_model in model_ids}"
    )


def verify_opensearch(session: boto3.Session):
    """
    Verify OpenSearch Serverless API access.
    """

    client = session.client(
        "opensearchserverless"
    )

    response = client.list_collection_groups()

    groups = response.get(
        "collectionGroupSummaries",
        [],
    )

    print("\nOpenSearch Serverless")

    print("Connection successful")
    print(f"Collection groups found: {len(groups)}")


def main():

    print("=" * 50)
    print("CloudRAG AWS Preflight")
    print("=" * 50)

    print(f"Profile: {AWS_PROFILE}")
    print(f"Region: {AWS_REGION}")

    try:
        session = create_session()

        verify_identity(session)

        checks = [
            ("S3", verify_s3),
            ("Bedrock", verify_bedrock),
            ("OpenSearch", verify_opensearch),
        ]

        failures = []

        for name, check in checks:
            try:
                check(session)

            except (ClientError, BotoCoreError) as error:
                failures.append(name)

                print(f"\n{name}: FAILED")
                print(error)

        print("\n" + "=" * 50)

        if failures:
            print(f"Failed checks: {', '.join(failures)}")
            raise SystemExit(1)

        print("All AWS preflight checks passed")

    except (
        NoCredentialsError,
        ProfileNotFound,
        ClientError,
        BotoCoreError,
    ) as error:

        print("\nAWS authentication failed.")
        print(error)

        raise SystemExit(1)


if __name__ == "__main__":
    main()