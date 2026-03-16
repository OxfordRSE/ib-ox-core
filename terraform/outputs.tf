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
  description = "Application URL (custom domain if set, otherwise the ALB DNS name)"
  value = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

output "domain_setup_instructions" {
  description = "Instructions for setting up the custom domain (only shown when domain_name is not configured)"
  value = var.domain_name == "" ? <<-MSG
    No custom domain configured. To add HTTPS with a custom domain:
    1. Note the ALB DNS name: ${aws_lb.main.dns_name}
    2. Request an ACM certificate in the AWS Console (DNS validation) for your domain.
    3. Create a Route 53 CNAME: <your-domain> → ${aws_lb.main.dns_name}
    4. Approve the ACM DNS validation record in Route 53.
    5. Re-deploy with: -var="domain_name=<your-domain>" -var="certificate_arn=<arn>"
  MSG
  : null
}
