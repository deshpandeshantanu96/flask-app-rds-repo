resource "aws_iam_policy" "secretsmanager_policy" {
  name        = "AllowSecretsManagerAccess"
  description = "Allow Create, Put, and Get on Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:PutSecretValue",
          "secretsmanager:GetSecretValue"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_secretsmanager_policy" {
  user       = "git_terraform_project_user"
  policy_arn = aws_iam_policy.secretsmanager_policy.arn
}
