terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Bucket para armazenar os dados dos ativos
resource "aws_s3_bucket" "binance_data" {
  bucket = "criptos-data"

  tags = {
    Environment = "production"
    Project     = "binance-crawler"
  }
}

# Configuração de versionamento do S3
resource "aws_s3_bucket_versioning" "binance_data_versioning" {
  bucket = aws_s3_bucket.binance_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Configuração de lifecycle do S3
resource "aws_s3_bucket_lifecycle_configuration" "binance_data_lifecycle" {
  bucket = aws_s3_bucket.binance_data.id

  rule {
    id     = "archive_old_data"
    status = "Enabled"
    
    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# Política de bucket para acesso público de leitura (opcional)
resource "aws_s3_bucket_public_access_block" "binance_data_public_access" {
  bucket = aws_s3_bucket.binance_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role para o Lambda
resource "aws_iam_role" "lambda_role" {
  name = "binance-crawler-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy para o Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "binance-crawler-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.binance_data.arn,
          "${aws_s3_bucket.binance_data.arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/binance-crawler"
  retention_in_days = 14
}

# Lambda Function
resource "aws_lambda_function" "binance_crawler" {
  filename         = "../lambda/binance-crawler.zip"
  function_name    = "binance-crawler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "nodejs18.x"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.binance_data.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_log_group
  ]
}

# EventBridge para agendar execução da Lambda
resource "aws_cloudwatch_event_rule" "binance_crawler_schedule" {
  name                = "binance-crawler-schedule"
  description         = "Agenda execução do crawler às 2h e 19h"
  schedule_expression = "cron(0 2,19 * * ? *)"  # 2h e 19h todos os dias
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.binance_crawler_schedule.name
  target_id = "BinanceCrawlerTarget"
  arn       = aws_lambda_function.binance_crawler.arn
}

# Lambda Permission para EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.binance_crawler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.binance_crawler_schedule.arn
}

 