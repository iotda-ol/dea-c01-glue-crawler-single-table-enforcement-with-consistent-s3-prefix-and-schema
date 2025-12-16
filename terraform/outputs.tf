# Outputs for AWS Glue Crawler Single Table Enforcement

output "s3_bucket_name" {
  description = "Name of the S3 bucket for data storage"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.data_lake.arn
}

output "s3_data_path" {
  description = "Full S3 path where data should be uploaded"
  value       = "s3://${aws_s3_bucket.data_lake.id}/${var.s3_data_prefix}/"
}

output "glue_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.main.name
}

output "glue_database_arn" {
  description = "ARN of the Glue catalog database"
  value       = aws_glue_catalog_database.main.arn
}

output "glue_crawler_name" {
  description = "Name of the Glue crawler"
  value       = aws_glue_crawler.single_table.name
}

output "glue_crawler_arn" {
  description = "ARN of the Glue crawler"
  value       = aws_glue_crawler.single_table.arn
}

output "glue_crawler_role_arn" {
  description = "ARN of the IAM role used by the Glue crawler"
  value       = aws_iam_role.glue_crawler.arn
}

output "aws_console_crawler_url" {
  description = "AWS Console URL to view the Glue crawler"
  value       = "https://${var.aws_region}.console.aws.amazon.com/glue/home?region=${var.aws_region}#/v2/data-catalog/crawlers/view/${aws_glue_crawler.single_table.name}"
}

output "aws_console_database_url" {
  description = "AWS Console URL to view the Glue database"
  value       = "https://${var.aws_region}.console.aws.amazon.com/glue/home?region=${var.aws_region}#/v2/data-catalog/databases/view/${aws_glue_catalog_database.main.name}"
}

output "configuration_summary" {
  description = "Summary of key configuration settings for single table enforcement"
  value = {
    s3_data_prefix            = var.s3_data_prefix
    schema_update_behavior    = var.schema_update_behavior
    schema_delete_behavior    = var.schema_delete_behavior
    table_similarity_threshold = var.table_similarity_threshold
    recrawl_behavior          = var.recrawl_behavior
  }
}
