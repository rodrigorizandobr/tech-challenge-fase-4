output "s3_bucket_name" {
  description = "Nome do bucket S3"
  value       = aws_s3_bucket.binance_data.bucket
}

output "lambda_function_name" {
  description = "Nome da função Lambda"
  value       = aws_lambda_function.binance_crawler.function_name
}

output "lambda_function_arn" {
  description = "ARN da função Lambda"
  value       = aws_lambda_function.binance_crawler.arn
}

output "cloudwatch_log_group" {
  description = "Nome do grupo de logs do CloudWatch"
  value       = aws_cloudwatch_log_group.lambda_log_group.name
}

output "eventbridge_rule_arn" {
  description = "ARN da regra do EventBridge"
  value       = aws_cloudwatch_event_rule.binance_crawler_schedule.arn
} 