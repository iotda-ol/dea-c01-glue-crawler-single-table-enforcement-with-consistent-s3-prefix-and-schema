# Multi-Cloud Component Quick Reference

This quick reference card summarizes the cloud service equivalents for the Glue Crawler single table enforcement solution.

## 📋 Cloud Service Mapping

### Storage & Data Management

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Object Storage** | Amazon S3 | Google Cloud Storage | Azure Blob Storage |
| **Data Catalog** | AWS Glue Data Catalog | Dataplex / Data Catalog | Microsoft Purview |
| **Schema Discovery** | AWS Glue Crawler | Dataplex Auto Discovery | Purview Scanner / ADF |
| **ETL Service** | AWS Glue ETL | Cloud Data Fusion / Dataflow | Azure Data Factory |

### Identity & Security

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Service Identity** | IAM Roles | Service Accounts | Managed Identities |
| **Access Control** | IAM Policies | Cloud IAM | Azure RBAC |
| **Encryption Keys** | KMS | Cloud KMS | Key Vault |
| **Network Security** | VPC Endpoints | Private Service Connect | Private Endpoints |

### Query & Analytics

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Serverless SQL** | Amazon Athena | BigQuery | Synapse Serverless SQL |
| **Data Warehouse** | Amazon Redshift | BigQuery | Azure Synapse Analytics |
| **Spark/Hadoop** | Amazon EMR | Cloud Dataproc | Azure Databricks |
| **External Tables** | Redshift Spectrum | BigQuery External Tables | Synapse External Tables |

### Observability

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Logging** | CloudWatch Logs | Cloud Logging | Azure Monitor Logs |
| **Metrics** | CloudWatch | Cloud Monitoring | Azure Monitor Metrics |
| **Audit Trail** | CloudTrail | Cloud Audit Logs | Azure Activity Log |
| **Dashboards** | CloudWatch Dashboards | Cloud Monitoring Dashboards | Azure Dashboards |

## 🔑 Critical Configuration (Universal)

### 1. Prefix Structure (All Clouds)

✅ **Correct** - Single flat prefix:
```
storage://bucket/third-party-data/file1.csv
storage://bucket/third-party-data/file2.csv
storage://bucket/third-party-data/file3.csv
```

❌ **Wrong** - Date-based subdirectories create multiple tables:
```
storage://bucket/data/2024/01/file1.csv
storage://bucket/data/2024/02/file1.csv
```

### 2. Schema Merge Configuration

| Cloud | Configuration |
|-------|---------------|
| **AWS** | `TableGroupingPolicy: "CombineCompatibleSchemas"`<br/>`AddOrUpdateBehavior: "MergeNewColumns"` |
| **GCP** | Enable schema evolution in Dataplex<br/>Auto-merge compatible schemas |
| **Azure** | Enable schema drift in Purview scan rules<br/>Configure merge in ADF |

### 3. File Consistency Requirements

- ✅ All files MUST use the same format (CSV, JSON, or Parquet)
- ✅ All files MUST use the same compression (none, gzip, snappy, etc.)
- ✅ Schema SHOULD be compatible across all files
- ❌ DO NOT mix formats or compression types

### 4. Similarity Threshold

| Value | Behavior | Use Case |
|-------|----------|----------|
| **0.7** | Aggressive grouping | When schemas vary slightly |
| **0.8** | Balanced (recommended) | Most use cases |
| **0.9** | Conservative | When strict schema matching needed |

## 💰 Cost Comparison (USD, approximate)

### Storage (per GB/month)

| Service | Cost | Notes |
|---------|------|-------|
| AWS S3 Standard | $0.023 | First 50TB |
| GCP Standard Storage | $0.020 | First TB |
| Azure Blob Hot | $0.018 | First 50TB |

### Catalog

| Service | Cost | Notes |
|---------|------|-------|
| AWS Glue Catalog | $1 per 100K objects | First 1M free |
| GCP Dataplex | Included | With Dataplex pricing |
| Azure Purview | $0.28/capacity unit/hr | Minimum 2 units |

### Crawler/Scanner (per hour)

