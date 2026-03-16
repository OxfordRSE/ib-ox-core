locals {
  project_name = "ib-ox"

  tags = {
    Project      = var.app_name
    project-name = local.project_name
    ManagedBy    = "terraform"
    Environment  = "production"
  }
}
