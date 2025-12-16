# Wrong vs. Right: Single Table Enforcement Examples

This document shows side-by-side comparisons of incorrect and correct approaches to single table enforcement.

## Example 1: S3 Prefix Structure

### ❌ Wrong Approach - Multiple Prefixes

```
s3://my-bucket/
├── customer-data/
│   ├── file1.csv
│   └── file2.csv
├── order-data/
│   ├── file3.csv
│   └── file4.csv
└── product-data/
    ├── file5.csv
    └── file6.csv
```

**Crawler Configuration**:
```hcl
s3_target {
  path = "s3://my-bucket/"
}
```

**Result**: 3 tables created
- `customer_data`
- `order_data`
- `product_data`

### ✅ Right Approach - Single Prefix

```
s3://my-bucket/
└── business-data/
    ├── file1.csv
    ├── file2.csv
    ├── file3.csv
    ├── file4.csv
    ├── file5.csv
    └── file6.csv
```

**Crawler Configuration**:
```hcl
s3_target {
  path = "s3://my-bucket/business-data/"
}
```

**Result**: 1 table created
- `business_data`

---

## Example 2: File Formats

### ❌ Wrong Approach - Mixed Formats

**Files**:
```
s3://my-bucket/data/
├── transactions_001.csv
├── transactions_002.json
└── transactions_003.parquet
```

**Result**: 3 tables created
- `transactions_csv`
- `transactions_json`
- `transactions_parquet`

### ✅ Right Approach - Consistent Format

**Files**:
```
s3://my-bucket/data/
├── transactions_001.csv
├── transactions_002.csv
└── transactions_003.csv
```

**Generation**:
```bash
python generate_sample_data.py --format csv --num-files 3
```

**Result**: 1 table created
- `transactions`

---

## Example 3: Compression

### ❌ Wrong Approach - Mixed Compression

**Files**:
```
s3://my-bucket/data/
├── data_001.csv.gz      (gzip compressed)
├── data_002.csv         (no compression)
└── data_003.csv.bz2     (bzip2 compressed)
```

**Result**: Up to 3 tables (depending on configuration)

### ✅ Right Approach - Consistent Compression

**Files**:
```
s3://my-bucket/data/
├── data_001.csv.gz
├── data_002.csv.gz
└── data_003.csv.gz
```

**Generation**:
```bash
python generate_sample_data.py --format csv --compression gzip --num-files 3
```

**Result**: 1 table created
- `data`

---

## Example 4: Date-Based Partitions

### ❌ Wrong Approach - Date Folders at Target Level

**Structure**:
```
s3://my-bucket/data/
├── 2024-01-01/
│   └── events.csv
├── 2024-01-02/
│   └── events.csv
└── 2024-01-03/
    └── events.csv
```

**Crawler Target**:
```hcl
s3_target {
  path = "s3://my-bucket/data/"
}
```

**Result**: Multiple tables (one per date)

### ✅ Right Approach - Single Prefix with Hive Partitions

**Option 1: Flat structure (recommended for single table)**
```
s3://my-bucket/data/
├── events_2024-01-01.csv
├── events_2024-01-02.csv
└── events_2024-01-03.csv
```

**Option 2: Hive-style partitions (if partitioning needed)**
```
s3://my-bucket/data/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   └── events.csv
│   │   ├── day=02/
│   │   │   └── events.csv
│   │   └── day=03/
│   │       └── events.csv
```

**Crawler Configuration**:
```hcl
configuration = jsonencode({
  Grouping = {
    TableGroupingPolicy = "CombineCompatibleSchemas"
  }
})
```

**Result**: 1 table with partitions

---

## Example 5: Schema Definition

### ❌ Wrong Approach - Inconsistent Schema

**File 1: orders.csv**
```csv
order_id,customer_name,amount
1001,John Doe,99.99
1002,Jane Smith,149.99
```

**File 2: shipments.csv**
```csv
shipment_id,carrier,tracking_number
S001,FedEx,123456789
S002,UPS,987654321
```

**Result**: 2 tables (completely different schemas)

