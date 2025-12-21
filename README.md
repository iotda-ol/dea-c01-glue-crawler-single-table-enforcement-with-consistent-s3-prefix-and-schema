# AWS Glue Crawler - Single Table Enforcement Solution

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Terraform](https://img.shields.io/badge/Terraform-1.0+-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Glue-orange.svg)](https://aws.amazon.com/glue/)
[![DEA-C01](https://img.shields.io/badge/Exam-DEA--C01-blue.svg)](https://aws.amazon.com/certification/certified-data-engineer-associate/)

This repository demonstrates how to configure AWS Glue Crawlers to create a **single table** from third-party data stored in Amazon S3. It enforces consistent file format, compression, and schema, and uses a stable S3 prefix structure to prevent unintended table splits. Terraform examples and best practices align with **AWS Certified Data Engineer - Associate (DEA-C01)** exam objectives.

## 🎯 Problem Statement

When ingesting third-party data into a data lake, AWS Glue Crawlers often create **multiple tables** instead of the desired single table. This happens due to:
- Inconsistent S3 prefix structures
- Mixed file formats (CSV, JSON, Parquet)
- Different compression types
- Schema variations
- Improper crawler configuration

This solution provides a **production-ready approach** to enforce single table creation while maintaining schema flexibility.

## ✨ Features

- **Single Table Enforcement**: Crawler configuration guaranteed to create one table
- **Consistent Data Format**: Ensures uniform file format, compression, and schema
- **Terraform Infrastructure**: Complete IaC for S3, Glue, and IAM resources
- **Sample Data Generation**: Python scripts to generate test data with consistent schema
- **S3 Upload Automation**: Tools to upload data with proper prefix structure
- **Comprehensive Documentation**: Architecture, best practices, and troubleshooting guides
- **Multi-Cloud Architecture Diagram**: Universal infrastructure diagram mapping AWS, GCP, and Azure components
- **DEA-C01 Aligned**: Follows AWS Data Engineer certification best practices

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌────────────┐         ┌────────────────┐                 │
│  │ S3 Bucket  │◄────────│ Glue Crawler   │                 │
│  │            │  Scan   │                 │                 │
│  │ third-     │         │ - Single prefix │                 │
│  │ party-     │         │ - Schema merge  │                 │
│  │ data/      │         │ - Compatible    │                 │
│  │  file1.csv │         │   grouping      │                 │
│  │  file2.csv │         └────────┬────────┘                 │
│  │  file3.csv │                  │                          │
│  └────────────┘                  │ Creates                  │
│                                  ▼                          │
│                       ┌────────────────────┐                │
│                       │  Glue Data Catalog │                │
│                       │                    │                │
│                       │  ✓ Single Table    │                │
│                       │  ✓ Merged Schema   │                │
│                       │  ✓ Queryable       │                │
│                       └────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 🌐 Universal Multi-Cloud Architecture

See the **[Universal Infrastructure Diagram](INFRASTRUCTURE_DIAGRAM.md)** for a comprehensive view of how this architecture maps to AWS, GCP, and Azure components. The diagram shows equivalent services and migration paths between cloud providers.

- **📊 Interactive Diagram**: Open `diagram-viewer.html` in a browser
- **📝 Mermaid Source**: `map-diagram-infra.mermaid`
- **📚 Documentation**: `INFRASTRUCTURE_DIAGRAM.md`

## 📋 Prerequisites

- **Terraform** >= 1.0
- **Python** >= 3.8
- **AWS CLI** >= 2.0
- AWS Account with permissions for S3, Glue, and IAM

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/dea-c01-glue-crawler-single-table-enforcement-with-consistent-s3-prefix-and-schema.git
cd dea-c01-glue-crawler-single-table-enforcement-with-consistent-s3-prefix-and-schema
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region
```

### 3. Deploy Infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings
terraform init
terraform plan
terraform apply
```

### 4. Generate and Upload Sample Data

```bash
cd ../python
pip install -r requirements.txt

# Generate sample data
python generate_sample_data.py --format csv --compression gzip --num-files 5

# Upload to S3 (replace with your bucket name from terraform output)
python upload_to_s3.py --bucket YOUR_BUCKET_NAME --prefix third-party-data
```

### 5. Run the Glue Crawler

```bash
# Replace with your crawler name from terraform output
aws glue start-crawler --name YOUR_CRAWLER_NAME

# Monitor status
aws glue get-crawler --name YOUR_CRAWLER_NAME
```

### 6. Verify Single Table

```bash
# List tables (should return only ONE)
aws glue get-tables --database-name YOUR_DATABASE_NAME | jq '.TableList[].Name'
```

## 📁 Project Structure

```
.
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                # Main Terraform configuration
│   ├── variables.tf           # Input variables
│   ├── outputs.tf             # Output values
│   └── terraform.tfvars.example  # Example configuration
│
├── python/                    # Data generation and upload scripts
│   ├── generate_sample_data.py   # Generate test data
│   ├── upload_to_s3.py          # Upload files to S3
│   └── requirements.txt         # Python dependencies
│
├── docs/                      # Comprehensive documentation
│   ├── ARCHITECTURE.md        # System architecture overview
│   ├── SETUP.md               # Detailed setup guide
│   ├── MULTIPLE_TABLES_CAUSES.md  # Common pitfalls and solutions
│   ├── DEA_C01_BEST_PRACTICES.md  # Exam-aligned best practices
│   └── TROUBLESHOOTING.md     # Troubleshooting guide
│
├── map-diagram-infra.mermaid  # Universal multi-cloud infrastructure diagram
├── INFRASTRUCTURE_DIAGRAM.md  # Diagram guide and cloud component mapping
├── diagram-viewer.html        # Interactive diagram viewer (open in browser)
│
└── README.md                  # This file
```

## 🔑 Key Configuration

### Critical Settings for Single Table

**S3 Prefix Structure**:
```
✅ Correct: s3://bucket/third-party-data/file1.csv
✅ Correct: s3://bucket/third-party-data/file2.csv
❌ Wrong:   s3://bucket/data/2024/01/file1.csv
❌ Wrong:   s3://bucket/vendor-a/file1.csv
```

**Terraform Configuration**:
```hcl
# Single S3 target
s3_target {
  path = "s3://bucket/third-party-data/"
}

# Schema merge policy
schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"
  delete_behavior = "LOG"
}

# Table grouping
configuration = jsonencode({
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
  }
  Tables = {
    AddOrUpdateBehavior = "MergeNewColumns"
  }
})
```

## 📚 Documentation

### Core Documents

1. **[SETUP.md](docs/SETUP.md)** - Complete deployment guide
2. **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and components
3. **[MULTIPLE_TABLES_CAUSES.md](docs/MULTIPLE_TABLES_CAUSES.md)** - Why multiple tables occur and how to prevent it
4. **[DEA_C01_BEST_PRACTICES.md](docs/DEA_C01_BEST_PRACTICES.md)** - AWS certification best practices
5. **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
6. **[INFRASTRUCTURE_DIAGRAM.md](INFRASTRUCTURE_DIAGRAM.md)** - Universal multi-cloud architecture diagram guide

### Multi-Cloud Architecture

- **[Universal Infrastructure Diagram](INFRASTRUCTURE_DIAGRAM.md)** - Comprehensive diagram showing component mapping across AWS, GCP, and Azure
- **Interactive Viewer** - Open `diagram-viewer.html` in a browser to see the live diagram
- **Mermaid Source** - `map-diagram-infra.mermaid` contains the diagram source code

### Quick Links

- [Prerequisites and Installation](docs/SETUP.md#prerequisites)
- [Common Causes of Multiple Tables](docs/MULTIPLE_TABLES_CAUSES.md#table-of-contents)
- [Performance Optimization](docs/DEA_C01_BEST_PRACTICES.md#performance-optimization)
- [Security Best Practices](docs/DEA_C01_BEST_PRACTICES.md#security-and-compliance)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 🎓 DEA-C01 Exam Relevance

This solution covers key DEA-C01 exam domains:

- **Domain 1: Data Ingestion and Transformation** (30%)
  - Glue Crawler configuration
  - Schema detection and evolution
  - Data cataloging strategies

- **Domain 2: Data Store Management** (26%)
  - S3 data organization
  - Partitioning strategies
  - File format selection

- **Domain 3: Data Operations and Support** (22%)
  - Monitoring and logging
  - Performance optimization
  - Cost optimization

- **Domain 4: Data Security and Governance** (22%)
  - IAM roles and policies
  - Encryption at rest
  - Access control

## 🛠️ Configuration Options

### File Formats

```bash
# CSV (good for human-readable data)
python generate_sample_data.py --format csv

# JSON (good for nested structures)
python generate_sample_data.py --format json

# Parquet (best for analytics)
python generate_sample_data.py --format parquet
```

### Compression Types

```bash
# No compression
python generate_sample_data.py --compression none

# Gzip (universal, good compression)
python generate_sample_data.py --compression gzip

# Snappy (fast, Parquet only)
python generate_sample_data.py --format parquet --compression snappy
```

### Similarity Threshold

```hcl
# In terraform.tfvars
table_similarity_threshold = 0.8  # Recommended

# 0.7 = More aggressive grouping
# 0.8 = Balanced (recommended)
# 0.9 = Conservative grouping
```

## 🧪 Testing

### Test Single Table Creation

```bash
# Generate and upload test data
cd python
python generate_sample_data.py --format csv --num-files 5
python upload_to_s3.py --bucket YOUR_BUCKET --prefix third-party-data

# Run crawler
aws glue start-crawler --name YOUR_CRAWLER

# Verify result (should output: 1)
aws glue get-tables --database-name YOUR_DB | jq '.TableList | length'
```

### Test Schema Evolution

```bash
# Upload files with additional column
# Crawler should merge schemas into single table
# Verify with: aws glue get-table --database-name YOUR_DB --name TABLE_NAME
```

## 🚨 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Multiple tables created | Different S3 prefixes | Use single prefix |
| Multiple tables created | Mixed file formats | Use consistent format |
| Schema not updating | Wrong update behavior | Set UPDATE_IN_DATABASE |
| Crawler fails | IAM permissions | Check role policies |
| No data in table | Wrong S3 location | Verify path matches |

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 💰 Cost Considerations

- **Glue Crawler**: $0.44 per DPU-hour
- **S3 Storage**: ~$0.023 per GB (Standard)
- **Glue Catalog**: Free for first 1M objects/month
- **Data Scans**: Pay per GB scanned (Athena)

**Cost Optimization**:
- Use `CRAWL_NEW_FOLDERS_ONLY` recrawl policy
- Schedule crawlers appropriately (not continuous)
- Use compression to reduce storage costs
- Clean up unused tables

## 🔒 Security

- ✅ S3 encryption at rest (AES256)
- ✅ IAM least privilege access
- ✅ S3 public access blocked
- ✅ CloudTrail logging enabled
- ✅ VPC endpoint support (optional)

See [DEA_C01_BEST_PRACTICES.md](docs/DEA_C01_BEST_PRACTICES.md#security-and-compliance) for complete security guide.

## 🧹 Cleanup

To remove all resources and avoid charges:

```bash
cd terraform

# Empty S3 bucket first
aws s3 rm s3://YOUR_BUCKET_NAME --recursive

# Destroy infrastructure
terraform destroy
```

## 📖 Additional Resources

### AWS Documentation
- [AWS Glue Crawlers](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html)
- [Glue Best Practices](https://docs.aws.amazon.com/glue/latest/dg/best-practices.html)
- [DEA-C01 Exam Guide](https://aws.amazon.com/certification/certified-data-engineer-associate/)

### Related Projects
- [AWS Glue Samples](https://github.com/aws-samples/aws-glue-samples)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✍️ Authors

Created for AWS Certified Data Engineer - Associate (DEA-C01) exam preparation and real-world data engineering scenarios.

## 🌟 Acknowledgments

- AWS Glue documentation and best practices
- Terraform AWS provider community
- DEA-C01 certification study groups

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/repo/issues)
- **Documentation**: See [docs/](docs/) directory
- **AWS Support**: [AWS Support Center](https://console.aws.amazon.com/support/)

---

**⭐ If this project helped you, please star the repository!**

**🎓 Studying for DEA-C01?** Check out [DEA_C01_BEST_PRACTICES.md](docs/DEA_C01_BEST_PRACTICES.md) for exam tips!
