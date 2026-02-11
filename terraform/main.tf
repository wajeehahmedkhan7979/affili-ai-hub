terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "affili-ai-terraform-state"
    key    = "prod/main.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AFFILI-AI-HUB"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "affili-ai-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"] # App & DB
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"] # ALB & NAT

  enable_nat_gateway = true
  single_nat_gateway = true # Save costs in non-prod, use false for high-availability

  tags = {
    Terraform = "true"
    Environment = var.environment
  }
}
