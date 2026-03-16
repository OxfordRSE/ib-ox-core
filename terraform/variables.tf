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

variable "domain_name" {
  description = <<-EOT
    Custom domain name for the application (e.g. "dashboard.example.ac.uk").
    Leave empty to skip Route 53 / ACM certificate setup.

    Deployment process:
    1. First deploy with domain_name = "" to create the ALB and get its DNS name.
    2. Request an ACM certificate in the AWS Console for this domain (DNS validation).
    3. In Route 53, create a CNAME record: <domain_name> → <alb_dns_name>.
    4. Approve the ACM DNS validation record in Route 53.
    5. Re-deploy with domain_name set and certificate_arn pointing to the validated cert.
  EOT
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = <<-EOT
    ARN of a validated ACM certificate for the domain_name.
    Required when domain_name is set. The deployment will fail if domain_name is
    provided without a valid certificate_arn, to ensure HTTPS is always enforced.
  EOT
  type        = string
  default     = ""

  validation {
    condition = (
      var.domain_name == "" ||
      (var.domain_name != "" && var.certificate_arn != "")
    )
    error_message = "certificate_arn must be set when domain_name is provided. Request an ACM certificate and validate it via DNS before re-deploying."
  }
}
