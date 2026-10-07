#!/bin/bash
# ==============================================================================
# JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Agent
# Google Cloud Platform (GCP) Serverless Cloud Run Deployment Script
# ==============================================================================

set -euo pipefail

# 1. Configuration & Defaults
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "ruchi-agent-poc")}"
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

# Ensure service accounts have Cloud Storage permissions for Cloud Build staging
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null || echo "")
if [ -n "${PROJECT_NUMBER}" ]; then
  echo "Setting Cloud Storage permissions for project service accounts..."
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" --quiet 2>/dev/null || true
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" --quiet 2>/dev/null || true
fi

# 3. Build & Deploy to Serverless Cloud Run
echo "Step 2: Building container and deploying to Cloud Run..."
if ! gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}"; then
  echo "Cloud Build submit fallback: Deploying directly from source..."
  gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --platform=managed \
    --region="${REGION}" \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}" \
    --project="${PROJECT_ID}"
else
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
fi

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --format='value(status.url)' --project="${PROJECT_ID}")

echo "=========================================================================="
echo "  Deployment Completed Successfully!"
echo "  Live Service URL: ${SERVICE_URL}"
echo "  Customer Chat UI: ${SERVICE_URL}/"
echo "  Agent Info:       ${SERVICE_URL}/api/agents/list"
echo "  Evaluation:       ${SERVICE_URL}/api/rubric/scores"
echo "=========================================================================="
