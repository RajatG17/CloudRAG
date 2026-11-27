import getpass
import os

import boto3

from dotenv import load_dotenv

load_dotenv()

def main():

    username = input(
        "Test username [cloudrag-test]: "
    ).strip() or "cloudrag-test"


    password = getpass.getpass(
        "New test password: "
    )

    confirm = getpass.getpass(
        "Confirm password: "
    )

    if password != confirm:
        raise ValueError("Passwords do not match")

    session = boto3.Session(
        profile_name=os.getenv("AWS_PROFILE") or None,
        region_name = os.getenv("AWS_REGION", "ap-south-1"),
    )

    cognito = session.client("cognito-idp")

    pool_id = os.environ["COGNITO_USER_POOL_ID"]

    cognito.admin_create_user(
        UserPoolId=pool_id,
        Username=username,
        MessageAction="SUPPRESS",
    )

    cognito.admin_set_user_password(
        UserPoolId=pool_id,
        Username=username,
        Password=password,
        Permanent=True,
    )

    print(f"Created test user: {username}")

if __name__ == "__main__":
    main()