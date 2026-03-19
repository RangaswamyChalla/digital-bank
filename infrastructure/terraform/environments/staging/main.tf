# Staging Environment Terraform Configuration
# Deploys the Digital Bank application to AWS staging environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "digital-bank-terraform-state-staging"
    key    = "staging/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "digital-bank"
      Environment = "staging"
      ManagedBy   = "terraform"
    }
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for staging"
  type        = string
  default     = "staging.digitalbank.example.com"
}

#==============================================================================
# Network Configuration (assumes VPC module or existing VPC)
#==============================================================================
variable "vpc_id" {
  description = "VPC ID for staging"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for backend services"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for load balancers"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for backend"
  type        = list(string)
}

#==============================================================================
# Database Configuration
#==============================================================================
variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "bankadmin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

#==============================================================================
# Application Configuration
#==============================================================================
variable "backend_image" {
  description = "Docker image for backend"
  type        = string
  default     = "ghcr.io/digital-bank/backend:latest"
}

variable "frontend_build_path" {
  description = "Path to frontend build directory"
  type        = string
  default     = "../frontend/dist"
}

#==============================================================================
# Secret Configuration
#==============================================================================
variable "secret_key" {
  description = "JWT SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
  sensitive   = true
}

variable "otlp_endpoint" {
  description = "OpenTelemetry collector endpoint"
  type        = string
  default     = ""
}

#==============================================================================
# Module: PostgreSQL with Read Replica
#==============================================================================
module "postgres" {
  source = "../../modules/postgres"

  environment = "staging"
  project_name = "digital-bank"

  vpc_id           = var.vpc_id
  subnet_ids       = var.private_subnet_ids
  security_group_ids = [module.postgres_security_group.id]

  allocated_storage   = 50
  instance_class      = "db.t3.medium"
  replica_instance_class = "db.t3.small"
  multi_az           = false
  storage_encrypted  = true
  backup_retention_days = 7

  username = var.db_username
  password = var.db_password

  enable_read_replica = true
}

module "postgres_security_group" {
  source = "terraform-aws-security-group//modules/postgres"

  name        = "digital-bank-staging-postgres"
  description = "Security group for PostgreSQL"
  vpc_id      = var.vpc_id

  egress_rules = ["all-all"]
}

#==============================================================================
# Module: Redis
#==============================================================================
module "redis" {
  source = "../../modules/redis"

  environment = "staging"
  project_name = "digital-bank"

  vpc_id           = var.vpc_id
  subnet_ids       = var.private_subnet_ids
  security_group_ids = [module.redis_security_group.id]

  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  engine_version      = "7.0"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false
}

module "redis_security_group" {
  source = "terraform-aws-security-group//modules/redis-elasticache"

  name        = "digital-bank-staging-redis"
  description = "Security group for Redis"
  vpc_id      = var.vpc_id

  egress_rules = ["all-all"]
}

#==============================================================================
# Module: Backend (ECS Fargate)
#==============================================================================
module "backend" {
  source = "../../modules/backend"

  environment = "staging"
  project_name = "digital-bank"

  vpc_id           = var.vpc_id
  subnet_ids       = var.private_subnet_ids
  security_groups = var.security_group_ids

  container_image = var.backend_image

  database_url = "postgresql://${var.db_username}:${var.db_password}@${module.postgres.primary_endpoint}:5432/bankdb"
  redis_url    = "redis://${module.redis.redis_endpoint}:6379"

  secret_key    = var.secret_key
  sentry_dsn    = var.sentry_dsn
  otlp_endpoint = var.otlp_endpoint

  desired_count = 2
}

#==============================================================================
# Module: Frontend (S3 + CloudFront)
#==============================================================================
module "frontend" {
  source = "../../modules/frontend"

  environment = "staging"
  project_name = "digital-bank"

  backend_url   = "https://${module.backend.backend_url}"
  domain_name   = var.domain_name

  enable_cdn = true
}

#==============================================================================
# Outputs
#==============================================================================
output "backend_url" {
  description = "Backend API URL"
  value       = module.backend.backend_url
}

output "frontend_url" {
  description = "Frontend URL"
  value       = module.frontend.frontend_url
}

output "database_endpoint" {
  description = "Database primary endpoint"
  value       = module.postgres.primary_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
}
