# Terraform PostgreSQL Module
# Handles PostgreSQL RDS setup with read replicas

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for RDS"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for RDS subnets"
  type        = list(string)
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 50
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "replica_instance_class" {
  description = "Read replica instance class"
  type        = string
  default     = "db.t3.small"
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period"
  type        = number
  default     = 7
}

variable "username" {
  description = "Master username"
  type        = string
  default     = "bankadmin"
}

variable "password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "security_group_ids" {
  description = "Security groups for RDS"
  type        = list(string)
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = true
}

variable "enable_read_replica" {
  description = "Create read replica"
  type        = bool
  default     = true
}

output "primary_endpoint" {
  description = "Primary database endpoint"
  value       = aws_db_instance.primary.address
  sensitive   = true
}

output "replica_endpoint" {
  description = "Read replica endpoint"
  value       = aws_db_instance.replica[0].address
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.primary.name
}

output "database_port" {
  description = "Database port"
  value       = aws_db_instance.primary.port
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet"
  }
}

resource "aws_db_instance" "primary" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine        = "postgres"
  engine_version = "15.3"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2
  storage_type         = "gp3"
  storage_encrypted    = var.storage_encrypted

  db_name  = "bankdb"
  username = var.username
  password = var.password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids

  multi_az               = var.multi_az
  availability_zone      = var.multi_az ? null : data.aws_availability_zones.available.names[0]
  publicly_accessible   = false

  backup_retention_period = var.backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  auto_minor_version_upgrade = true
  deletion_protection         = var.environment == "production" ? true : false
  final_snapshot_identifier    = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-final-snapshot"
  skip_final_snapshot         = var.skip_final_snapshot

  performance_insights_enabled = var.environment == "production" ? true : false

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
    Role        = "primary"
  }
}

# Read replica for analytics queries
resource "aws_db_instance" "replica" {
  count = var.enable_read_replica ? 1 : 0

  identifier     = "${var.project_name}-${var.environment}-db-replica"
  engine        = "postgres"
  engine_version = aws_db_instance.primary.engine_version
  instance_class = var.replica_instance_class

  publicly_accessible = false

  source_region          = data.aws_region.current.name
  source_db_instance_arn = aws_db_instance.primary.arn

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids

  backup_retention_period = 0
  deletion_protection     = false

  performance_insights_enabled = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-replica"
    Environment = var.environment
    Role        = "replica"
  }

  depends_on = [aws_db_instance.primary]
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_region" "current" {}
