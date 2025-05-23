variable "db_instance_identifier" {
  description = "The identifier for the RDS instance"
  type        = string
}

variable "db_name" {
  description = "The name of the database to create"
  type        = string
}

variable "db_username" {
  description = "Username for the master DB user"
  type        = string
}

variable "db_password" {
  description = "Password for the master DB user"
  type        = string
  sensitive   = true
}

variable "db_engine" {
  description = "The database engine to use"
  type        = string
}

variable "db_engine_version" {
  description = "The engine version to use"
  type        = string
}

variable "db_instance_class" {
  description = "The instance type of the RDS instance"
  type        = string
}

variable "db_allocated_storage" {
  description = "The allocated storage in gigabytes"
  type        = number
}

variable "db_storage_type" {
  description = "The storage type for the database"
  type        = string
}

variable "db_skip_final_snapshot" {
  description = "Determines whether a final DB snapshot is created"
  type        = bool
}

variable "db_publicly_accessible" {
  description = "Whether the DB instance should be publicly accessible"
  type        = bool
}

variable "db_backup_retention_period" {
  description = "The days to retain backups for"
  type        = number
}

#variable "vpc_security_group_ids" {
#  description = "List of VPC security groups to associate"
#  type        = list(string)
#}

variable "aws_region" {
  description = "Region"
  type        = string
}