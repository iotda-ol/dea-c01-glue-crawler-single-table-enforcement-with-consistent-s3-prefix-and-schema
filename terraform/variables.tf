# Variables for AWS Glue Crawler Single Table Enforcement

variable "aws_region" {
  description = "AWS region for deploying resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "glue-single-table"
}

variable "s3_data_prefix" {
  description = "S3 prefix for data files - MUST be consistent to enforce single table"
  type        = string
  default     = "third-party-data"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.s3_data_prefix))
    error_message = "S3 prefix must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "crawler_exclusions" {
  description = "Patterns to exclude from crawler (e.g., temporary files, metadata)"
  type        = list(string)
  default = [
    "**/_temporary/**",
    "**/.spark/**",
    "**/_SUCCESS",
    "**/.metadata/**"
  ]
}

variable "schema_delete_behavior" {
  description = "How to handle deleted columns in schema (LOG, DELETE_FROM_DATABASE, DEPRECATE_IN_DATABASE)"
  type        = string
  default     = "LOG"
  
  validation {
    condition     = contains(["LOG", "DELETE_FROM_DATABASE", "DEPRECATE_IN_DATABASE"], var.schema_delete_behavior)
    error_message = "Must be one of: LOG, DELETE_FROM_DATABASE, DEPRECATE_IN_DATABASE."
  }
}

variable "schema_update_behavior" {
  description = "How to handle new columns in schema (LOG, UPDATE_IN_DATABASE)"
  type        = string
  default     = "UPDATE_IN_DATABASE"
  
  validation {
    condition     = contains(["LOG", "UPDATE_IN_DATABASE"], var.schema_update_behavior)
    error_message = "Must be one of: LOG, UPDATE_IN_DATABASE."
  }
}

variable "recrawl_behavior" {
  description = "When to recrawl data (CRAWL_EVERYTHING, CRAWL_NEW_FOLDERS_ONLY)"
  type        = string
  default     = "CRAWL_NEW_FOLDERS_ONLY"
  
  validation {
    condition     = contains(["CRAWL_EVERYTHING", "CRAWL_NEW_FOLDERS_ONLY"], var.recrawl_behavior)
    error_message = "Must be one of: CRAWL_EVERYTHING, CRAWL_NEW_FOLDERS_ONLY."
  }
}

variable "table_similarity_threshold" {
  description = "Similarity threshold for combining schemas (0.0-1.0). Lower = more aggressive grouping"
  type        = number
  default     = 0.8
  
  validation {
    condition     = var.table_similarity_threshold >= 0.0 && var.table_similarity_threshold <= 1.0
    error_message = "Similarity threshold must be between 0.0 and 1.0."
  }
}

variable "crawler_schedule" {
  description = "Cron expression for crawler schedule (e.g., 'cron(0 1 * * ? *)' for daily at 1 AM UTC). Leave empty for on-demand only."
  type        = string
  default     = ""
}