| Service | Cost | Notes |
|---------|------|-------|
| AWS Glue Crawler | $0.44/DPU-hour | Min 2 DPUs |
| GCP Dataplex Discovery | Included | With Dataplex |
| Azure Purview Scanner | Included | In capacity units |

### Query (per TB processed)

| Service | Cost | Notes |
|---------|------|-------|
| AWS Athena | $5.00 | Per TB scanned |
| GCP BigQuery | $5.00 | First 1TB/month free |
| Azure Synapse Serverless | $5.00 | Per TB processed |

## 🔄 Migration Paths

### AWS ➜ GCP

1. **Storage**: Use Storage Transfer Service (S3 → Cloud Storage)
2. **Catalog**: Export Glue metadata → Import to Dataplex API
3. **ETL**: Rewrite Glue jobs to Dataflow/Dataproc
4. **Tools**: `gsutil`, Storage Transfer Service, Dataflow templates

### AWS ➜ Azure

1. **Storage**: Use AzCopy or Data Factory (S3 → Blob Storage)
2. **Catalog**: Export Glue metadata → Create Purview assets
3. **ETL**: Migrate Glue jobs to Data Factory/Databricks
4. **Tools**: AzCopy, Azure Data Factory, Azure Migrate

### GCP ➜ AWS

1. **Storage**: Use gsutil or Storage Transfer (Cloud Storage → S3)
2. **Catalog**: Export BigQuery/Dataplex schemas → Glue Catalog API
3. **ETL**: Rewrite Dataflow to Glue ETL
4. **Tools**: `aws s3 sync`, Storage Transfer, Glue API

### Azure ➜ AWS

1. **Storage**: Use AzCopy or DataSync (Blob → S3)
2. **Catalog**: Export Purview metadata → Glue Catalog
3. **ETL**: Migrate Data Factory to Glue workflows
4. **Tools**: AzCopy, AWS DataSync, Glue API

## 📚 IaC Provider Support

| Cloud | Terraform | Pulumi | Native IaC | CDK |
|-------|-----------|--------|------------|-----|
| **AWS** | ✅ hashicorp/aws | ✅ pulumi/aws | CloudFormation | AWS CDK |
| **GCP** | ✅ hashicorp/google | ✅ pulumi/gcp | Deployment Manager | - |
| **Azure** | ✅ hashicorp/azurerm | ✅ pulumi/azure | ARM/Bicep | - |

## 🎯 Best Practices (Universal)

### Data Organization
- ✅ Single, consistent prefix structure
- ✅ Flat directory structure (avoid date-based folders in data path)
- ✅ Uniform file format and compression
- ✅ UTF-8 encoding for text files

### Security
- ✅ Encryption at rest (provider-managed or customer-managed keys)
- ✅ Encryption in transit (HTTPS/TLS only)
- ✅ Service identities (no hard-coded credentials)
- ✅ Audit logging enabled
- ✅ Public access blocked by default

### Performance
- ✅ Use incremental/delta scanning
- ✅ Compress data files appropriately
- ✅ Columnar formats (Parquet/ORC) for analytics
- ✅ Partitioning via catalog, not file paths
- ✅ Regular cleanup of old data

### Cost Optimization
- ✅ Schedule crawlers/scanners (don't run continuously)
- ✅ Use lifecycle policies for old data
- ✅ Compress files (50-90% storage reduction)
- ✅ Use reserved/committed capacity for predictable loads
- ✅ Clean up unused tables and metadata

## 📖 Additional Resources

### AWS
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [DEA-C01 Exam Guide](https://aws.amazon.com/certification/certified-data-engineer-associate/)

### GCP
- [Dataplex Documentation](https://cloud.google.com/dataplex/docs)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [GCP Best Practices](https://cloud.google.com/architecture/framework)

### Azure
- [Microsoft Purview Documentation](https://docs.microsoft.com/azure/purview/)
- [Azure Data Factory Documentation](https://docs.microsoft.com/azure/data-factory/)
- [Azure Architecture Center](https://docs.microsoft.com/azure/architecture/)

---

**📊 Version**: 1.0  
**📅 Last Updated**: 2025-12-21  
**🌐 For Full Documentation**: See `INFRASTRUCTURE_DIAGRAM.md`
