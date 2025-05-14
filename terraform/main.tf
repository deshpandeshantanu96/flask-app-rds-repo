resource "random_password" "db" {
  length  = 16
  special = false # Avoid special chars if your DB doesn't support them
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "db_password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

resource "aws_db_instance" "free_tier" {
  identifier             = var.db_instance_identifier
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  engine                 = var.db_engine
  engine_version         = var.db_engine_version
  username               = var.db_username
  password               = random_password.db.result
  db_name                = var.db_name
  storage_type           = var.db_storage_type
  skip_final_snapshot    = var.db_skip_final_snapshot
  publicly_accessible    = var.db_publicly_accessible
  backup_retention_period = var.db_backup_retention_period
  vpc_security_group_ids = var.vpc_security_group_ids
  multi_az               = false # Free tier doesn't support Multi-AZ
  storage_encrypted      = false # Free tier has limitations on encryption

  # Free tier specific parameters
  license_model          = "general-public-license"
  parameter_group_name   = "default.mysql5.7"
  deletion_protection    = false

  # Enable performance insights (disabled for free tier as it may incur costs)
  performance_insights_enabled = false

  tags = {
    Name        = "Free Tier RDS"
    Environment = "Development"
    Terraform   = "true"
  }
}

# Create a default security group if none provided
resource "aws_security_group" "rds_sg" {
  count = length(var.vpc_security_group_ids) == 0 ? 1 : 0

  name        = "free-tier-rds-sg"
  description = "Security group for Free Tier RDS"

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict this in production!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "free-tier-rds-sg"
  }
}

# 5. IAM Policy for GitHub Actions OIDC
data "aws_iam_policy_document" "github_actions_rds" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
      "rds-db:connect"
    ]
    resources = [
      aws_secretsmanager_secret.rds_credentials.arn,
      "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:*/github-actions"
    ]
  }
}

resource "aws_iam_policy" "github_actions_rds" {
  name        = "GitHubActionsRDSAccess"
  description = "Allow GitHub Actions to fetch RDS secrets and connect"
  policy      = data.aws_iam_policy_document.github_actions_rds.json
}

# 6. OIDC Provider (if not already exists)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}