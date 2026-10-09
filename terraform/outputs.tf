# ==============================================================================
# Terraform Outputs for JPMC Cross-Channel Agent Platform
# ==============================================================================

output "cloud_run_service_url" {
  description = "Live HTTPS endpoint URL for the JPMC Cross-Channel Agent Cloud Run service"
  value       = google_cloud_run_v2_service.jpmc_agent_service.uri
}

output "healthcheck_endpoint" {
  description = "Readiness and health probe URL"
  value       = "${google_cloud_run_v2_service.jpmc_agent_service.uri}/healthz"
}

output "artifact_registry_repository_url" {
  description = "Full Artifact Registry Docker repository URI"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agent_repo.repository_id}"
}

output "agent_service_account_email" {
  description = "Dedicated least-privilege service account email for the Cloud Run service"
  value       = google_service_account.agent_runtime_sa.email
}
