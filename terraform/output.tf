output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.free_tier.endpoint
}

output "rds_username" {
  description = "The master username for the RDS instance"
  value       = aws_db_instance.free_tier.username
  sensitive   = true
}

output "rds_db_name" {
  description = "The name of the database"
  value       = aws_db_instance.free_tory.db_name
}

output "rds_instance_id" {
  description = "The ID of the RDS instance"
  value       = aws_db_instance.free_tier.id
}

output "rds_arn" {
  description = "The ARN of the RDS instance"
  value       = aws_db_instance.free_tier.arn
}