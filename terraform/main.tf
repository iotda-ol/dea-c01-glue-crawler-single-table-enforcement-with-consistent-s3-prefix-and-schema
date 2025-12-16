# AWS Glue Crawler Single Table Enforcement Solution
# This configuration demonstrates best practices for ensuring a Glue crawler
# creates a single table from third-party data in S3

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

  default_tags {
    tags = {
      Project     = "glue-crawler-single-table"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# S3 Bucket for third-party data
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "Data Lake Bucket"
    Description = "Storage for third-party data with consistent schema"
  }
}

# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create consistent S3 prefix structure
# This structure is critical for single table enforcement
resource "aws_s3_object" "data_prefix" {
  bucket       = aws_s3_bucket.data_lake.id
  key          = "${var.s3_data_prefix}/"
  content_type = "application/x-directory"
}

# Glue Database
resource "aws_glue_catalog_database" "main" {
  name        = "${var.project_name}_${var.environment}_db"
  description = "Glue database for third-party data catalog"

  tags = {
    Name = "Main Data Catalog Database"
  }
}

# IAM Role for Glue Crawler
resource "aws_iam_role" "glue_crawler" {
  name = "${var.project_name}-${var.environment}-glue-crawler-role"

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

  tags = {
    Name = "Glue Crawler Service Role"
  }
}

# Attach AWS managed policy for Glue service
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom policy for S3 access
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "${var.project_name}-${var.environment}-glue-s3-policy"
  role = aws_iam_role.glue_crawler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })
}

# Glue Crawler with Single Table Enforcement Configuration
resource "aws_glue_crawler" "single_table" {
  name          = "${var.project_name}-${var.environment}-crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.main.name
  description   = "Crawler configured to enforce single table creation from third-party data"

  # Target the specific S3 prefix for consistent data location
  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.id}/${var.s3_data_prefix}/"
    
    # Exclusions to avoid scanning non-data files
    exclusions = var.crawler_exclusions
  }

  # Schema change policy - critical for maintaining single table
  schema_change_policy {
    delete_behavior = var.schema_delete_behavior
    update_behavior = var.schema_update_behavior
  }

  # Recrawl policy - prevents unnecessary re-crawls
  recrawl_policy {
    recrawl_behavior = var.recrawl_behavior
  }

  # Configuration to prevent multiple table creation
  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      # Partition structure - keep flat to avoid table splits
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
      # Table grouping - CRITICAL for single table enforcement
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
    }
    # Grouping settings to treat all data as single dataset
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
      # Similarity threshold to group tables (0.0-1.0)
      # Higher value means stricter matching, lower means more grouping
      TableLevelConfiguration = {
        SimilarityThreshold = var.table_similarity_threshold
      }
    }
  })

  # Schedule (optional) - can be set via variable
  schedule = var.crawler_schedule

  tags = {
    Name        = "Single Table Enforcement Crawler"
    Description = "Configured to create one table regardless of file count"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
