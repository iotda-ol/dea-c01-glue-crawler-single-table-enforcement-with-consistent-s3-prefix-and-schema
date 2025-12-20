# Setup and Deployment Guide

This guide walks you through deploying the AWS Glue crawler solution for single table enforcement.

## Prerequisites

### Required Tools
- **Terraform** >= 1.0 ([Download](https://www.terraform.io/downloads))
- **Python** >= 3.8 ([Download](https://www.python.org/downloads/))
- **AWS CLI** >= 2.0 ([Download](https://aws.amazon.com/cli/))
- **Git** ([Download](https://git-scm.com/downloads))

### AWS Requirements
- AWS Account with appropriate permissions
- IAM user or role with permissions to create:
  - S3 buckets
  - IAM roles and policies
  - Glue resources (databases, crawlers)

### AWS Permissions Required

The following AWS permissions are needed to deploy this solution:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketVersioning",
        "s3:PutEncryptionConfiguration",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateDatabase",
        "glue:CreateCrawler",
        "glue:UpdateCrawler",
        "glue:StartCrawler",
        "glue:GetCrawler",
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetTables"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/dea-c01-glue-crawler-single-table-enforcement-with-consistent-s3-prefix-and-schema.git
cd dea-c01-glue-crawler-single-table-enforcement-with-consistent-s3-prefix-and-schema
```

### Step 2: Configure AWS Credentials

**Option A: Using AWS CLI**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your default output format (json)
```

**Option B: Using Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option C: Using AWS Profile**
```bash
export AWS_PROFILE="your-profile-name"
```

### Step 3: Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
# or using virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### Step 4: Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` to customize your deployment:

```hcl
# terraform.tfvars

# AWS Configuration
aws_region  = "us-east-1"        # Your preferred region
environment = "dev"               # dev, staging, or prod

# Project Configuration
project_name = "glue-single-table"  # Your project name

# S3 Configuration
s3_data_prefix = "third-party-data"  # S3 prefix for data files

# Crawler Configuration
table_similarity_threshold = 0.8     # 0.7-0.9 recommended
crawler_schedule          = ""       # Leave empty for manual execution
```

### Step 5: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...

Terraform has been successfully initialized!
```

### Step 6: Review Terraform Plan

```bash
terraform plan
```

This shows what resources will be created without actually creating them. Review the output carefully.

Expected resources:
- 1 S3 bucket
- 1 S3 bucket versioning configuration
- 1 S3 bucket encryption configuration
- 1 S3 bucket public access block
- 1 S3 object (prefix)
- 1 Glue database
- 1 IAM role
- 1 IAM role policy attachment
- 1 IAM role policy
- 1 Glue crawler

### Step 7: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm the deployment.

Expected output:
```
Apply complete! Resources: 10 added, 0 changed, 0 destroyed.

Outputs:

aws_console_crawler_url = "https://us-east-1.console.aws.amazon.com/glue/home?region=us-east-1#/v2/data-catalog/crawlers/view/glue-single-table-dev-crawler"
glue_crawler_name = "glue-single-table-dev-crawler"
glue_database_name = "glue_single_table_dev_db"
s3_bucket_name = "glue-single-table-dev-123456789012"
s3_data_path = "s3://glue-single-table-dev-123456789012/third-party-data/"
```

**Save these outputs** - you'll need them for the next steps.

---

## Testing the Solution

### Step 1: Generate Sample Data

```bash
cd ../python

# Generate CSV files with gzip compression
python generate_sample_data.py \
  --format csv \
  --compression gzip \
  --num-files 5 \
  --records-per-file 1000
```

This creates 5 CSV files in the `generated_data/` directory.

**Alternative formats**:
```bash
# JSON format
python generate_sample_data.py --format json --compression gzip --num-files 5

# Parquet format (requires pandas and pyarrow)
python generate_sample_data.py --format parquet --compression snappy --num-files 5
```

### Step 2: Upload Data to S3

```bash
# Replace with your bucket name from Terraform output
export BUCKET_NAME="glue-single-table-dev-123456789012"

python upload_to_s3.py \
  --bucket $BUCKET_NAME \
  --prefix third-party-data
```

Expected output:
```
✓ Bucket 'glue-single-table-dev-123456789012' is accessible

Uploading files to s3://glue-single-table-dev-123456789012/third-party-data/

Uploading sample_data_001.csv.gz (2,145 bytes)... ✓
Uploading sample_data_002.csv.gz (2,198 bytes)... ✓
Uploading sample_data_003.csv.gz (2,176 bytes)... ✓
Uploading sample_data_004.csv.gz (2,189 bytes)... ✓
Uploading sample_data_005.csv.gz (2,201 bytes)... ✓

✓ Files uploaded successfully
```

### Step 3: Run the Glue Crawler

**Option A: Using AWS CLI**
```bash
# Replace with your crawler name from Terraform output
export CRAWLER_NAME="glue-single-table-dev-crawler"

aws glue start-crawler --name $CRAWLER_NAME
```

**Option B: Using AWS Console**
1. Navigate to the AWS Console URL from Terraform output
2. Click "Run crawler"
3. Wait for crawler to complete (typically 1-2 minutes)

### Step 4: Monitor Crawler Execution

```bash
# Check crawler status
aws glue get-crawler --name $CRAWLER_NAME | jq '.Crawler.State'

# Wait for "READY" status
watch -n 5 'aws glue get-crawler --name $CRAWLER_NAME | jq ".Crawler.State"'
```

Possible states:
- `RUNNING` - Crawler is executing
- `READY` - Crawler completed successfully
- `FAILED` - Crawler encountered an error

### Step 5: Verify Single Table Creation

```bash
# List tables in the database
export DB_NAME="glue_single_table_dev_db"

aws glue get-tables --database-name $DB_NAME | jq '.TableList[].Name'
```

**Expected output**: Only ONE table name
```json
"third_party_data"
```

**❌ If you see multiple tables**, review [MULTIPLE_TABLES_CAUSES.md](MULTIPLE_TABLES_CAUSES.md) for troubleshooting.

### Step 6: Inspect Table Schema

```bash
# Get table details
aws glue get-table \
  --database-name $DB_NAME \
  --name third_party_data | jq '.Table.StorageDescriptor.Columns'
```

Expected schema:
```json
[
  {
    "Name": "transaction_id",
    "Type": "string"
  },
  {
    "Name": "customer_id",
    "Type": "string"
  },
  {
    "Name": "product_name",
    "Type": "string"
  },
  {
    "Name": "quantity",
    "Type": "bigint"
  },
  {
    "Name": "unit_price",
    "Type": "double"
  },
  {
    "Name": "total_amount",
    "Type": "double"
  },
  {
    "Name": "transaction_date",
    "Type": "string"
  },
  {
    "Name": "status",
    "Type": "string"
  }
]
```

### Step 7: Query Data with Athena (Optional)

```bash
# Query the cataloged data using Athena
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM ${DB_NAME}.third_party_data" \
  --query-execution-context Database=${DB_NAME} \
  --result-configuration OutputLocation=s3://${BUCKET_NAME}/athena-results/
```

---

## Verification Checklist

After deployment, verify:

- [ ] Terraform deployed successfully (10 resources)
- [ ] S3 bucket created with encryption enabled
- [ ] Glue database created
- [ ] Glue crawler created and configured
- [ ] IAM role created with correct permissions
- [ ] Sample data generated successfully
- [ ] Files uploaded to correct S3 prefix
- [ ] Crawler executed successfully
- [ ] **Only ONE table created** (critical!)
- [ ] Table schema matches expected schema
- [ ] Data queryable via Athena (optional)

---

## Common Setup Issues

### Issue 1: Terraform Init Fails

**Error**: `Failed to download provider`

**Solution**:
```bash
# Clear Terraform cache
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### Issue 2: AWS Credentials Not Found

**Error**: `No valid credential sources found`

**Solution**:
```bash
# Verify AWS configuration
aws sts get-caller-identity

# If fails, reconfigure
aws configure
```

### Issue 3: S3 Bucket Name Already Exists

**Error**: `BucketAlreadyExists`

**Solution**: Edit `terraform.tfvars` and change `project_name` or `environment`:
```hcl
project_name = "glue-single-table-unique"
```

### Issue 4: Insufficient IAM Permissions

**Error**: `AccessDenied`

**Solution**: Ensure your IAM user/role has the required permissions listed in [Prerequisites](#aws-permissions-required).

### Issue 5: Python Dependencies Installation Fails

**Error**: `No module named 'boto3'`

**Solution**:
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue 6: Crawler Creates Multiple Tables

**Problem**: More than one table created

**Solution**: See [MULTIPLE_TABLES_CAUSES.md](MULTIPLE_TABLES_CAUSES.md) for detailed troubleshooting.

---

## Configuration Options

### Changing the AWS Region

Edit `terraform.tfvars`:
```hcl
aws_region = "eu-west-1"  # Change to your region
```

Then re-deploy:
```bash
terraform apply
```

### Changing the S3 Prefix

Edit `terraform.tfvars`:
```hcl
s3_data_prefix = "my-custom-prefix"
```

Update sample data upload:
```bash
python upload_to_s3.py --bucket $BUCKET_NAME --prefix my-custom-prefix
```

### Scheduling the Crawler

Edit `terraform.tfvars`:
```hcl
# Run daily at 2 AM UTC
crawler_schedule = "cron(0 2 * * ? *)"

# Run every 6 hours
crawler_schedule = "cron(0 */6 * * ? *)"
```

Apply changes:
```bash
terraform apply
```

### Adjusting Similarity Threshold

Edit `terraform.tfvars`:
```hcl
# More aggressive grouping (may combine different schemas)
table_similarity_threshold = 0.7

# Conservative grouping (stricter matching)
table_similarity_threshold = 0.9
```

Apply changes:
```bash
terraform apply
```

---

## Next Steps

### For Development
1. Experiment with different file formats (CSV, JSON, Parquet)
2. Test schema evolution (add new columns)
3. Try different compression types
4. Adjust similarity threshold

### For Production
1. Review [DEA_C01_BEST_PRACTICES.md](DEA_C01_BEST_PRACTICES.md)
2. Implement monitoring and alerting
3. Set up appropriate crawler schedule
4. Configure backup and disaster recovery
5. Implement Lake Formation governance (optional)
6. Set up cost monitoring

### For Learning
1. Review [ARCHITECTURE.md](ARCHITECTURE.md)
2. Study [MULTIPLE_TABLES_CAUSES.md](MULTIPLE_TABLES_CAUSES.md)
3. Practice troubleshooting scenarios
4. Prepare for DEA-C01 exam

---

## Cleanup

To destroy all resources and avoid ongoing costs:

```bash
cd terraform

# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

Type `yes` when prompted.

**Note**: This will delete:
- S3 bucket (ensure it's empty first)
- Glue database and all tables
- Glue crawler
- IAM role and policies

To manually empty the S3 bucket before destroying:
```bash
aws s3 rm s3://$BUCKET_NAME --recursive
```

---

## Support and Troubleshooting

### Getting Help

1. **Check Documentation**:
   - [ARCHITECTURE.md](ARCHITECTURE.md)
   - [MULTIPLE_TABLES_CAUSES.md](MULTIPLE_TABLES_CAUSES.md)
   - [DEA_C01_BEST_PRACTICES.md](DEA_C01_BEST_PRACTICES.md)
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

2. **AWS Resources**:
   - [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
   - [AWS Terraform Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

3. **Community**:
   - AWS Forums
   - Stack Overflow (tag: aws-glue)
   - GitHub Issues

### Logging and Debugging

Enable detailed logging:
```bash
# Terraform debug logs
export TF_LOG=DEBUG
terraform apply

# AWS CLI debug
aws glue start-crawler --name $CRAWLER_NAME --debug

# Python script verbose output
python generate_sample_data.py --verbose
```

### Health Check Commands

```bash
# Check S3 bucket
aws s3 ls s3://$BUCKET_NAME/third-party-data/

# Check Glue database
aws glue get-database --name $DB_NAME

# Check crawler status
aws glue get-crawler --name $CRAWLER_NAME

# Check tables
aws glue get-tables --database-name $DB_NAME

# Check crawler metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Glue \
  --metric-name glue.crawler.runtime \
  --dimensions Name=CrawlerName,Value=$CRAWLER_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average
```

---

## Summary

You've successfully:
- ✅ Deployed AWS Glue infrastructure with Terraform
- ✅ Generated sample data with consistent schema
- ✅ Uploaded data to S3 with proper structure
- ✅ Executed Glue crawler
- ✅ Verified single table creation
- ✅ Learned configuration options

**Key Takeaways**:
1. Consistent S3 prefix is critical
2. Same format and compression across files
3. Compatible schema enables single table
4. Proper crawler configuration matters
5. Regular monitoring ensures reliability

For production deployments, follow [DEA_C01_BEST_PRACTICES.md](DEA_C01_BEST_PRACTICES.md).
