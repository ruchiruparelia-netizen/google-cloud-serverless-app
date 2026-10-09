# ==============================================================================
# JPMorgan Chase — Instant Cross-Channel Credit Card Replacement & Fraud Agent
# Declarative Infrastructure-as-Code (Terraform) for Google Cloud Platform
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud APIs
locals {
  required_apis = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
  ])
}

resource "google_project_service" "enabled_apis" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# 2. Google Artifact Registry Docker Repository
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Container registry for JPMorgan Chase Multi-Agent Platform"
  format        = "DOCKER"
  depends_on    = [google_project_service.enabled_apis]
}

# 3. Dedicated Least-Privilege Runtime Service Account
resource "google_service_account" "agent_runtime_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "JPMC Card & Fraud Agent Cloud Run Service Account"
  description  = "Least-privilege identity for Vertex AI Agent Platform, Memory Bank, and OpenTelemetry Cloud Trace"
  depends_on   = [google_project_service.enabled_apis]
}

locals {
  runtime_iam_roles = toset([
    "roles/aiplatform.user",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
  ])
}

resource "google_project_iam_member" "agent_runtime_permissions" {
  for_each = local.runtime_iam_roles
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

# 4. Secret Manager Configuration for Enterprise Governance
resource "google_secret_manager_secret" "hitl_webhook_secret" {
  secret_id = "${var.service_name}-hitl-signing-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

# 5. Serverless Google Cloud Run v2 Service
resource "google_cloud_run_v2_service" "jpmc_agent_service" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.agent_runtime_sa.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agent_repo.repository_id}/${var.service_name}:${var.image_tag}"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = true
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }
      env {
        name  = "JPMC_REASONING_PRO_MODEL"
        value = var.reasoning_pro_model
      }
      env {
        name  = "JPMC_FAST_FLASH_MODEL"
        value = var.fast_flash_model
      }
      env {
        name  = "JPMC_LITE_TELEMETRY_MODEL"
        value = var.lite_telemetry_model
      }
      env {
        name  = "HITL_DISPUTE_THRESHOLD_USD"
        value = tostring(var.hitl_dispute_threshold_usd)
      }

      startup_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        initial_delay_seconds = 3
        period_seconds        = 5
        failure_threshold     = 5
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        period_seconds    = 15
        failure_threshold = 3
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.agent_repo,
    google_project_iam_member.agent_runtime_permissions,
  ]
}

# 6. Cloud Run Invoker IAM Policy
resource "google_cloud_run_v2_service_iam_member" "invoker_binding" {
  project  = var.project_id
  location = google_cloud_run_v2_service.jpmc_agent_service.location
  name     = google_cloud_run_v2_service.jpmc_agent_service.name
  role     = "roles/run.invoker"
  member   = var.invoker_principal
}
