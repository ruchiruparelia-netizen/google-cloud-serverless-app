#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import base64
import sys
import os

def run_simulation(endpoint="http://localhost:8080", filename="test-doc.txt", bucket="mock-bucket"):
    print(f"Starting local simulation for GCS notification event...")
    print(f"Target Endpoint: {endpoint}")
    print(f"Target Bucket:   {bucket}")
    print(f"Target File:     {filename}")

    # Ensure local_storage directory exists and create a sample document
    os.makedirs("local_storage", exist_ok=True)
    file_path = os.path.join("local_storage", filename)
    if not os.path.exists(file_path):
        sample_content = (
            "Invoice Summary\n"
            "Invoice Reference: INV-2026-004\n"
            "This document is an urgent billing statement for consulting services.\n"
            "The total amount due is $1,250.00.\n"
            "Please send the payment via bank transfer ASAP.\n"
            "Thank you for your business!"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample_content)
        print(f"Created sample text file at {file_path}")
    else:
        print(f"Using existing file at {file_path}")

    # Construct GCS object finalized event notification payload
    gcs_notification = {
        "kind": "storage#object",
        "id": f"{bucket}/{filename}/1234567890",
        "selfLink": f"https://www.googleapis.com/storage/v1/b/{bucket}/o/{filename}",
        "name": filename,
        "bucket": bucket,
        "generation": "1234567890",
        "metageneration": "1",
        "contentType": "text/plain",
        "timeCreated": "2026-06-28T16:44:00.000Z",
        "updated": "2026-06-28T16:44:00.000Z",
        "storageClass": "STANDARD",
        "size": str(os.path.getsize(file_path)),
        "md5Hash": "mock-md5-hash",
        "mediaLink": "mock-media-link",
        "crc32c": "mock-crc32c",
        "etag": "mock-etag"
    }

    # Base64-encode the GCS notification event payload
    encoded_data = base64.b64encode(json.dumps(gcs_notification).encode("utf-8")).decode("utf-8")

    # Construct the Pub/Sub envelope structure
    pubsub_envelope = {
        "message": {
            "data": encoded_data,
            "messageId": "123456789012",
            "publishTime": "2026-06-28T16:45:00Z"
        },
        "subscription": f"projects/mock-project/subscriptions/mock-sub"
    }

    data = json.dumps(pubsub_envelope).encode("utf-8")

    # Send POST request
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        print(f"Sending simulated Pub/Sub POST request to {endpoint}...")
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
            print(f"\n--- SUCCESS (HTTP {status_code}) ---")
            print(json.dumps(json.loads(response_body), indent=2))
    except urllib.error.HTTPError as e:
        status_code = e.getcode()
        response_body = e.read().decode("utf-8")
        print(f"\n--- ERROR (HTTP {status_code}) ---")
        try:
            print(json.dumps(json.loads(response_body), indent=2))
        except Exception:
            print(response_body)
    except urllib.error.URLError as e:
        print(f"\nConnection failed: {e.reason}")
        print("Make sure your Flask app is running locally (e.g., python src/main.py)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulate GCS Pub/Sub notification upload to Cloud Run.")
    parser.add_argument("--endpoint", default="http://localhost:8080", help="Endpoint URL (default: http://localhost:8080)")
    parser.add_argument("--file", default="test-doc.txt", help="Filename of the mock GCS object (default: test-doc.txt)")
    parser.add_argument("--bucket", default="mock-bucket", help="Name of the mock GCS bucket (default: mock-bucket)")

    args = parser.parse_args()
    run_simulation(endpoint=args.endpoint, filename=args.file, bucket=args.bucket)
