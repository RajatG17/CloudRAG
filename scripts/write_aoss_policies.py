import json
import os
from pathlib import Path

COLLECTION = "cloudrag-vectors-dev"
INDEX = "knowledge-chunks-v1"

OUT_DIR = Path("infrastructure/aoss")

OUT_DIR.mkdir(parents=True, exist_ok=True)

def write_policy(filename, policy):
    
    path = OUT_DIR/ filename
    
    path.write_text(
        json.dumps(policy, indent=2),
        encoding="utf-8",
    )
    
    print(f"Wrote {path}")
    
def main():
    
    principal = os.getenv("AOSS_PRINCIPAL_ARN")
    
    if not principal:
        raise ValueError(
            "Use an IAM user or IAM role ARN, "
            "not an STS session ARN"
        )
        
    encryption = {
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": [
                    f"collection/{COLLECTION}"
                ],
            }
        ],
        "AWSOwnedKey": True,
    }
    
    network = [
        {
            "Description": (
                "Temporary public API access "
                "for local development"
            ),
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [
                        f"collection/{COLLECTION}"
                    ],
                }
            ],
            "AllowFromPublic": True,
        }
    ]
    
    data_access = [
        {
            "Rules": [
                {
                    "ResourceType": "index",
                    "Resource": [
                        f"index/{COLLECTION}/{INDEX}"
                    ],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument",
                    ],
                }
            ],
            "Principal": [principal]
        }
    ]
    
    write_policy("encryption.json", encryption)
    write_policy("network.json", network)
    write_policy("data-access.json", data_access)
    
if __name__ == "__main__":
    main()