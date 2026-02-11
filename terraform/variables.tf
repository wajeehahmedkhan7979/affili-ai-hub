variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (staging/production)"
  default     = "production"
}

variable "app_count" {
  description = "Number of docker containers to run"
  default     = 2
}

variable "ecr_repository_url" {
  description = "ECR Repository URL"
}

variable "db_username" {
  description = "Database master username"
  default     = "affili_admin"
}

variable "db_password" {
  description = "Database master password"
  sensitive   = true
}
