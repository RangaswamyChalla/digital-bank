# Production Environment Terraform Configuration
# Deploys the Digital Bank application to AWS production environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "digital-bank-terraform-state-prod"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    # Enable state encryption and versioning
    encrypt = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "digital-bank"
      Environment = "production"
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
  description = "Domain name for production"
  type        = string
  default     = "digitalbank.example.com"
}

#==============================================================================
# Network Configuration
#==============================================================================
variable "vpc_id" {
  description = "VPC ID for production"
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

#==============================================================================
# Secret Configuration (use AWS Secrets Manager in production)
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
# Module: PostgreSQL with Read Replica (Production - Multi-AZ)
#==============================================================================
module "postgres" {
  source = "../../modules/postgres"

  environment = "production"
  project_name = "digital-bank"

  vpc_id           = var.vpc_id
  subnet_ids       = var.private_subnet_ids
  security_group_ids = [module.postgres_security_group.id]

  allocated_storage   = 100
  instance_class      = "db.r6g.large"
  replica_instance_class = "db.r6g.medium"
  multi_az           = true
  storage_encrypted  = true
  backup_retention_days = 30

  username = var.db_username
  password = var.db_password

  enable_read_replica = true
}

module "postgres_security_group" {
  source = "terraform-aws-security-group//modules/postgres"

  name        = "digital-bank-prod-postgres"
  description = "Security group for PostgreSQL"
  vpc_id      = var.vpc_id

  egress_rules = ["all-all"]
}

#==============================================================================
# Module: Redis (Production - with clustering)
#==============================================================================
module "redis" {
  source = "../../modules/redis"

  environment = "production"
  project_name = "digital-bank"

  vpc_id           = var.vpc_id
  subnet_ids       = var.private_subnet_ids
  security_group_ids = [module.redis_security_group.id]

  node_type           = "cache.r6g.large"
  num_cache_nodes     = 2
  engine_version      = "7.0"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = true
}

module "redis_security_group" {
  source = "terraform-aws-security-group//modules/redis-elasticache"

  name        = "digital-bank-prod-redis"
  description = "Security group for Redis"
  vpc_id      = var.vpc_id

  egress_rules = ["all-all"]
}

#==============================================================================
# Module: Backend (ECS Fargate - Production)
#==============================================================================
module "backend" {
  source = "../../modules/backend"

  environment = "production"
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

  desired_count = 4  # Higher count for production
}

#==============================================================================
# Module: Frontend (S3 + CloudFront - Production)
#==============================================================================
module "frontend" {
  source = "../../modules/frontend"

  environment = "production"
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

output "database_replica_endpoint" {
  description = "Database read replica endpoint"
  value       = module.postgres.replica_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
}
