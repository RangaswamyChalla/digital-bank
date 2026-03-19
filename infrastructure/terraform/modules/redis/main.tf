# Terraform Redis Module
# Handles Redis ElastiCache setup for caching and pub/sub

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for ElastiCache"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ElastiCache"
  type        = list(string)
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "security_group_ids" {
  description = "Security groups for ElastiCache"
  type        = list(string)
}

variable "at_rest_encryption_enabled" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Enable TLS encryption"
  type        = bool
  default     = false
}

variable "automatic_failover_enabled" {
  description = "Enable automatic failover (requires cluster mode)"
  type        = bool
  default     = false
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:${var.port}"
}

output "redis_endpoint" {
  description = "Redis endpoint address"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port"
  value       = var.port
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-redis-subnet"
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_security_group" "main" {
  name                 = "${var.project_name}-${var.environment}-redis-sg"
  description          = "Security group for ElastiCache Redis"
  ingress {
    from_port       = var.port
    to_port         = var.port
    protocol        = "tcp"
    security_groups = var.security_group_ids
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-sg"
  }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine              = "redis"
  engine_version      = var.engine_version
  node_type           = var.node_type
  num_cache_nodes     = var.num_cache_nodes
  port                = var.port
  parameter_group_name = "default.redis7"
  security_group_ids  = [aws_elasticache_security_group.main.id]
  subnet_group_name   = aws_elasticache_subnet_group.main.name

  snapshot_retention_limit   = var.environment == "production" ? 7 : 0
  snapshot_window           = "03:00-05:00"
  maintenance_window       = "mon:05:00-mon:07:00"

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token_enabled        = var.transit_encryption_enabled

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis"
    Environment = var.environment
  }
}
