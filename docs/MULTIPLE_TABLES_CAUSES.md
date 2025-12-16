# Common Causes of Multiple Tables in Glue Crawler

When configuring AWS Glue Crawlers, you may unexpectedly end up with multiple tables instead of the single table you intended. This document explains the common causes and how to prevent them.

## Table of Contents
1. [Inconsistent S3 Prefix Structure](#1-inconsistent-s3-prefix-structure)
2. [Different File Formats](#2-different-file-formats)
3. [Different Compression Types](#3-different-compression-types)
4. [Schema Incompatibilities](#4-schema-incompatibilities)
5. [Date-Based or Hierarchical Partitions](#5-date-based-or-hierarchical-partitions)
6. [Multiple Crawler Targets](#6-multiple-crawler-targets)
7. [Table Grouping Configuration](#7-table-grouping-configuration)
8. [Similarity Threshold Too High](#8-similarity-threshold-too-high)

---

## 1. Inconsistent S3 Prefix Structure

### ❌ Problem
Files stored in different S3 prefixes (folders) are treated as separate datasets.

### Example of Multiple Tables Created
```
s3://my-bucket/data/customer-orders/file1.csv
s3://my-bucket/data/product-orders/file2.csv
s3://my-bucket/orders-archive/file3.csv
```
**Result**: 3 tables created: `customer_orders`, `product_orders`, `orders_archive`

### ✅ Solution
Store all files under a single, consistent prefix:
```
s3://my-bucket/third-party-data/file1.csv
s3://my-bucket/third-party-data/file2.csv
s3://my-bucket/third-party-data/file3.csv
```
**Result**: 1 table created: `third_party_data`

### Terraform Configuration
```hcl
s3_target {
  path = "s3://${aws_s3_bucket.data_lake.id}/third-party-data/"
}
```

---

## 2. Different File Formats

### ❌ Problem
Mixing different file formats (CSV, JSON, Parquet) causes Glue to create separate tables for each format.

### Example of Multiple Tables Created
```
s3://my-bucket/data/transactions.csv
s3://my-bucket/data/transactions.json
s3://my-bucket/data/transactions.parquet
```
**Result**: 3 tables created: `transactions_csv`, `transactions_json`, `transactions_parquet`

### ✅ Solution
Use a single file format consistently across all files:

**Option 1: CSV only**
```
s3://my-bucket/data/file1.csv
s3://my-bucket/data/file2.csv
s3://my-bucket/data/file3.csv
```

**Option 2: Parquet only (recommended for analytics)**
```
s3://my-bucket/data/file1.parquet
s3://my-bucket/data/file2.parquet
s3://my-bucket/data/file3.parquet
```

### Implementation
```python
# Generate consistent format
python generate_sample_data.py --format csv --num-files 5
```

---

## 3. Different Compression Types

### ❌ Problem
Mixing compression types (gzip, snappy, none) for the same format can cause table splits.

### Example of Multiple Tables Created
```
s3://my-bucket/data/file1.csv.gz    (gzip)
s3://my-bucket/data/file2.csv       (no compression)
s3://my-bucket/data/file3.csv.snappy (snappy)
```
**Result**: Up to 3 tables created based on compression type

### ✅ Solution
Use the same compression consistently:

**Option 1: All gzip**
```
s3://my-bucket/data/file1.csv.gz
s3://my-bucket/data/file2.csv.gz
s3://my-bucket/data/file3.csv.gz
```

**Option 2: All uncompressed**
```
s3://my-bucket/data/file1.csv
s3://my-bucket/data/file2.csv
s3://my-bucket/data/file3.csv
```

### Implementation
```python
# Generate with consistent compression
python generate_sample_data.py --format csv --compression gzip --num-files 5
```

---

## 4. Schema Incompatibilities

### ❌ Problem
Files with significantly different schemas are treated as separate datasets.

### Example of Multiple Tables Created

**File 1: orders.csv**
```csv
order_id,customer_id,amount,date
1001,C001,99.99,2024-01-01
```

**File 2: returns.csv**
```csv
return_id,product_id,reason,status
R001,P001,damaged,approved
```

**Result**: 2 tables created: `orders` and `returns`

### ✅ Solution
Ensure all files share the same base schema:

**All files: transactions.csv**
```csv
transaction_id,customer_id,product_name,quantity,unit_price,total_amount,transaction_date,status
TXN-001,CUST-1001,Laptop,1,999.99,999.99,2024-01-01,completed
TXN-002,CUST-1002,Mouse,2,29.99,59.98,2024-01-02,completed
```

### Schema Evolution
If you need to add columns over time, configure the crawler to merge schemas:

```hcl
schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"  # Add new columns
  delete_behavior = "LOG"                  # Keep deleted columns
}

configuration = jsonencode({
  Tables = {
    AddOrUpdateBehavior = "MergeNewColumns"
  }
})
```

---

## 5. Date-Based or Hierarchical Partitions

### ❌ Problem
Using date-based folder structures at the crawler target level causes multiple tables.

### Example of Multiple Tables Created
```
s3://my-bucket/data/2024/01/01/file1.csv
s3://my-bucket/data/2024/01/02/file2.csv
s3://my-bucket/data/2024/02/01/file3.csv
```

If crawler targets `s3://my-bucket/data/`, it may create separate tables for each date.

### ✅ Solution

**Option 1: Single prefix without date folders**
```
s3://my-bucket/data/file-2024-01-01.csv
s3://my-bucket/data/file-2024-01-02.csv
s3://my-bucket/data/file-2024-02-01.csv
```

**Option 2: Configure Hive-style partitions AFTER single table creation**
First, create single table, then add partitions:
```
s3://my-bucket/data/year=2024/month=01/day=01/file1.csv
s3://my-bucket/data/year=2024/month=01/day=02/file2.csv
```

Configure crawler to recognize partitions:
```hcl
configuration = jsonencode({
  Grouping = {
    TableLevelConfiguration = {
      PartitionKey = "year,month,day"
    }
  }
})
```

---

## 6. Multiple Crawler Targets

### ❌ Problem
Configuring multiple S3 targets in a single crawler can lead to multiple tables.

### Example Configuration
```hcl
s3_target {
  path = "s3://my-bucket/customer-data/"
}

s3_target {
  path = "s3://my-bucket/order-data/"
}
```
**Result**: 2 tables created: `customer_data` and `order_data`

### ✅ Solution
Use a single S3 target with one consistent prefix:

```hcl
s3_target {
  path = "s3://my-bucket/business-data/"
}
```

Then place all files under that single prefix.

---

## 7. Table Grouping Configuration

### ❌ Problem
Missing or incorrect table grouping configuration prevents schema combining.

### Example of Missing Configuration
```hcl
# No configuration specified - uses default behavior
resource "aws_glue_crawler" "default" {
  name = "my-crawler"
  # ... other settings
}
```
**Result**: May create separate tables for minor schema differences

### ✅ Solution
Explicitly configure table grouping:

```hcl
configuration = jsonencode({
  Version = 1.0
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
  }
  Tables = {
    AddOrUpdateBehavior = "MergeNewColumns"
  }
})
```

---

## 8. Similarity Threshold Too High

### ❌ Problem
When the similarity threshold is set too high (e.g., 0.95), even minor schema differences cause table splits.

### Example
```hcl
# Too strict - requires 95% schema similarity
table_similarity_threshold = 0.95
```

**Scenario**: Files with 8/10 matching columns (80% similarity) will create separate tables.

### ✅ Solution
Use a moderate threshold that allows for minor variations:

```hcl
# Recommended: allows reasonable schema variation
table_similarity_threshold = 0.8
```

**Threshold Guidelines**:
- **0.7**: Aggressive grouping, may combine different datasets
- **0.8**: Recommended balance
- **0.9**: Conservative, requires high similarity
- **1.0**: Exact match only (almost always creates multiple tables)

---

## Decision Matrix: Single Table vs. Multiple Tables

| Scenario | Single Table? | Notes |
|----------|---------------|-------|
| Same format, same compression, same schema | ✅ Yes | Ideal case |
| Same format, different compression | ⚠️ Maybe | Depends on configuration |
| Different formats (CSV + JSON) | ❌ No | Will create separate tables |
| Same schema with 1-2 extra columns | ✅ Yes | With MergeNewColumns |
| Completely different schemas | ❌ No | Intentionally separate datasets |
| Same prefix, same format | ✅ Yes | Recommended approach |
| Different S3 prefixes | ❌ No | Location-based grouping |
| Date-based folders as target | ⚠️ Maybe | Use Hive partitioning instead |

---

## Troubleshooting Checklist

When you encounter multiple tables, check:

- [ ] Are all files under the **same S3 prefix**?
- [ ] Are all files using the **same file format** (CSV, JSON, or Parquet)?
- [ ] Are all files using the **same compression** (all gzip, all none, etc.)?
- [ ] Do all files have a **compatible schema** (same core columns)?
- [ ] Is the crawler configured with **CombineCompatibleSchemas**?
- [ ] Is the table similarity threshold set to **0.8 or lower**?
- [ ] Are you using **MergeNewColumns** for schema updates?
- [ ] Do you have **only one S3 target** configured?
- [ ] Are there any **date-based folders** in the target path?
- [ ] Are exclusion patterns **not** filtering out valid data files?

---

## Prevention Best Practices

### 1. Standardize Data Format Early
Choose one format (CSV, JSON, or Parquet) and enforce it for all ingestion.

### 2. Validate Before Upload
```python
# Validate schema consistency
python validate_schema.py --directory generated_data/
```

### 3. Use Single Prefix Strategy
```
✅ Good: s3://bucket/data/
❌ Bad:  s3://bucket/data/2024/
❌ Bad:  s3://bucket/{customer_name}/data/
```

### 4. Configure Crawler Properly
```hcl
# Essential settings for single table
configuration = jsonencode({
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
  }
  Tables = {
    AddOrUpdateBehavior = "MergeNewColumns"
  }
})

schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"
  delete_behavior = "LOG"
}
```

### 5. Test with Sample Data
Always test crawler configuration with sample data before production deployment.

---

## Summary

Creating a single table in AWS Glue requires:

1. **Consistent S3 prefix** - one location for all files
2. **Consistent file format** - CSV, JSON, or Parquet (pick one)
3. **Consistent compression** - gzip, snappy, or none (pick one)
4. **Compatible schemas** - same core columns across files
5. **Proper crawler configuration** - CombineCompatibleSchemas enabled
6. **Appropriate threshold** - 0.8 recommended for balance
7. **Schema merge policy** - MergeNewColumns for evolution

Following these practices ensures your Glue crawler creates and maintains a single table, simplifying queries and analytics.
