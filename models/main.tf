terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Data source para bucket existente
data "aws_s3_bucket" "cripto_data" {
  bucket = var.s3_bucket_name
}

# IAM Role para Glue
resource "aws_iam_role" "glue_role" {
  name = "cripto-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy para Glue
resource "aws_iam_role_policy" "glue_policy" {
  name = "cripto-glue-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.cripto_data.arn,
          "${data.aws_s3_bucket.cripto_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# IAM Role para Lambda (apenas para trigger)
resource "aws_iam_role" "lambda_role" {
  name = "cripto-lambda-role"

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

# IAM Policy para Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cripto-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${data.aws_s3_bucket.cripto_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun"
        ]
        Resource = [
          aws_glue_job.model_training.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Glue Job para Feature Engineering
resource "aws_glue_job" "feature_engineering" {
  name         = "cripto-feature-engineering"
  role_arn     = aws_iam_role.glue_role.arn
  worker_type  = "Standard"
  number_of_workers = 2
  timeout      = 30

  command {
    script_location = "s3://${data.aws_s3_bucket.cripto_data.bucket}/scripts/feature_engineering.py"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET_NAME" = data.aws_s3_bucket.cripto_data.bucket
    "--job-language" = "python"
    "--job-bookmark-option" = "job-bookmark-enable"
  }

  depends_on = [aws_iam_role_policy.glue_policy]
}

# Glue Job para Model Training
resource "aws_glue_job" "model_training" {
  name         = "cripto-model-training"
  role_arn     = aws_iam_role.glue_role.arn
  worker_type  = "Standard"
  number_of_workers = 2
  timeout      = 360

  command {
    script_location = "s3://${data.aws_s3_bucket.cripto_data.bucket}/scripts/train_models_glue_simple.py"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET_NAME" = data.aws_s3_bucket.cripto_data.bucket
    "--job-language" = "python"
    "--job-bookmark-option" = "job-bookmark-enable"
  }

  depends_on = [aws_iam_role_policy.glue_policy]
}

# Lambda para trigger do Glue Training
resource "aws_lambda_function" "glue_trigger" {
  filename         = data.archive_file.glue_trigger.output_path
  function_name    = "cripto-glue-trigger"
  role            = aws_iam_role.lambda_role.arn
  handler         = "glue_trigger.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      BUCKET = data.aws_s3_bucket.cripto_data.bucket
      GLUE_JOB_NAME = aws_glue_job.model_training.name
    }
  }
}

# Archive para Lambda trigger
data "archive_file" "glue_trigger" {
  type        = "zip"
  source_file = "glue_trigger.py"
  output_path = "glue_trigger.zip"
}

# Permissão para Lambda ser invocado pelo S3
resource "aws_lambda_permission" "glue_trigger" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.glue_trigger.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.cripto_data.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "feature_engineering" {
  name              = "/aws-glue/jobs/cripto-feature-engineering"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "model_training" {
  name              = "/aws-glue/jobs/cripto-model-training"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "glue_trigger" {
  name              = "/aws/lambda/cripto-glue-trigger"
  retention_in_days = 7
}

# S3 Notification para trigger do pipeline
resource "aws_s3_bucket_notification" "pipeline_triggers" {
  bucket = data.aws_s3_bucket.cripto_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.glue_trigger.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "cripto_features.csv"
  }
} 