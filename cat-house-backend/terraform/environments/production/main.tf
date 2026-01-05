terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket  = "cat-house-terraform-state"
    key     = "production/terraform.tfstate"
    region  = "sa-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "production"
      ManagedBy   = "Terraform"
      Project     = "CatHouse"
    }
  }
}

module "infrastructure" {
  source = "../../modules/common"
  
  environment                = "production"
  aws_region                 = var.aws_region
  certificate_arn            = var.certificate_arn
  certificate_arn_cloudfront = var.certificate_arn_cloudfront
  domain_name                = var.domain_name
  app_prefix                 = var.app_prefix
  hosted_zone_id             = var.hosted_zone_id
  frontend_domain            = var.frontend_domain_production
  api_domain                 = var.api_domain_production
  alert_email                = var.alert_email
}
