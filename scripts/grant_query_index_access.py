import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()


REGION = os.getenv("AWS_REGION", "ap-south-1")
PROFILE = os.getenv("AWS_PROFILE") or None

ROLE_NAME = "cloudrag-query-lambda-role"
POLICY_NAME = "cloudrag-vectors-data"

def main():

    session = boto3.Session(
        profile_name=PROFILE,
        region_name=REGION,
    )

    iam = session.client("iam")
    aoss = session.client("opensearchserverless")

    role_arn = iam.get_role(\
        RoleName=ROLE_NAME
        )["Role"]["Arn"]

    response = aoss.get_access_policy(
        type="data",
        name=POLICY_NAME,
    )

    details = response["accessPolicyDetail"]

    existing = details["policy"]

    if isinstance(existing, str):
        rules = json.loads(existing)
    else:
        rules = existing

    if any(
        role_arn in entry.get("Principal", [])
        for entry in rules
    ): 
        print("Role already present in data policy")

        return

    rules.append({
        "Description": "CloudRAG query read access",
        "Principal": [role_arn],
        "Rules": [
            {
                "ResourceType": "index",
                "Resource": [
                    "index/cloudrag-vectors-dev/knowledge-chunks-v2"
                ],
                "Permission": [
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                ],
            }
        ],
    })

    aoss.update_access_policy(
        type="data",
        name=POLICY_NAME,
        policyVersion=details["policyVersion"],
        policy=json.dumps(rules),
    )

    print("Granted OpenSearch read acces to:")
    print(role_arn)

if __name__ == "__main__":
    main()