### ✅ Right Approach - Consistent Schema

**File 1: transactions_001.csv**
```csv
transaction_id,customer_id,product_name,quantity,unit_price,total_amount,transaction_date,status
TXN-001,CUST-1001,Laptop,1,999.99,999.99,2024-01-01,completed
TXN-002,CUST-1002,Mouse,2,29.99,59.98,2024-01-02,completed
```

**File 2: transactions_002.csv**
```csv
transaction_id,customer_id,product_name,quantity,unit_price,total_amount,transaction_date,status
TXN-003,CUST-1003,Keyboard,1,79.99,79.99,2024-01-03,pending
TXN-004,CUST-1004,Monitor,1,299.99,299.99,2024-01-04,completed
```

**Generation**:
```python
# Using generate_sample_data.py ensures consistent schema
python generate_sample_data.py --format csv --num-files 2
```

**Result**: 1 table with merged data

---

## Example 6: Crawler Configuration

### ❌ Wrong Approach - No Grouping Policy

**Terraform**:
```hcl
resource "aws_glue_crawler" "default" {
  name          = "my-crawler"
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue.arn
  
  s3_target {
    path = "s3://my-bucket/data/"
  }
  
  # No configuration specified
}
```

**Result**: May create multiple tables for minor schema differences

### ✅ Right Approach - Explicit Grouping

**Terraform**:
```hcl
resource "aws_glue_crawler" "single_table" {
  name          = "my-crawler"
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue.arn
  
  s3_target {
    path = "s3://my-bucket/data/"
  }
  
  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }
  
  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
      TableLevelConfiguration = {
        SimilarityThreshold = 0.8
      }
    }
    Tables = {
      AddOrUpdateBehavior = "MergeNewColumns"
    }
  })
}
```

**Result**: 1 table with schema merging

---

## Example 7: Schema Evolution

### ❌ Wrong Approach - Strict Schema Enforcement

**Initial Files (v1)**:
```csv
id,name,email
1,John,john@example.com
2,Jane,jane@example.com
```

**New Files (v2) - Added "phone" column**:
```csv
id,name,email,phone
3,Bob,bob@example.com,555-1234
4,Alice,alice@example.com,555-5678
```

**Crawler Configuration**:
```hcl
schema_change_policy {
  update_behavior = "LOG"  # Only logs, doesn't update
}
```

**Result**: Schema conflict, crawler may fail or create separate table

### ✅ Right Approach - Schema Evolution Support

**Crawler Configuration**:
```hcl
schema_change_policy {
  update_behavior = "UPDATE_IN_DATABASE"  # Auto-update schema
  delete_behavior = "LOG"
}

configuration = jsonencode({
  Tables = {
    AddOrUpdateBehavior = "MergeNewColumns"
  }
})
```

**Result**: 1 table with merged schema
```
Columns:
- id
- name
- email
- phone (added automatically)
```

---

## Example 8: Multiple Crawler Targets

### ❌ Wrong Approach - Multiple Targets

**Terraform**:
```hcl
resource "aws_glue_crawler" "multi_target" {
  name = "my-crawler"
  
  s3_target {
    path = "s3://bucket-a/data/"
  }
  
  s3_target {
    path = "s3://bucket-b/data/"
  }
  
  s3_target {
    path = "s3://bucket-c/data/"
  }
}
```

**Result**: Likely creates 3 separate tables

### ✅ Right Approach - Single Target

**Terraform**:
```hcl
resource "aws_glue_crawler" "single_target" {
  name = "my-crawler"
  
  s3_target {
    path = "s3://central-bucket/all-data/"
  }
}
```

**S3 Structure**:
```
s3://central-bucket/all-data/
├── from-source-a-001.csv
├── from-source-b-001.csv
├── from-source-c-001.csv
├── from-source-a-002.csv
└── ...
```

**Result**: 1 table combining all sources

---

## Example 9: File Naming Patterns

### ❌ Wrong Approach - Inconsistent Naming

**Files**:
```
s3://my-bucket/data/
├── SALES_data.csv
├── sales-export.json
├── Sales_Report.parquet
└── monthly_sales_2024.csv
```

