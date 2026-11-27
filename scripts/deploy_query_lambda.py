import os
import boto3

from dotenv import load_dotenv

load_dotenv()

FUNCTION_NAME = "cloudrag-query-api"
ROLE_NAME = "cloudrag-query-lambda-role"

def main():

    image_uri = os.environ["CLOUDRAG_IMAGE_URI"]

    session = boto3.Session(
        profile_name=os.getenv("AWS_PROFILE") or None,
        region_name=os.getenv(
            "AWS_REGION",
            "ap-south-1",
        ),
    )

    iam = session.client("iam")
    client = session.client("lambda")

    role_arn = iam.get_role(
        RoleName=ROLE_NAME
    )["Role"]["Arn"]

    variables = {
        "AOSS_ENDPOIND": os.environ["AOSS_ENDPOINT"],
        "AOSS_INDEX": os.getenv(
            "AOSS_INDEX",
            "knowledge-chunks-v2",
        ),
        "CLOUDRAG_RETRIEVER": "opensearch",
        "CLOUDRAG_LLM_PROVIDER": "bedrock",
        "CLOUDRAG_DEFAULT_TENANT": "demo",
        "BEDROCK_EMBED_MODEL": os.getenv(
            "BEDROCK_EMBED_MODEL",
            "amazon.titan-embed-text-v2:0",
        ),
        "BEDROCK_EMBED_DIMENSIONS": "512",
        "BEDROCK_GENERATION_MODEL": os.getenv(
            "BEDROCK_GENERATION_MODEL",
            "apac.amazon.nova-lite-v1:0",
        ),
        "BEDROCK_MAX_OUTPUT_TOKENS": "256",
        "COGNITO_APP_CLIENT_ID": os.environ[
            "COGNITO_APP_CLIENT_ID"
        ],
        "AOSS_TIMEOUT_SECONDS": "10",
        "AOSS_MAX_RETRIES": "0",
        "BEDROCK_READ_TIMEOUT_SECONDS": "12",
        "BEDROCK_TOTAL_ATTEMPTS": "1",
    }

    configuration = {
        "Timeout": 28,
        "MemorySize": 1024, 
        "Environment": {
            "Variables": variables,
        },
    }

    try:

        client.get_function(
            FunctionName=FUNCTION_NAME,
        )

        exists = True
    except client.exceptions.ResourceNotFoundException:
        exists = False

    if not exists:

        print("Creating lambda function")

        client.create_function(
            FunctionName=FUNCTION_NAME,
            PackageType="Image",
            Code={
                "ImageUri": image_uri,
            },
            Role=role_arn,
            Architectures=["x86_64"],
            **configuration
        )

        client.get_waiter(
            "function_active_v2"
        ).wait(FunctionName=FUNCTION_NAME)

    else:

        print("Updating Lambda container image")

        client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ImageUri=image_uri,
        )

        client.get_waiter(
            "function_updated_v2"
        ).wait(FunctionName=FUNCTION_NAME)

        print("Updating Lambda configuration")

        client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            **configuration,
        )

        client.get_waiter(
            "function_updated_v2"
        ).wait(FunctionName=FUNCTION_NAME)

    response = client.get_function(
        FunctionName=FUNCTION_NAME
    )
    
    print("Function ARN:")
    print(response["Configuration"]["FunctionArn"])

    print("State:")
    print(response["Configuration"]["State"])

    print("Last update status:")
    print(
        response["Configuration"]["LastUpdateStatus"]
    )


if __name__ == "__main__":
    main()