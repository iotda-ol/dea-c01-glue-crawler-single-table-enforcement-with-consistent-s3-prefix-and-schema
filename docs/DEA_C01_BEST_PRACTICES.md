# DEA-C01 Best Practices for AWS Glue Crawlers

This document outlines best practices for AWS Glue Crawlers aligned with the AWS Certified Data Engineer - Associate (DEA-C01) exam objectives and AWS best practices.

## Table of Contents
1. [Data Cataloging Best Practices](#data-cataloging-best-practices)
2. [Schema Management](#schema-management)
3. [Performance Optimization](#performance-optimization)
4. [Security and Compliance](#security-and-compliance)
5. [Cost Optimization](#cost-optimization)
6. [Operational Excellence](#operational-excellence)
7. [Data Quality](#data-quality)

---

## Data Cataloging Best Practices

### 1. Use Consistent Naming Conventions

**Best Practice**: Establish and enforce naming standards for databases and tables.

```hcl
# Good naming pattern
resource "aws_glue_catalog_database" "main" {
  name = "${var.project_name}_${var.environment}_db"
  # Example: customer_data_prod_db
}
```

**Benefits**:
- Easy to identify resource purpose
- Simplifies multi-environment management
- Improves searchability

### 2. Organize Data by Access Patterns

**Best Practice**: Structure S3 prefixes based on how data will be queried, not how it arrives.

```
✅ Good (query-optimized):
s3://data-lake/orders/          # All order data together
s3://data-lake/customers/       # All customer data together

❌ Bad (source-optimized):
s3://data-lake/vendor-a/orders/
s3://data-lake/vendor-b/orders/
```

### 3. Single Table for Homogeneous Data

**Best Practice**: Configure crawlers to create one table per logical dataset.

```hcl
configuration = jsonencode({
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
    TableLevelConfiguration = {
      SimilarityThreshold = 0.8
    }
  }
})
```

**When to use**:
- Third-party data with consistent schema
- Time-series data from same source
- Log files with same structure

**When NOT to use**:
- Fundamentally different data types
- Incompatible schemas (e.g., orders vs. customers)

---

## Schema Management

### 1. Handle Schema Evolution Gracefully

**Best Practice**: Configure crawlers to handle schema changes without breaking existing queries.

```hcl
schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"  # Add new columns
  delete_behavior = "LOG"                  # Log but don't delete
}
```

**Configuration Options**:

| Setting | Update Behavior | When to Use |
|---------|----------------|-------------|
| UPDATE_IN_DATABASE | Auto-add new columns | Production (recommended) |
| LOG | Log changes only | Testing/validation |

| Setting | Delete Behavior | When to Use |
|---------|----------------|-------------|
| LOG | Log deletions | Production (safest) |
| DELETE_FROM_DATABASE | Remove columns | Dev/test only |
| DEPRECATE_IN_DATABASE | Mark as deprecated | Compliance requirements |

### 2. Version Control Schema Definitions

**Best Practice**: Maintain schema definitions in version control.

```python
# schema_definitions.py
TRANSACTION_SCHEMA = {
    "transaction_id": "string",
    "customer_id": "string",
    "amount": "decimal(10,2)",
    "transaction_date": "date",
    "status": "string"
}
```

**Benefits**:
- Track schema changes over time
- Enable schema validation before ingestion
- Support rollback if needed

### 3. Use Appropriate Data Types

**Best Practice**: Ensure correct data type mapping for efficient queries.

```python
# Correct type mapping
{
    "transaction_id": "string",      # Not int - may have leading zeros
    "amount": "decimal(10,2)",       # Not double - financial precision
    "quantity": "int",               # Not string - enable aggregations
    "transaction_date": "date",      # Not string - enable date operations
    "is_active": "boolean"           # Not string - enable boolean logic
}
```

---

## Performance Optimization

### 1. Use Appropriate Recrawl Policies

**Best Practice**: Choose recrawl behavior based on data arrival patterns.

```hcl
recrawl_policy {
  recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"  # Efficient for append-only
}
```

**Options**:
- **CRAWL_EVERYTHING**: Full scan every time
  - Use when: Files frequently modified
  - Cost: Higher DPU usage
  
- **CRAWL_NEW_FOLDERS_ONLY**: Incremental scan
  - Use when: Append-only data
  - Cost: Lower DPU usage (recommended)

### 2. Exclude Unnecessary Files

**Best Practice**: Configure exclusions to avoid scanning non-data files.

```hcl
s3_target {
  path = "s3://${aws_s3_bucket.data_lake.id}/data/"
  
  exclusions = [
    "**/_temporary/**",     # Spark temporary files
    "**/.spark/**",         # Spark metadata
    "**/_SUCCESS",          # Success markers
    "**/.metadata/**",      # Metadata files
    "**/*.log",             # Log files
    "**/._*"                # Hidden files
  ]
}
```

### 3. Optimize File Sizes

**Best Practice**: Use optimal file sizes for better crawler and query performance.

**Guidelines**:
- **Minimum**: 128 MB per file
- **Optimal**: 128 MB - 1 GB per file
- **Maximum**: Avoid files > 5 GB

**Too many small files**:
```
❌ Bad: 10,000 files of 1 MB each
✅ Good: 100 files of 100 MB each
```

**Implementation**:
```python
# Combine small files before upload
python combine_files.py --target-size 128MB
```

### 4. Use Columnar Formats for Analytics

**Best Practice**: Convert data to Parquet or ORC for analytical workloads.

```python
# Convert CSV to Parquet
import pandas as pd

df = pd.read_csv('data.csv')
df.to_parquet('data.parquet', 
              compression='snappy',
              engine='pyarrow')
```

**Benefits**:
- 80-90% storage reduction
- 10-100x faster queries
- Built-in compression
- Efficient column pruning

---

## Security and Compliance

### 1. Implement Least Privilege Access

**Best Practice**: Grant minimum necessary permissions to Glue crawler role.

```hcl
resource "aws_iam_role_policy" "glue_s3_access" {
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.data_lake.arn}",
          "${aws_s3_bucket.data_lake.arn}/third-party-data/*"  # Specific prefix only
        ]
      }
    ]
  })
}
```

**Avoid**:
```hcl
# ❌ Too permissive
Resource = ["*"]
Action = ["s3:*"]
```

### 2. Enable Encryption

**Best Practice**: Encrypt data at rest and in transit.

```hcl
# S3 encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # or "aws:kms" for KMS
    }
  }
}
```

**Catalog encryption**:
```hcl
resource "aws_glue_data_catalog_encryption_settings" "example" {
  data_catalog_encryption_settings {
    encryption_at_rest {
      catalog_encryption_mode = "SSE-KMS"
      sse_aws_kms_key_id     = aws_kms_key.glue.arn
    }
    
    connection_password_encryption {
      return_connection_password_encrypted = true
      aws_kms_key_id                      = aws_kms_key.glue.arn
    }
  }
}
```

### 3. Implement Data Classification

**Best Practice**: Tag resources with data classification levels.

```hcl
resource "aws_glue_catalog_database" "main" {
  name = "customer_data_db"
  
  tags = {
    DataClassification = "Sensitive"
    ComplianceScope    = "PCI-DSS"
    DataOwner          = "data-team@company.com"
  }
}
```

### 4. Enable Audit Logging

**Best Practice**: Enable CloudTrail and CloudWatch logging for compliance.

```hcl
# CloudWatch log group for crawler
resource "aws_cloudwatch_log_group" "crawler_logs" {
  name              = "/aws/glue/crawlers/${var.project_name}"
  retention_in_days = 90
  
  tags = {
    Purpose = "Audit and troubleshooting"
  }
}
```

---

## Cost Optimization

### 1. Schedule Crawlers Appropriately

**Best Practice**: Run crawlers only when data changes, not continuously.

```hcl
# Run daily at 2 AM UTC
schedule = "cron(0 2 * * ? *)"

# Or on-demand only
schedule = ""
```

**Cost Considerations**:
- Crawler: $0.44 per DPU-hour
- Catalog storage: Free for first 1M objects
- Avoid over-crawling unchanged data

### 2. Use Sample Sizes Effectively

**Best Practice**: Configure appropriate sample sizes for schema detection.

```hcl
configuration = jsonencode({
  Version = 1.0
  CrawlerOutput = {
    MaxSampleSize = 1  # Sample 1 MB per file (default: 1)
  }
})
```

**Guidelines**:
- Small files (< 10 MB): Sample all
- Large files (> 1 GB): Sample 1 MB sufficient
- Homogeneous data: Lower sample size OK

### 3. Consolidate Multiple Crawlers

**Best Practice**: Use one crawler for related datasets when possible.

```
✅ Good:
- crawler_transactions (covers all transaction types)

❌ Bad:
- crawler_online_transactions
- crawler_store_transactions  
- crawler_mobile_transactions
```

### 4. Clean Up Unused Tables

**Best Practice**: Implement lifecycle management for catalog metadata.

```python
# Delete unused tables
import boto3

glue = boto3.client('glue')

# List tables
response = glue.get_tables(DatabaseName='my_database')

for table in response['TableList']:
    # Check last accessed time
    if is_unused(table):
        glue.delete_table(
            DatabaseName='my_database',
            Name=table['Name']
        )
```

---

## Operational Excellence

### 1. Monitor Crawler Execution

**Best Practice**: Set up CloudWatch alarms for crawler failures.

```hcl
resource "aws_cloudwatch_metric_alarm" "crawler_failed" {
  alarm_name          = "glue-crawler-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.crawler.failureCount"
  namespace           = "AWS/Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alert when Glue crawler fails"
  
  dimensions = {
    CrawlerName = aws_glue_crawler.single_table.name
  }
}
```

### 2. Implement Retry Logic

**Best Practice**: Configure appropriate retry behavior for transient failures.

```python
# Retry crawler execution
import boto3
from botocore.exceptions import ClientError
import time

def run_crawler_with_retry(crawler_name, max_retries=3):
    glue = boto3.client('glue')
    
    for attempt in range(max_retries):
        try:
            response = glue.start_crawler(Name=crawler_name)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'CrawlerRunningException':
                print(f"Crawler already running, waiting...")
                time.sleep(60)
            else:
                if attempt == max_retries - 1:
                    raise
                time.sleep(30 * (attempt + 1))
```

### 3. Version Infrastructure as Code

**Best Practice**: Use Terraform state management and versioning.

```bash
# Use remote state
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "glue-crawler/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 4. Document Configuration Decisions

**Best Practice**: Maintain clear documentation of crawler configurations.

```markdown
# Configuration Rationale

## Similarity Threshold: 0.8
- Reason: Balances grouping vs. accuracy
- Tested: 2024-01-15
- Review: Quarterly

## Recrawl Behavior: CRAWL_NEW_FOLDERS_ONLY
- Reason: Append-only data pattern
- Cost savings: ~60% vs CRAWL_EVERYTHING
- Review: If data modification patterns change
```

---

## Data Quality

### 1. Validate Schema Before Crawling

**Best Practice**: Implement schema validation before data ingestion.

```python
def validate_schema(file_path, expected_schema):
    """Validate file schema matches expected schema."""
    import pandas as pd
    
    df = pd.read_csv(file_path, nrows=1)
    actual_columns = set(df.columns)
    expected_columns = set(expected_schema.keys())
    
    if actual_columns != expected_columns:
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns
        
        raise ValueError(
            f"Schema mismatch!\n"
            f"Missing columns: {missing}\n"
            f"Extra columns: {extra}"
        )
    
    return True
```

### 2. Handle Data Quality Issues

**Best Practice**: Configure crawler to handle common data quality problems.

```hcl
configuration = jsonencode({
  Version = 1.0
  CrawlerOutput = {
    # Handle inconsistent data types
    EnableTypeInference = true
    
    # Handle null values
    HandleNullValues = "IgnoreNulls"
    
    # Handle malformed records
    ErrorHandling = {
      Mode = "LOG"  # or "FAIL_FAST"
    }
  }
})
```

### 3. Implement Data Validation Rules

**Best Practice**: Use AWS Glue Data Quality (DQ) rules.

```python
# Example DQ rules
rules = """
Rules = [
    ColumnExists "transaction_id",
    ColumnExists "customer_id",
    ColumnExists "amount",
    ColumnValues "amount" > 0,
    ColumnValues "status" in ["completed", "pending", "cancelled"],
    Completeness "customer_id" >= 0.95,
    Uniqueness "transaction_id" >= 0.99
]
"""
```

---

## DEA-C01 Exam Tips

### Key Concepts for the Exam

1. **Glue Crawler Behavior**:
   - Understands how crawlers infer schema
   - Groups tables by location and format
   - Handles partitions automatically (Hive-style)

2. **Schema Change Policies**:
   - UPDATE_IN_DATABASE vs. LOG
   - DELETE_FROM_DATABASE vs. DEPRECATE_IN_DATABASE
   - Impact on existing queries

3. **Cost Optimization**:
   - DPU-hour pricing model
   - Recrawl policies for cost savings
   - Sample sizes and their impact

4. **Integration Points**:
   - Athena for querying
   - EMR for processing
   - Redshift Spectrum for analytics
   - Lake Formation for governance

5. **Security**:
   - IAM roles and policies
   - Encryption at rest and in transit
   - Resource-based policies
   - Data classification

### Common Exam Scenarios

**Scenario 1**: Multiple tables created unexpectedly
- **Solution**: Check S3 prefix consistency, file formats, and table grouping policy

**Scenario 2**: Schema changes breaking queries
- **Solution**: Use UPDATE_IN_DATABASE with MergeNewColumns

**Scenario 3**: High crawler costs
- **Solution**: Use CRAWL_NEW_FOLDERS_ONLY and appropriate scheduling

**Scenario 4**: Partitioning requirements
- **Solution**: Use Hive-style partitions (year=2024/month=01/)

**Scenario 5**: Data access control
- **Solution**: Implement Lake Formation permissions or S3 bucket policies

---

## Summary Checklist

### For Single Table Enforcement:
- [ ] Single S3 prefix for all files
- [ ] Consistent file format across all files
- [ ] Consistent compression type
- [ ] Compatible schema (allow for minor evolution)
- [ ] CombineCompatibleSchemas enabled
- [ ] Similarity threshold set (0.8 recommended)
- [ ] MergeNewColumns configured
- [ ] Appropriate exclusion patterns

### For Production Readiness:
- [ ] Encryption enabled (S3 and catalog)
- [ ] Least privilege IAM policies
- [ ] CloudWatch monitoring configured
- [ ] Cost optimization settings applied
- [ ] Documentation complete
- [ ] Testing performed with sample data
- [ ] Backup/disaster recovery plan
- [ ] Change management process

### For DEA-C01 Success:
- [ ] Understand crawler configuration options
- [ ] Know schema change policy impacts
- [ ] Familiar with cost optimization techniques
- [ ] Understand security best practices
- [ ] Know integration points (Athena, EMR, etc.)
- [ ] Practice with real scenarios
- [ ] Review AWS documentation
- [ ] Understand troubleshooting approaches
