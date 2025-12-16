#!/bin/bash
# Complete Workflow for AWS Glue Crawler Single Table Enforcement
# This script demonstrates the end-to-end process

set -e  # Exit on error

echo "==========================================="
echo "AWS Glue Crawler - Single Table Workflow"
echo "==========================================="

# Configuration
PROJECT_DIR=$(pwd)
AWS_REGION=${AWS_REGION:-"us-east-1"}
ENVIRONMENT=${ENVIRONMENT:-"dev"}

echo -e "\n1. Checking prerequisites..."
command -v terraform >/dev/null 2>&1 || { echo "Error: terraform not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "Error: aws cli not found"; exit 1; }

echo "✓ All prerequisites met"

# Verify AWS credentials
echo -e "\n2. Verifying AWS credentials..."
aws sts get-caller-identity >/dev/null 2>&1 || { echo "Error: AWS credentials not configured"; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account: $ACCOUNT_ID"
echo "✓ AWS Region: $AWS_REGION"

# Deploy infrastructure
echo -e "\n3. Deploying infrastructure with Terraform..."
cd terraform

if [ ! -f terraform.tfvars ]; then
    echo "Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo "⚠️  Please review terraform.tfvars and customize if needed"
    echo "Press Enter to continue..."
    read
fi

echo "Initializing Terraform..."
terraform init -input=false

echo "Planning infrastructure..."
terraform plan -out=tfplan

echo "Applying infrastructure..."
terraform apply -auto-approve tfplan

# Extract outputs
BUCKET_NAME=$(terraform output -raw s3_bucket_name)
DB_NAME=$(terraform output -raw glue_database_name)
CRAWLER_NAME=$(terraform output -raw glue_crawler_name)
S3_DATA_PATH=$(terraform output -raw s3_data_path)

echo -e "\n✓ Infrastructure deployed successfully!"
echo "  Bucket: $BUCKET_NAME"
echo "  Database: $DB_NAME"
echo "  Crawler: $CRAWLER_NAME"
echo "  S3 Path: $S3_DATA_PATH"

cd ..

# Install Python dependencies
echo -e "\n4. Installing Python dependencies..."
cd python
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Python dependencies installed"

# Generate sample data
echo -e "\n5. Generating sample data..."
python generate_sample_data.py \
    --format csv \
    --compression gzip \
    --num-files 5 \
    --records-per-file 1000

echo "✓ Sample data generated"

# Upload to S3
echo -e "\n6. Uploading data to S3..."
python upload_to_s3.py \
    --bucket "$BUCKET_NAME" \
    --prefix third-party-data

echo "✓ Data uploaded to S3"

# Verify S3 contents
echo -e "\n7. Verifying S3 contents..."
FILE_COUNT=$(aws s3 ls s3://$BUCKET_NAME/third-party-data/ | wc -l)
echo "✓ Found $FILE_COUNT files in S3"

cd ..

# Run Glue Crawler
echo -e "\n8. Running Glue Crawler..."
aws glue start-crawler --name "$CRAWLER_NAME"

echo "Waiting for crawler to complete..."
STATUS="RUNNING"
while [ "$STATUS" = "RUNNING" ]; do
    sleep 10
    STATUS=$(aws glue get-crawler --name "$CRAWLER_NAME" | jq -r '.Crawler.State')
    echo "  Crawler status: $STATUS"
done

LAST_STATUS=$(aws glue get-crawler --name "$CRAWLER_NAME" | jq -r '.Crawler.LastCrawl.Status')
echo "✓ Crawler completed with status: $LAST_STATUS"

if [ "$LAST_STATUS" != "SUCCEEDED" ]; then
    echo "⚠️  Crawler did not succeed. Check CloudWatch logs for details."
    ERROR_MSG=$(aws glue get-crawler --name "$CRAWLER_NAME" | jq -r '.Crawler.LastCrawl.ErrorMessage')
    echo "Error: $ERROR_MSG"
    exit 1
fi

# Verify single table creation
echo -e "\n9. Verifying single table creation..."
TABLE_COUNT=$(aws glue get-tables --database-name "$DB_NAME" | jq '.TableList | length')
TABLE_NAMES=$(aws glue get-tables --database-name "$DB_NAME" | jq -r '.TableList[].Name')

echo "Number of tables created: $TABLE_COUNT"
echo "Table name(s): $TABLE_NAMES"

if [ "$TABLE_COUNT" -eq 1 ]; then
    echo "✅ SUCCESS! Exactly one table created as expected."
else
    echo "❌ FAILURE! Expected 1 table but got $TABLE_COUNT tables."
    echo "See docs/MULTIPLE_TABLES_CAUSES.md for troubleshooting."
    exit 1
fi

# Display table schema
echo -e "\n10. Table schema:"
aws glue get-table \
    --database-name "$DB_NAME" \
    --name "$TABLE_NAMES" | \
    jq '.Table.StorageDescriptor.Columns[] | {Name, Type}'

# Display table location
TABLE_LOCATION=$(aws glue get-table \
    --database-name "$DB_NAME" \
    --name "$TABLE_NAMES" | \
    jq -r '.Table.StorageDescriptor.Location')
echo -e "\nTable location: $TABLE_LOCATION"

# Display record count (if Athena is configured)
echo -e "\n11. Testing with Athena (optional)..."
read -p "Do you want to query the table with Athena? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    QUERY_EXEC_ID=$(aws athena start-query-execution \
        --query-string "SELECT COUNT(*) as record_count FROM ${DB_NAME}.${TABLE_NAMES}" \
        --query-execution-context Database="${DB_NAME}" \
        --result-configuration OutputLocation="s3://${BUCKET_NAME}/athena-results/" \
        --query 'QueryExecutionId' --output text)
    
    echo "Query execution ID: $QUERY_EXEC_ID"
    echo "Waiting for query to complete..."
    
    sleep 5
    aws athena get-query-results --query-execution-id "$QUERY_EXEC_ID" | \
        jq '.ResultSet.Rows'
fi

# Summary
echo -e "\n==========================================="
echo "Workflow Complete!"
echo "==========================================="
echo ""
echo "Summary:"
echo "  ✓ Infrastructure deployed"
echo "  ✓ Sample data generated and uploaded"
echo "  ✓ Glue crawler executed successfully"
echo "  ✓ Single table created: $TABLE_NAMES"
echo "  ✓ Table location: $TABLE_LOCATION"
echo ""
echo "Next steps:"
echo "  1. Query the table using Athena"
echo "  2. Review the schema and data"
echo "  3. Experiment with schema evolution"
echo "  4. Review documentation in docs/"
echo ""
echo "To clean up resources:"
echo "  cd terraform && terraform destroy"
echo ""
echo "AWS Console URLs:"
echo "  Crawler: https://${AWS_REGION}.console.aws.amazon.com/glue/home?region=${AWS_REGION}#/v2/data-catalog/crawlers/view/${CRAWLER_NAME}"
echo "  Database: https://${AWS_REGION}.console.aws.amazon.com/glue/home?region=${AWS_REGION}#/v2/data-catalog/databases/view/${DB_NAME}"
echo "  S3 Bucket: https://s3.console.aws.amazon.com/s3/buckets/${BUCKET_NAME}"
echo ""
echo "==========================================="
