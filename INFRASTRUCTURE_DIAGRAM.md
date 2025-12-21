# Universal Infrastructure Diagram Guide

## Overview

This document explains the **universal infrastructure diagram** (`map-diagram-infra.mermaid`) that maps the AWS Glue Crawler single table enforcement solution to equivalent components in **AWS**, **GCP**, and **Azure**.

## Diagram File

📄 **File**: `map-diagram-infra.mermaid`  
📊 **Format**: Mermaid (universal, GitHub-compatible)  
🌐 **Clouds Covered**: AWS, GCP, Azure

## Viewing the Diagram

### Option 1: GitHub (Recommended)
GitHub natively renders Mermaid diagrams. Simply view the `map-diagram-infra.mermaid` file on GitHub.

### Option 2: Mermaid Live Editor
1. Go to https://mermaid.live/
2. Copy the contents of `map-diagram-infra.mermaid`
3. Paste into the editor
4. View and export (PNG, SVG, PDF)

### Option 3: VS Code
1. Install the "Markdown Preview Mermaid Support" extension
2. Create a markdown file with:
   ````markdown
   ```mermaid
   [paste diagram content here]
   ```
   ````
3. Open preview (Ctrl+Shift+V or Cmd+Shift+V)

### Option 4: Command Line (mermaid-cli)
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.png

# Generate SVG
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.svg

# Generate PDF
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.pdf
```

## Architecture Components

The diagram illustrates the following universal components mapped across AWS, GCP, and Azure:

### 1. Object Storage Layer
- **AWS**: Amazon S3 (Simple Storage Service)
- **GCP**: Google Cloud Storage
- **Azure**: Azure Blob Storage

**Key Features**:
- Consistent prefix structure (`third-party-data/`)
- Encryption at rest
- Versioning for data protection

### 2. Data Catalog Layer
- **AWS**: AWS Glue Data Catalog
- **GCP**: Google Cloud Dataplex / Data Catalog
- **Azure**: Microsoft Purview Data Catalog

**Key Features**:
- Centralized metadata repository
- Schema versioning
- Single table metadata

### 3. Schema Discovery & Crawler
- **AWS**: AWS Glue Crawler
- **GCP**: Dataplex Auto Discovery / Cloud Data Fusion
- **Azure**: Microsoft Purview Scanner / Azure Data Factory

**Key Features**:
- Automatic schema discovery
- Schema merge policy (CombineCompatibleSchemas)
- Incremental scanning

### 4. Identity & Access Management
- **AWS**: IAM Roles
- **GCP**: Service Accounts
- **Azure**: Managed Identities

**Key Features**:
- Service-level permissions
- No hard-coded credentials
- Least privilege access

### 5. Query & Analytics
**Query Engines**:
- **AWS**: Amazon Athena
- **GCP**: BigQuery
- **Azure**: Azure Synapse Serverless SQL

**Analytics Platforms**:
- **AWS**: Amazon EMR, Redshift Spectrum
- **GCP**: Cloud Dataproc, BigQuery
- **Azure**: Azure Databricks, Synapse Analytics

### 6. Observability
**Logging**:
- **AWS**: CloudWatch Logs
- **GCP**: Cloud Logging
- **Azure**: Azure Monitor Logs

**Monitoring**:
- **AWS**: CloudWatch
- **GCP**: Cloud Monitoring
- **Azure**: Azure Monitor

**Audit Trail**:
- **AWS**: CloudTrail
- **GCP**: Cloud Audit Logs
- **Azure**: Activity Log

### 7. Security Controls
**Network Security**:
- **AWS**: VPC Endpoints
- **GCP**: Private Service Connect
- **Azure**: Private Endpoints

**Access Control**:
- Bucket/container policies
- IAM/RBAC policies
- Public access blocked

## Critical Configuration for Single Table Enforcement

### 1. Consistent Prefix Structure
✅ **Correct**:
```
storage://bucket/third-party-data/file1.csv
storage://bucket/third-party-data/file2.csv
storage://bucket/third-party-data/file3.csv
```

❌ **Wrong** (creates multiple tables):
```
storage://bucket/data/2024/01/file1.csv
storage://bucket/vendor-a/file1.csv
```

### 2. Schema Merge Policy
- **AWS**: `CombineCompatibleSchemas` + `MergeNewColumns`
- **GCP**: Auto merge with schema evolution enabled
- **Azure**: Enable schema drift handling in scan rules

### 3. Similarity Threshold
- **Recommended**: 0.8 (balances grouping vs. accuracy)
- **Lower (0.7)**: More aggressive grouping
- **Higher (0.9)**: Conservative grouping

### 4. File Format Consistency
- All files must use the same format: CSV, JSON, or Parquet
- All files must use the same compression: none, gzip, snappy, etc.
- Mixed formats or compression will create multiple tables

### 5. Recrawl Policy
- **AWS**: `CRAWL_NEW_FOLDERS_ONLY`
- **GCP**: Incremental discovery
- **Azure**: Incremental scan with delta detection

## Infrastructure as Code (IaC) Equivalents

### Terraform Providers

**AWS**:
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Resources: aws_s3_bucket, aws_glue_crawler, aws_glue_catalog_database
```

**GCP**:
```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Resources: google_storage_bucket, google_dataplex_lake, google_data_catalog_entry
```

**Azure**:
```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Resources: azurerm_storage_account, azurerm_purview_account, azurerm_data_factory
```

### Other IaC Tools
- **Pulumi**: Available for all three clouds with unified API
- **CloudFormation**: AWS only
- **ARM/Bicep**: Azure only
- **Deployment Manager**: GCP only

