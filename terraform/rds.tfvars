
# db_instance_identifier     = "prod-db-instance"
# db_name                   = "production_db"
# db_username               = "admin"
# db_engine                 = "mysql"
# db_engine_version         = "8.0"
# db_instance_class         = "db.t3.micro"
# db_allocated_storage      = 20
# db_storage_type           = "gp2"
# db_skip_final_snapshot    = false
# db_publicly_accessible    = false
# db_backup_retention_period = 7

# vpc_security_group_ids = []

db_instance_identifier     = "my-rds-instance"
db_name                    = "mydatabase"
db_username                = "admin"
# db_password                = "MySecurePassword123!"  # Use secrets in real usage
db_engine                  = "mysql"
db_engine_version          = "8.0"
db_instance_class          = "db.t3.micro"
db_allocated_storage       = 20
db_storage_type            = "gp2"
db_skip_final_snapshot     = true
db_publicly_accessible     = true
db_backup_retention_period = 0
# vpc_security_group_ids     = ["sg-0123456789abcdef0"]
aws_region                 = "us-east-1"

