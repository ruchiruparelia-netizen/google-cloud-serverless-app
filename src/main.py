import os
import base64
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config from environment variables
MOCK_GCP = os.environ.get("MOCK_GCP", "false").lower() == "true"
PROJECT_ID = os.environ.get("PROJECT_ID", "mock-project-id")
BQ_DATASET = os.environ.get("BQ_DATASET", "document_pipeline")
BQ_TABLE = os.environ.get("BQ_TABLE", "metadata")

# Initialize GCP clients unless mocking
if not MOCK_GCP:
    try:
        from google.cloud import storage
        from google.cloud import bigquery
        
        storage_client = storage.Client()
        bq_client = bigquery.Client()
        logger.info("GCP Clients initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {e}. Falling back to MOCK_GCP=true.")
        MOCK_GCP = True
else:
    logger.info("Running in local MOCK_GCP mode. External GCP calls will be simulated.")


def simulate_ocr(content: str):
    """
    Simulates OCR on the document text.
    Extracts word count and tags based on simple content analysis.
    """
    words = content.split()
    word_count = len(words)
    
    # Simple tag extraction based on keywords
    possible_tags = {
        "invoice": ["invoice", "bill", "payment", "amount", "due"],
        "receipt": ["receipt", "purchase", "store", "tax"],
        "contract": ["contract", "agreement", "party", "signature", "terms"],
        "report": ["report", "analysis", "summary", "finding", "result"],
        "urgent": ["urgent", "asap", "immediate", "attention"]
    }
    
    tags = set()
    content_lower = content.lower()
    for tag, keywords in possible_tags.items():
        if any(keyword in content_lower for keyword in keywords):
            tags.add(tag)
            
    # Default tag if none found
    if not tags:
        tags.add("document")
        
    return word_count, list(tags)


@app.route("/", methods=["POST"])
def handle_pubsub_push():
    """
    Endpoint that receives Pub/Sub push messages.
    """
    envelope = request.get_json()
    if not envelope:
        msg = "No JSON payload received"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "Invalid Pub/Sub message format"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    pubsub_message = envelope["message"]
    if "data" not in pubsub_message:
        msg = "No data payload in Pub/Sub message"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    # Parse and decode base64 Pub/Sub data
    try:
        data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        event_data = json.loads(data_str)
    except Exception as e:
        msg = f"Failed to decode base64 Pub/Sub data: {e}"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    # Extract bucket and file info
    bucket_name = event_data.get("bucket")
    object_name = event_data.get("name")
    time_created = event_data.get("timeCreated")

    if not bucket_name or not object_name:
        msg = "Missing bucket or name in GCS notification event"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    logger.info(f"Received notification for file: gs://{bucket_name}/{object_name}")

    # Step 1: Download file content
    content = ""
    if MOCK_GCP:
        # Simulate download: look for file in local_storage directory or use mock content
        local_path = os.path.join("local_storage", object_name)
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(f"[Mock] Successfully read file content from local_storage/{object_name}")
            except Exception as e:
                logger.error(f"[Mock] Failed to read local file {local_path}: {e}")
                content = "This is a mock fallback text representing file contents."
        else:
            logger.info(f"[Mock] Local file {local_path} not found. Using default mock text.")
            content = "Invoice summary: The total due for invoice #1024 is $250. Please send payment ASAP."
    else:
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            content = blob.download_as_text()
            logger.info(f"Successfully downloaded file content from GCS.")
        except Exception as e:
            msg = f"Failed to download file from GCS: {e}"
            logger.error(msg)
            return jsonify({"error": msg}), 500

    # Step 2: Simulated OCR
    word_count, tags = simulate_ocr(content)
    tags_str = ", ".join(tags)
    
    # Step 3: Date metadata
    # Parse event creation time or default to current UTC time
    if time_created:
        # Standard GCS time format is ISO 8601 UTC: 2026-06-28T16:00:00.000Z
        # BigQuery TIMESTAMP accepts ISO 8601 strings
        date_str = time_created
    else:
        date_str = datetime.now(timezone.utc).isoformat()

    # Log extracted metadata
    logger.info(f"Extracted metadata - Filename: {object_name}, Date: {date_str}, Tags: {tags_str}, Word Count: {word_count}")

    # Step 4: Stream metadata to BigQuery
    row_data = {
        "filename": object_name,
        "date": date_str,
        "tags": tags_str,
        "word_count": word_count
    }

    if MOCK_GCP:
        logger.info(f"[Mock] Inserting row into BigQuery table {PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}: {row_data}")
        # Append to a mock log file for verification
        os.makedirs("local_storage", exist_ok=True)
        with open("local_storage/mock_bigquery_inserts.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row_data) + "\n")
    else:
        try:
            table_ref = bq_client.dataset(BQ_DATASET).table(BQ_TABLE)
            table = bq_client.get_table(table_ref)
            errors = bq_client.insert_rows(table, [row_data])
            if errors:
                msg = f"BigQuery insert_rows failed: {errors}"
                logger.error(msg)
                return jsonify({"error": msg}), 500
            logger.info("Successfully streamed row to BigQuery.")
        except Exception as e:
            msg = f"Failed to stream row to BigQuery: {e}"
            logger.error(msg)
            return jsonify({"error": msg}), 500

    return jsonify({"status": "success", "metadata": row_data}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
