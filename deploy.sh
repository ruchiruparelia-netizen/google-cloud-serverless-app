#!/bin/bash
# ==============================================================================
# JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Agent
# Google Cloud Platform (GCP) Serverless Cloud Run Deployment Script
# ==============================================================================

set -euo pipefail

# 1. Configuration & Defaults
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="jpmc-card-fraud-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=========================================================================="
echo "  Deploying JPMC Cross-Channel Credit Card & Fraud Mitigation Agent"
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"
echo "  Service: ${SERVICE_NAME}"
echo "=========================================================================="

if [ -z "${PROJECT_ID}" ]; then
  echo "Error: PROJECT_ID is not set. Please set GOOGLE_CLOUD_PROJECT or run 'gcloud config set project <PROJECT_ID>'."
  exit 1
fi

# 2. Enable Required Google Cloud APIs
echo "Step 1: Enabling necessary Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  cloudtrace.googleapis.com \
  logging.googleapis.com \
  --project="${PROJECT_ID}"

# 3. Build & Submit Container Image via Google Cloud Build
echo "Step 2: Submitting container build to Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}"

# 4. Deploy to Serverless Cloud Run
echo "Step 3: Deploying container to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_NAME}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}" \
  --project="${PROJECT_ID}"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --format='value(status.url)' --project="${PROJECT_ID}")

echo "=========================================================================="
echo "  Deployment Completed Successfully!"
echo "  Live Service URL: ${SERVICE_URL}"
echo "  Customer Chat UI: ${SERVICE_URL}/"
echo "  Agent Info:       ${SERVICE_URL}/api/agents/list"
echo "  Evaluation:       ${SERVICE_URL}/api/rubric/scores"
echo "=========================================================================="
