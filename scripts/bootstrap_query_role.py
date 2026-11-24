import json
import os
import boto3

from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
PROFILE= os.getenv("AWS_PROFILE") or None

ROLE_NAME = "cloudrag-query-lambda-role"
COLLECTION = "cloudrag-vectors-dev"

def main():

    session = boto3.Session(
        profile_name=PROFILE,
        region_name=REGION,
    )

    iam = session.client("iam")
    bedrock = session.client("bedrock")
    aoss = session.client("opensearchserverless")

    titan_id = os.getenv(
        "BEDROCK_EMBED_MODEL",
        "amazon.titan-embed-text-v2:0",
    )

    nova_profile_id = os.getenv(
        "BEDROCK_GENERATION_MODEL",
        "apac.amazon.noav-lite-v1:0",
    )

    titan = bedrock.get_foundation_model(
        modelIdentifier=titan_id
    )

    titan_arn = titan[
        "modelDetails"
    ]["modelArn"]

    profile = bedrock.get_inference_profile(
        inferenceProfileIdentifier=nova_profile_id
    )

    profile_arn = profile["inferenceProfileArn"]

    model_arns = [
        model["modelArn"]
        for model in profile["models"]
    ]

    collection_response = aoss.batch_get_collection(
        names=[COLLECTION]
    )

    collection_arn = collection_response[
        "collectionDetails"
    ][0]["arn"]

    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
            }
        ],
    }

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TitanEmbeddingInference",
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": titan_arn,
            },
            {
                "Sid": "NovaInferenceProfile",
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": profile_arn,
            },
            {
                "Sid": "NovaUnderlyingModels",
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": model_arns,
                "Condition": {
                    "StringEquals": {
                        "bedrock:InferenceProfileArn": (
                            profile_arn
                        )
                    }
                },
            },
            {
                "Sid": "OpenSearchDataPlane",
                "Effect": "Allow",
                "Action": "aoss:APIAccessAll",
                "Resource": collection_arn,
            },
        ],
    }

    try:
        response = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description=(
                "CloudRAG query Lambda execution role"
            ),
        )

        role_arn = response["Role"]["Arn"]

    except iam.exceptions.EntityAlreadyExistsException:

        response = iam.get_role(
            RoleName=ROLE_NAME
        )

        role_arn = response["Role"]["Arn"]

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="cloudrag-query-access",
        PolicyDocument=json.dumps(policy),
    )

    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn=(
            "arn:aws:iam::aws:policy/service-role/"
            "AWSLambdaBasicExecutionRole"
        ),
    )

    print("Lambda execution role:", role_arn)

    print("Titan model ARN:", titan_arn)

    print("Nova profile ARN:", profile_arn)

    print("Nova destination models:")

    for arn in model_arns:
        print(" ", arn)

    print("OpenSearch collection ARN:", collection_arn)

if __name__ == "__main__":
    main()




