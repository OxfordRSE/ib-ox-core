variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "app_name" {
  description = "Application name (used as prefix for all resources)"
  type        = string
  default     = "ib-ox-core"
}

variable "image_tag" {
  description = "Docker image tag to deploy (e.g. 0.1.0)"
  type        = string
}

variable "api_min_n" {
  description = "Minimum N (student count) for suppression"
  type        = number
  default     = 5
}

variable "api_secret_key" {
  description = "JWT secret key for the API"
  type        = string
  sensitive   = true
}

variable "container_cpu" {
  description = "CPU units for each container (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory in MiB for each container"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS (leave empty for HTTP-only)"
  type        = string
  default     = ""
}
