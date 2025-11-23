variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "spotify_client_id" {
  description = "Spotify App Client ID"
  type        = string
  sensitive   = true
}

variable "spotify_client_secret" {
  description = "Spotify App Client Secret"
  type        = string
  sensitive   = true
}

variable "spotify_redirect_uri" {
  description = "Spotify App Redirect URI"
  type        = string
  default     = "http://127.0.0.1:8000/callback"
}

variable "lambda_zip_path" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = " /spotify_extractor.zip"
}