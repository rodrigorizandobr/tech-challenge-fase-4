output "s3_bucket_name" {
  description = "Nome do bucket S3"
  value       = data.aws_s3_bucket.cripto_data.bucket
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = data.aws_s3_bucket.cripto_data.arn
}

output "glue_feature_engineering_job" {
  description = "Nome do Glue Job de Feature Engineering"
  value       = aws_glue_job.feature_engineering.name
}

output "glue_model_training_job" {
  description = "Nome do Glue Job de Model Training"
  value       = aws_glue_job.model_training.name
}

output "lambda_glue_trigger_arn" {
  description = "ARN da Lambda que triggera o Glue Training"
  value       = aws_lambda_function.glue_trigger.arn
}

output "glue_role_arn" {
  description = "ARN da role do Glue"
  value       = aws_iam_role.glue_role.arn
}

output "lambda_role_arn" {
  description = "ARN da role da Lambda"
  value       = aws_iam_role.lambda_role.arn
}

output "cloudwatch_log_groups" {
  description = "Grupos de logs do CloudWatch"
  value = {
    feature_engineering = aws_cloudwatch_log_group.feature_engineering.name
    model_training     = aws_cloudwatch_log_group.model_training.name
    glue_trigger       = aws_cloudwatch_log_group.glue_trigger.name
  }
} 