## Cost Comparison

### Storage (per GB/month)
- **AWS S3 Standard**: ~$0.023
- **GCP Standard Storage**: ~$0.020
- **Azure Blob Hot**: ~$0.018

### Catalog
- **AWS Glue**: First 1M objects free, then $1 per 100K
- **GCP Dataplex**: Included with usage
- **Azure Purview**: ~$0.28 per capacity unit per hour

### Crawler/Scanner (per hour)
- **AWS Glue Crawler**: ~$0.44 per DPU-hour
- **GCP Dataplex Discovery**: Included with Dataplex
- **Azure Purview Scanner**: Included in capacity unit pricing

### Query
- **AWS Athena**: $5 per TB scanned
- **GCP BigQuery**: $5 per TB processed (first 1TB/month free)
- **Azure Synapse Serverless**: $5 per TB processed

## Migration Paths

### AWS → GCP
1. Use **Storage Transfer Service** to copy S3 → Cloud Storage
2. Export Glue Catalog to JSON
3. Import to Dataplex using API
4. Rewrite Glue ETL jobs to Dataflow/Dataproc

### AWS → Azure
1. Use **AzCopy** or **Data Factory** to copy S3 → Blob Storage
2. Export Glue Catalog metadata
3. Create equivalent Purview assets
4. Migrate Glue jobs to Azure Data Factory/Databricks

### GCP → AWS
1. Use **gsutil** or **Storage Transfer** to copy Cloud Storage → S3
2. Export BigQuery/Dataplex schemas
3. Create Glue Catalog tables via API/Terraform
4. Rewrite Dataflow to Glue ETL

### Azure → AWS
1. Use **AzCopy** or **AWS DataSync** to copy Blob → S3
2. Export Purview metadata
3. Populate Glue Catalog
4. Migrate Data Factory pipelines to Glue workflows

## Best Practices (Universal)

### Data Organization
- ✅ Use consistent, flat prefix structure
- ✅ Single format per dataset (CSV, JSON, or Parquet)
- ✅ Consistent compression type across all files
- ✅ UTF-8 encoding for text files
- ❌ Avoid date-based subdirectories in the data path

### Security
- ✅ Enable encryption at rest
- ✅ Enforce encryption in transit (HTTPS/TLS only)
- ✅ Use service identities, not user credentials
- ✅ Enable audit logging for all access
- ✅ Block public access by default

### Schema Management
- ✅ Enable schema evolution/merge
- ✅ Use backward-compatible changes only
- ✅ Version control schema changes
- ✅ Document breaking changes

### Cost Optimization
- ✅ Use incremental/delta scanning
- ✅ Compress data files (gzip for CSV, snappy for Parquet)
- ✅ Set appropriate lifecycle policies
- ✅ Use reserved capacity for predictable workloads
- ✅ Clean up unused tables and data

### Monitoring & Operations
- ✅ Set up alerting for crawler/scanner failures
- ✅ Monitor schema drift
- ✅ Track data quality metrics
- ✅ Implement data validation pipelines
- ✅ Regular backup of metadata

## Integration Examples

### AWS Example (Current Implementation)
```hcl
# See terraform/main.tf for complete implementation
resource "aws_glue_crawler" "single_table" {
  name          = "glue-single-table-dev-crawler"
  database_name = aws_glue_catalog_database.main.name
  
  s3_target {
    path = "s3://bucket/third-party-data/"
  }
  
  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }
  
  configuration = jsonencode({
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
}
```

### GCP Equivalent (Pseudo-code)
```hcl
resource "google_dataplex_lake" "main" {
  name     = "data-lake"
  location = "us-central1"
}

resource "google_dataplex_zone" "raw" {
  name     = "raw-zone"
  lake     = google_dataplex_lake.main.name
  type     = "RAW"
  
  discovery_spec {
    enabled  = true
    schedule = "0 1 * * *"
  }
}

resource "google_dataplex_asset" "third_party_data" {
  name          = "third-party-data"
  lake          = google_dataplex_lake.main.name
  dataplex_zone = google_dataplex_zone.raw.name
  
  resource_spec {
    type = "STORAGE_BUCKET"
    name = "projects/${var.project}/buckets/${var.bucket}"
  }
}
```

### Azure Equivalent (Pseudo-code)
```hcl
resource "azurerm_purview_account" "main" {
  name                = "purview-account"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  identity {
    type = "SystemAssigned"
  }
}

# Azure Data Factory for scanning
resource "azurerm_data_factory" "main" {
  name                = "data-factory"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# Purview Scanner would be configured via Azure Portal or API
```

## Related Documentation

- **[README.md](README.md)**: Project overview and quick start
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: AWS-specific architecture details
- **[docs/SETUP.md](docs/SETUP.md)**: Detailed setup guide for AWS
- **[docs/DEA_C01_BEST_PRACTICES.md](docs/DEA_C01_BEST_PRACTICES.md)**: AWS certification best practices

## Support

For questions or issues with the diagram:
1. Check the [Mermaid documentation](https://mermaid.js.org/)
2. Open an issue on GitHub
3. Refer to cloud provider documentation for specific implementations

## Contributing

To update the diagram:
1. Edit `map-diagram-infra.mermaid`
2. Test rendering using one of the methods above
3. Update this guide if adding new components
4. Submit a pull request

---

**📊 Diagram Version**: 1.0  
**📅 Last Updated**: 2025-12-21  
**🌐 Clouds Supported**: AWS, GCP, Azure
