
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

vpc_security_group_ids = []

identifier              = "my-rds-instance"
instance_class          = "db.t3.micro"
allocated_storage       = 20
engine                  = "mysql"
engine_version          = "8.0"
db_username             = "admin"
db_password             = "MySecurePassword123!"  # Replace with a strong password
db_name                 = "mydatabase"
publicly_accessible     = true
storage_type            = "gp2"
backup_retention_period = 0
skip_final_snapshot     = true
db_instance_name        = "MyRDSInstance"
