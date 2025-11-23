# Secrets Manager - Agora com refresh token
resource "aws_secretsmanager_secret" "spotify_credentials" {
  name = "spotify/api-credentials"
  description = "Credenciais OAuth da API do Spotify"

  tags = {
    Project     = "spotify-pipeline"
    Environment = "production"
  }
}

resource "aws_secretsmanager_secret_version" "initial_creds" {
  secret_id = aws_secretsmanager_secret.spotify_credentials.id
  secret_string = jsonencode({
    client_id     = var.spotify_client_id
    client_secret = var.spotify_client_secret
    redirect_uri  = var.spotify_redirect_uri
  })
}

# Adicionar policy para atualizar secrets (para refresh tokens)
resource "aws_iam_policy" "secrets_manager_update_policy" {
  name = "SpotifySecretsManagerUpdatePolicy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:UpdateSecret"
        ]
        Resource = [aws_secretsmanager_secret.spotify_credentials.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_update" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_manager_update_policy.arn
}