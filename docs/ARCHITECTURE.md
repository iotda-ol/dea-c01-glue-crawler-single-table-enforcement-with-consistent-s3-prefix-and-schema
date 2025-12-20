# Architecture Overview

## System Architecture

This solution demonstrates how to configure AWS Glue Crawlers to create a single table from third-party data stored in Amazon S3, ensuring consistent schema, file format, and compression across all objects.

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│                                                                  │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │   S3 Bucket    │         │   IAM Role       │               │
│  │                │         │   (Glue Crawler) │               │
│  │  third-party-  │◄────────┤                  │               │
│  │    data/       │  Read   │  - S3 Access     │               │
│  │    ├─file1.csv │         │  - Glue Service  │               │
│  │    ├─file2.csv │         └────────┬─────────┘               │
│  │    └─file3.csv │                  │                          │
│  └────────┬───────┘                  │ Assumes                  │
│           │                          │                          │
│           │ Crawl                    │                          │
│           │                          │                          │
│  ┌────────▼───────────────────────────▼─────────────┐          │
│  │         AWS Glue Crawler                          │          │
│  │                                                    │          │
│  │  Configuration:                                   │          │
│  │  • Single S3 prefix target                        │          │
│  │  • CombineCompatibleSchemas                       │          │
│  │  • MergeNewColumns behavior                       │          │
│  │  • Consistent format/compression enforcement      │          │
│  └────────────────────┬──────────────────────────────┘          │
│                       │                                          │
│                       │ Creates/Updates                          │
│                       │                                          │
│  ┌────────────────────▼──────────────────────┐                  │
│  │   AWS Glue Data Catalog                   │                  │
│  │                                            │                  │
│  │   Database: glue_single_table_dev_db      │                  │
│  │   └─ Table: third_party_data (SINGLE)     │                  │
│  │      ├─ Schema                             │                  │
│  │      ├─ Format: CSV                        │                  │
│  │      ├─ Compression: GZIP                  │                  │
│  │      └─ Location: s3://.../third-party-data/│                  │
│  └───────────────────────────────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. S3 Bucket (Data Lake)
- **Purpose**: Store third-party data with consistent structure
- **Features**:
  - Versioning enabled for data protection
  - Server-side encryption (AES256)
  - Public access blocked
  - Consistent prefix structure

### 2. S3 Prefix Structure
- **Critical Design Element**: Single, consistent prefix for all data files
- **Structure**: `s3://bucket-name/third-party-data/`
- **Why it matters**: 
  - Glue crawler groups files by location
  - Multiple prefixes = multiple tables
  - Date-based prefixes (e.g., `/2024/01/`) cause table proliferation

### 3. IAM Role
- **Purpose**: Grant Glue crawler access to S3 and Glue services
- **Policies**:
  - AWSGlueServiceRole (managed policy)
  - Custom S3 read/write permissions
  - CloudWatch Logs permissions (from managed policy)

### 4. Glue Database
- **Purpose**: Container for table metadata
- **Naming**: `{project_name}_{environment}_db`
- **Scope**: Single database for related datasets

### 5. Glue Crawler
- **Purpose**: Discover schema and create/update table metadata
- **Key Configuration**:
  - **S3 Target**: Single prefix path
  - **Schema Change Policy**: 
    - Update: `UPDATE_IN_DATABASE` (add new columns)
    - Delete: `LOG` (don't remove columns)
  - **Recrawl Policy**: `CRAWL_NEW_FOLDERS_ONLY` (efficiency)
  - **Table Grouping**: `CombineCompatibleSchemas`
  - **Similarity Threshold**: 0.8 (balance between grouping and accuracy)

## Data Flow

1. **Data Ingestion**:
   - Third-party data arrives in consistent format (CSV, JSON, or Parquet)
   - All files use same compression (gzip, snappy, or none)
   - Files uploaded to single S3 prefix

2. **Crawler Execution**:
   - Crawler scans S3 prefix
   - Reads file samples to infer schema
   - Detects format and compression
   - Groups compatible files into single table

3. **Catalog Update**:
   - Creates or updates single table in Glue Data Catalog
   - Schema merges new columns if detected
   - Table metadata includes:
     - Column names and types
     - File format and compression
     - Storage location
     - Statistics

4. **Query Access**:
   - Table queryable via Athena, EMR, Redshift Spectrum
   - Single table simplifies queries and analytics
   - Consistent schema ensures reliable results

## Key Design Decisions

### Single Prefix Strategy
**Decision**: Use one consistent S3 prefix for all data files  
**Rationale**: Prevents table proliferation caused by location-based grouping  
**Alternative Rejected**: Date-based partitioning at prefix level (causes multiple tables)

### Schema Merge Policy
**Decision**: `MergeNewColumns` with `UPDATE_IN_DATABASE`  
**Rationale**: Accommodates schema evolution while maintaining single table  
**Alternative Rejected**: Strict schema validation (too rigid for third-party data)

### Similarity Threshold
**Decision**: 0.8 (moderate grouping)  
**Rationale**: Balances aggressive grouping with schema accuracy  
**Tuning**: Lower (0.7) for more grouping, higher (0.9) for stricter matching

### Delete Behavior
**Decision**: `LOG` deleted columns  
**Rationale**: Preserves historical data, prevents accidental loss  
**Alternative**: `DELETE_FROM_DATABASE` (risky in production)

## Scalability Considerations

### File Count
- **Supported**: Thousands to millions of files
- **Performance**: Crawler samples files (doesn't read all)
- **Optimization**: Use `CRAWL_NEW_FOLDERS_ONLY` for incremental scans

### Data Volume
- **Supported**: Petabyte-scale datasets
- **Performance**: Catalog operations independent of data size
- **Note**: Query performance depends on file format and compression

### Schema Evolution
- **Supported**: Adding new columns over time
- **Limitation**: Column type changes may require manual intervention
- **Best Practice**: Maintain backward-compatible schema changes

## Security

### Data Encryption
- **At Rest**: S3 server-side encryption (AES256)
- **In Transit**: HTTPS for all AWS API calls
- **Option**: Can use KMS for additional key management

### Access Control
- **S3**: Bucket policies and IAM roles
- **Glue**: Resource-based policies
- **Principle**: Least privilege access

### Compliance
- **Logging**: CloudTrail for API calls
- **Monitoring**: CloudWatch for crawler execution
- **Audit**: S3 access logs (optional)

## Cost Optimization

### Crawler Execution
- **Cost Factor**: DPU-hours (Data Processing Units)
- **Optimization**: 
  - Use scheduled runs vs. continuous
  - Enable `CRAWL_NEW_FOLDERS_ONLY`
  - Exclude unnecessary file patterns

### Data Storage
- **Cost Factor**: S3 storage and requests
- **Optimization**:
  - Use compression (reduces storage 50-90%)
  - Lifecycle policies for old data
  - Intelligent-Tiering for variable access

### Catalog Storage
- **Cost**: Free for first 1M objects/month
- **Optimization**: Single table reduces metadata overhead vs. multiple tables
