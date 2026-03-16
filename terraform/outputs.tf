output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecr_api_url" {
  description = "ECR repository URL for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_dashboard_url" {
  description = "ECR repository URL for the dashboard image"
  value       = aws_ecr_repository.dashboard.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.main.name
}

output "app_url" {
  description = "Application URL (HTTPS on custom domain if set, otherwise HTTP on the ALB DNS name)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

output "domain_setup_note" {
  description = "Domain setup status / next steps"
  value = var.domain_name == "" ? (
    "No custom domain configured. Set domain_name in terraform.tfvars to enable HTTPS. "
    "A Route 53 hosted zone for the parent domain must exist before deploying with a domain name."
  ) : (
    "Domain: ${var.domain_name} — ACM certificate provisioned and DNS configured via Route 53. "
    "HTTPS is active on the ALB."
  )
}
