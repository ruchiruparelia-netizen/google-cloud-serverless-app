# ==============================================================================
# Terraform Input Variables for JPMC Cross-Channel Agent Platform
# ==============================================================================

variable "project_id" {
  description = "Google Cloud Platform Project ID"
  type        = string
  default     = "ruchi-agent-poc"

  validation {
    condition     = length(var.project_id) > 3
    error_message = "The GCP project_id must be a valid non-empty project identifier."
  }
}

variable "region" {
  description = "Primary Google Cloud region for Cloud Run and Vertex AI Agent Platform"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "jpmc-card-fraud-agent"
}

variable "artifact_repo_name" {
  description = "Artifact Registry Docker repository ID"
  type        = string
  default     = "jpmc-agents-repo"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "reasoning_pro_model" {
  description = "Gemini Pro model tier for Lead Synthesizer and 5-Avenue Veracity Gatekeeper"
  type        = string
  default     = "gemini-2.5-pro"
}

variable "fast_flash_model" {
  description = "Gemini Flash model tier for low-latency Fraud Velocity and Card Ops execution"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "lite_telemetry_model" {
  description = "Gemini Flash-Lite model tier for high-throughput IVR and mobile telemetry ingestion"
  type        = string
  default     = "gemini-2.5-flash-lite"
}

variable "hitl_dispute_threshold_usd" {
  description = "Dollar threshold above which programmatic Human-in-the-Loop (HITL) approval is enforced"
  type        = number
  default     = 2500.00
}

variable "min_instances" {
  description = "Minimum number of warm Cloud Run container instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of auto-scaled Cloud Run container instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "vCPU allocation per Cloud Run instance"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory allocation per Cloud Run instance"
  type        = string
  default     = "1Gi"
}

variable "invoker_principal" {
  description = "IAM principal granted roles/run.invoker (e.g. allUsers or user:ruchi@rrangan.altostrat.com)"
  type        = string
  default     = "user:ruchi@rrangan.altostrat.com"
}
