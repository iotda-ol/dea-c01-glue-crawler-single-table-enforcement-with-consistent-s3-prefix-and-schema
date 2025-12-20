# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the AWS Glue crawler single table enforcement solution.

## Table of Contents
1. [Multiple Tables Created](#multiple-tables-created)
2. [Crawler Fails to Run](#crawler-fails-to-run)
3. [Schema Detection Issues](#schema-detection-issues)
4. [Performance Problems](#performance-problems)
5. [Data Not Appearing in Table](#data-not-appearing-in-table)
6. [Terraform Deployment Issues](#terraform-deployment-issues)
7. [Python Script Errors](#python-script-errors)

---

## Multiple Tables Created

### Symptom
Crawler creates multiple tables instead of one.

### Diagnosis

```bash
# Check how many tables were created
aws glue get-tables --database-name $DB_NAME | jq '.TableList | length'

# List all table names
aws glue get-tables --database-name $DB_NAME | jq '.TableList[].Name'
```

### Root Causes and Solutions

#### 1. Different S3 Prefixes

**Check**:
```bash
aws glue get-tables --database-name $DB_NAME | \
  jq '.TableList[] | {name: .Name, location: .StorageDescriptor.Location}'
```

**Fix**: Ensure all files are under the same prefix
```bash
# Move files to consistent prefix
aws s3 sync s3://$BUCKET_NAME/wrong-prefix/ s3://$BUCKET_NAME/third-party-data/
aws s3 rm s3://$BUCKET_NAME/wrong-prefix/ --recursive
```

#### 2. Different File Formats

**Check**:
```bash
aws glue get-tables --database-name $DB_NAME | \
  jq '.TableList[] | {name: .Name, format: .StorageDescriptor.InputFormat}'
```

**Fix**: Regenerate data with consistent format
```bash
python generate_sample_data.py --format csv --num-files 5
```

#### 3. Different Compression

**Check**:
```bash
aws s3 ls s3://$BUCKET_NAME/third-party-data/ | \
  awk '{print $4}' | sed 's/.*\.//' | sort | uniq
```

**Fix**: Ensure consistent compression
```bash
# Regenerate with consistent compression
python generate_sample_data.py --format csv --compression gzip --num-files 5
```

#### 4. Table Grouping Not Configured

**Check**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | \
  jq '.Crawler.Configuration'
```

**Fix**: Update crawler configuration
```hcl
# In terraform/main.tf
configuration = jsonencode({
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
  }
})
```

Apply changes:
```bash
terraform apply
```

### Recovery Steps

**Option 1: Delete and Re-run**
```bash
# Delete all tables
for table in $(aws glue get-tables --database-name $DB_NAME | jq -r '.TableList[].Name'); do
  aws glue delete-table --database-name $DB_NAME --name $table
done

# Re-run crawler
aws glue start-crawler --name $CRAWLER_NAME
```

**Option 2: Manual Merge** (not recommended)
```bash
# Keep one table, manually add data from others
# Complex - better to re-run crawler with correct configuration
```

---

## Crawler Fails to Run

### Symptom
Crawler shows `FAILED` state or doesn't start.

### Diagnosis

```bash
# Check crawler state
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.State'

# Check last error
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.LastCrawl.ErrorMessage'

# Check CloudWatch logs
aws logs tail /aws-glue/crawlers/$CRAWLER_NAME --follow
```

### Common Errors

#### 1. Access Denied to S3

**Error**: `Access Denied` or `Insufficient permissions`

**Check IAM permissions**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.Role'

# Check role policies
ROLE_NAME=$(aws glue get-crawler --name $CRAWLER_NAME | jq -r '.Crawler.Role' | cut -d'/' -f2)
aws iam list-role-policies --role-name $ROLE_NAME
aws iam list-attached-role-policies --role-name $ROLE_NAME
```

**Fix**: Ensure role has S3 read permissions
```bash
# Check in terraform/main.tf
# Verify aws_iam_role_policy includes S3 GetObject and ListBucket
terraform apply
```

#### 2. Crawler Already Running

**Error**: `CrawlerRunningException`

**Check**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.State'
```

**Fix**: Wait for completion or stop crawler
```bash
# Stop the crawler
aws glue stop-crawler --name $CRAWLER_NAME

# Wait a moment, then restart
sleep 10
aws glue start-crawler --name $CRAWLER_NAME
```

#### 3. No Data Found

**Error**: `No files found` or `Empty result`

**Check S3 contents**:
```bash
aws s3 ls s3://$BUCKET_NAME/third-party-data/
```

**Fix**: Upload data files
```bash
python upload_to_s3.py --bucket $BUCKET_NAME --prefix third-party-data
```

#### 4. Invalid Configuration

**Error**: `Invalid crawler configuration`

**Check configuration**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.Configuration'
```

**Fix**: Validate JSON configuration
```bash
# In terraform, ensure configuration is valid JSON
terraform validate
terraform apply
```

---

## Schema Detection Issues

### Symptom
Incorrect data types or missing columns in detected schema.

### Diagnosis

```bash
# View detected schema
aws glue get-table --database-name $DB_NAME --name third_party_data | \
  jq '.Table.StorageDescriptor.Columns'
```

### Common Issues

#### 1. Wrong Data Types

**Example**: Numbers detected as strings

**Check sample data**:
```bash
# Download a sample file
aws s3 cp s3://$BUCKET_NAME/third-party-data/sample_data_001.csv.gz /tmp/
gunzip /tmp/sample_data_001.csv.gz
head -n 5 /tmp/sample_data_001.csv
```

**Fix**: Ensure data is properly formatted
```python
# In generate_sample_data.py
# Ensure numeric values don't have quotes
{
    "quantity": 10,           # ✅ Correct
    "unit_price": 99.99,      # ✅ Correct
    "status": "completed"     # ✅ Correct (string)
}
```

#### 2. Missing Columns

**Check if schema evolved**:
```bash
# Compare files
aws s3 cp s3://$BUCKET_NAME/third-party-data/sample_data_001.csv.gz - | \
  gunzip | head -n 1

aws s3 cp s3://$BUCKET_NAME/third-party-data/sample_data_002.csv.gz - | \
  gunzip | head -n 1
```

**Fix**: Ensure consistent schema
```bash
# Regenerate all files with same schema
python generate_sample_data.py --format csv --num-files 5
python upload_to_s3.py --bucket $BUCKET_NAME --prefix third-party-data

# Re-run crawler
aws glue start-crawler --name $CRAWLER_NAME
```

#### 3. Schema Not Updating

**Check schema change policy**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | \
  jq '.Crawler.SchemaChangePolicy'
```

**Expected**:
```json
{
  "UpdateBehavior": "UPDATE_IN_DATABASE",
  "DeleteBehavior": "LOG"
}
```

**Fix**: Update configuration
```hcl
# In terraform/main.tf
schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"
  delete_behavior = "LOG"
}
```

---

## Performance Problems

### Symptom
Crawler takes too long or times out.

### Diagnosis

```bash
# Check crawler runtime
aws glue get-crawler --name $CRAWLER_NAME | \
  jq '.Crawler.LastCrawl.DurationInSeconds'

# Check number of files
aws s3 ls s3://$BUCKET_NAME/third-party-data/ --recursive | wc -l
```

### Solutions

#### 1. Too Many Small Files

**Check file sizes**:
```bash
aws s3 ls s3://$BUCKET_NAME/third-party-data/ --recursive --human-readable
```

**Fix**: Combine small files
```python
# Create fewer, larger files
python generate_sample_data.py \
  --format csv \
  --num-files 10 \
  --records-per-file 10000
```

**Guideline**: Aim for 128MB - 1GB per file

#### 2. Unnecessary Recrawling

**Check recrawl policy**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | \
  jq '.Crawler.RecrawlPolicy'
```

**Fix**: Use incremental crawling
```hcl
recrawl_policy {
  recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
}
```

#### 3. Scanning Unnecessary Files

**Check exclusions**:
```bash
aws glue get-crawler --name $CRAWLER_NAME | \
  jq '.Crawler.Targets.S3Targets[].Exclusions'
```

**Fix**: Add exclusion patterns
```hcl
exclusions = [
  "**/_temporary/**",
  "**/.spark/**",
  "**/_SUCCESS",
  "**/*.log"
]
```

---

## Data Not Appearing in Table

### Symptom
Table created but appears empty or missing data.

### Diagnosis

```bash
# Check table location
aws glue get-table --database-name $DB_NAME --name third_party_data | \
  jq '.Table.StorageDescriptor.Location'

# List files at that location
LOCATION=$(aws glue get-table --database-name $DB_NAME --name third_party_data | \
  jq -r '.Table.StorageDescriptor.Location')
aws s3 ls $LOCATION
```

### Solutions

#### 1. Wrong S3 Location

**Check mismatch**:
```bash
# Expected location
echo "s3://$BUCKET_NAME/third-party-data/"

# Actual table location
aws glue get-table --database-name $DB_NAME --name third_party_data | \
  jq -r '.Table.StorageDescriptor.Location'
```

**Fix**: Delete table and re-run crawler with correct target
```bash
aws glue delete-table --database-name $DB_NAME --name third_party_data
aws glue start-crawler --name $CRAWLER_NAME
```

#### 2. File Format Mismatch

**Check table format**:
```bash
aws glue get-table --database-name $DB_NAME --name third_party_data | \
  jq '.Table.StorageDescriptor.InputFormat'
```

**Check actual files**:
```bash
aws s3 ls s3://$BUCKET_NAME/third-party-data/ | head -5
```

**Fix**: Ensure format matches
```bash
# If table expects CSV but files are JSON, regenerate:
python generate_sample_data.py --format csv --num-files 5
python upload_to_s3.py --bucket $BUCKET_NAME --prefix third-party-data
```

#### 3. Empty Files

**Check file sizes**:
```bash
aws s3 ls s3://$BUCKET_NAME/third-party-data/ --recursive --summarize
```

**Fix**: Regenerate with content
```bash
python generate_sample_data.py \
  --format csv \
  --num-files 5 \
  --records-per-file 100
```

---

## Terraform Deployment Issues

### Issue 1: State Lock Error

**Error**: `Error acquiring the state lock`

**Fix**:
```bash
# If no other Terraform operation is running
terraform force-unlock <LOCK_ID>

# Or remove local state lock
rm .terraform.tfstate.lock.info
```

### Issue 2: Resource Already Exists

**Error**: `AlreadyExists` or `Duplicate resource`

**Options**:

**Option A: Import existing resource**
```bash
# Import S3 bucket
terraform import aws_s3_bucket.data_lake existing-bucket-name

# Import Glue database
terraform import aws_glue_catalog_database.main existing-db-name
```

**Option B: Use different names**
```hcl
# In terraform.tfvars
project_name = "glue-single-table-v2"
```

### Issue 3: Terraform Destroy Fails

**Error**: `BucketNotEmpty`

**Fix**:
```bash
# Empty bucket first
aws s3 rm s3://$BUCKET_NAME --recursive

# Then destroy
terraform destroy
```

### Issue 4: Provider Version Conflict

**Error**: `Provider version constraint not met`

**Fix**:
```bash
# Update provider
terraform init -upgrade

# Or specify version in versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

---

## Python Script Errors

### Issue 1: boto3 Not Found

**Error**: `ModuleNotFoundError: No module named 'boto3'`

**Fix**:
```bash
pip install boto3
# or
pip install -r python/requirements.txt
```

### Issue 2: Access Denied

**Error**: `botocore.exceptions.ClientError: ... Access Denied`

**Fix**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Configure if needed
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### Issue 3: Pandas Not Installed

**Error**: `ModuleNotFoundError: No module named 'pandas'`

**Context**: Only needed for Parquet generation

**Fix**:
```bash
pip install pandas pyarrow
```

### Issue 4: File Already Exists

**Error**: `FileExistsError`

**Fix**:
```bash
# Remove old generated files
rm -rf generated_data/

# Regenerate
python generate_sample_data.py --format csv --num-files 5
```

---

## Diagnostic Commands

### Complete Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== Glue Crawler Health Check ==="

# Check Terraform state
echo -e "\n1. Checking Terraform deployment..."
cd terraform && terraform show | grep -E "aws_glue_crawler|aws_glue_catalog_database|aws_s3_bucket" && cd ..

# Check S3 bucket
echo -e "\n2. Checking S3 bucket..."
aws s3 ls s3://$BUCKET_NAME/third-party-data/ --summarize

# Check Glue database
echo -e "\n3. Checking Glue database..."
aws glue get-database --name $DB_NAME

# Check crawler state
echo -e "\n4. Checking crawler state..."
aws glue get-crawler --name $CRAWLER_NAME | jq '{State: .Crawler.State, LastRunState: .Crawler.LastCrawl.Status}'

# Check tables
echo -e "\n5. Checking tables..."
aws glue get-tables --database-name $DB_NAME | jq '.TableList | length'
aws glue get-tables --database-name $DB_NAME | jq '.TableList[].Name'

# Check IAM role
echo -e "\n6. Checking IAM role..."
ROLE_NAME=$(aws glue get-crawler --name $CRAWLER_NAME | jq -r '.Crawler.Role' | cut -d'/' -f2)
aws iam get-role --role-name $ROLE_NAME | jq '{RoleName: .Role.RoleName, Arn: .Role.Arn}'

echo -e "\n=== Health Check Complete ==="
```

Usage:
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## Getting Additional Help

### Enable Debug Logging

**Terraform**:
```bash
export TF_LOG=DEBUG
terraform apply 2>&1 | tee terraform-debug.log
```

**AWS CLI**:
```bash
aws glue start-crawler --name $CRAWLER_NAME --debug 2>&1 | tee aws-debug.log
```

**Python**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Collect Diagnostic Information

```bash
# System info
echo "AWS Region: $AWS_REGION"
echo "Account ID: $(aws sts get-caller-identity --query Account --output text)"

# Terraform version
terraform version

# AWS CLI version
aws --version

# Python version
python --version

# Installed packages
pip list | grep -E "boto3|pandas|pyarrow"
```

### Contact Support

When requesting help, provide:
1. Error message (complete, not truncated)
2. Crawler state and last error
3. S3 file structure (ls output)
4. Table count and names
5. Terraform version
6. AWS region
7. What you've tried

---

## Prevention

### Pre-Flight Checklist

Before running the crawler:

- [ ] All files in same S3 prefix
- [ ] All files same format (CSV, JSON, or Parquet)
- [ ] All files same compression (gzip, snappy, or none)
- [ ] Schema consistent across files
- [ ] Crawler configuration includes CombineCompatibleSchemas
- [ ] Similarity threshold set appropriately (0.8)
- [ ] IAM permissions correct
- [ ] No conflicting crawlers running

### Regular Maintenance

- Monitor crawler execution (CloudWatch)
- Review table count periodically
- Check for schema drift
- Validate data quality
- Review cost and performance metrics
- Update documentation

---

## Quick Reference

| Problem | Quick Check | Quick Fix |
|---------|-------------|-----------|
| Multiple tables | `aws glue get-tables` | Check S3 prefixes, formats |
| Crawler fails | Check CloudWatch logs | Review IAM permissions |
| Wrong schema | View table columns | Regenerate data |
| Slow crawler | Check file count/size | Combine small files |
| No data | Check S3 location | Verify upload path |
| Can't deploy | Terraform validate | Check AWS credentials |

---

## Summary

Most issues fall into these categories:
1. **Configuration** - Wrong settings in Terraform
2. **Data inconsistency** - Mixed formats, schemas, or locations
3. **Permissions** - IAM roles or policies incorrect
4. **Environment** - AWS credentials or tool versions

Always start with:
1. Check crawler logs
2. Verify S3 file structure
3. Review crawler configuration
4. Validate IAM permissions

For persistent issues, review [MULTIPLE_TABLES_CAUSES.md](MULTIPLE_TABLES_CAUSES.md) and [DEA_C01_BEST_PRACTICES.md](DEA_C01_BEST_PRACTICES.md).