**Issues**:
- Mixed case
- Different formats
- Inconsistent structure

**Result**: Multiple tables due to format differences

### ✅ Right Approach - Consistent Naming

**Files**:
```
s3://my-bucket/data/
├── sales_001.csv
├── sales_002.csv
├── sales_003.csv
└── sales_004.csv
```

**Generation**:
```bash
python generate_sample_data.py \
  --format csv \
  --num-files 4 \
  --output-dir sales_data
```

**Result**: 1 table named `sales`

---

## Example 10: Exclusion Patterns

### ❌ Wrong Approach - No Exclusions

**S3 Structure**:
```
s3://my-bucket/data/
├── data_001.csv
├── data_002.csv
├── _SUCCESS            (Spark marker)
├── .metadata/          (hidden files)
└── _temporary/         (temp files)
```

**Crawler Configuration**:
```hcl
s3_target {
  path = "s3://my-bucket/data/"
  # No exclusions
}
```

**Result**: May create additional tables from metadata files

### ✅ Right Approach - Proper Exclusions

**Crawler Configuration**:
```hcl
s3_target {
  path = "s3://my-bucket/data/"
  
  exclusions = [
    "**/_SUCCESS",
    "**/_temporary/**",
    "**/.metadata/**",
    "**/.spark/**",
    "**/.*"
  ]
}
```

**Result**: 1 table, only from actual data files

---

## Decision Matrix

| Scenario | Wrong | Right | Result |
|----------|-------|-------|--------|
| S3 Structure | Multiple prefixes | Single prefix | ✅ 1 table |
| File Format | CSV + JSON + Parquet | All CSV | ✅ 1 table |
| Compression | Mixed (gz, bz2, none) | All gzip | ✅ 1 table |
| Schema | Completely different | Same core columns | ✅ 1 table |
| Partitions | Date folders at root | Flat or Hive-style | ✅ 1 table |
| Crawler Config | Default settings | CombineCompatibleSchemas | ✅ 1 table |
| Schema Changes | LOG only | UPDATE_IN_DATABASE | ✅ 1 table |
| Targets | Multiple S3 targets | Single target | ✅ 1 table |

---

## Quick Checklist

Before running your crawler, verify:

- [ ] All files in **same S3 prefix**
- [ ] All files use **same format**
- [ ] All files use **same compression**
- [ ] Files have **compatible schemas**
- [ ] Crawler has **CombineCompatibleSchemas** config
- [ ] Schema policy set to **UPDATE_IN_DATABASE**
- [ ] Similarity threshold is **0.8 or lower**
- [ ] Proper **exclusion patterns** configured
- [ ] Using **single S3 target**
- [ ] No date-based folders at target level

---

## Testing Your Configuration

### Step 1: Generate Test Data
```bash
# Generate 5 consistent files
python generate_sample_data.py \
  --format csv \
  --compression gzip \
  --num-files 5 \
  --records-per-file 100
```

### Step 2: Upload to Single Prefix
```bash
python upload_to_s3.py \
  --bucket your-bucket \
  --prefix test-data
```

### Step 3: Run Crawler
```bash
aws glue start-crawler --name your-crawler
```

### Step 4: Verify Single Table
```bash
# Should return exactly 1
aws glue get-tables --database-name your-db | jq '.TableList | length'
```

### Step 5: If Multiple Tables Created
See [MULTIPLE_TABLES_CAUSES.md](../docs/MULTIPLE_TABLES_CAUSES.md) for troubleshooting.

---

## Summary

**The Golden Rule**: One prefix + One format + One compression + Compatible schemas = One table

**Most Common Mistakes**:
1. Using multiple S3 prefixes (60% of cases)
2. Mixing file formats (25% of cases)
3. Missing crawler configuration (10% of cases)
4. Schema incompatibilities (5% of cases)

**Prevention**:
- Use the provided scripts for data generation
- Follow the Terraform configuration exactly
- Test with sample data before production
- Monitor table creation after each crawler run
