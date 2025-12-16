#!/usr/bin/env python3
"""
Generate sample data with consistent schema for testing Glue crawler single table enforcement.

This script creates sample data files with:
- Consistent schema across all files
- Same file format (CSV, JSON, or Parquet)
- Same compression type (gzip, snappy, or none)
- Proper structure for single table creation

Usage:
    python generate_sample_data.py --format csv --compression gzip --num-files 3
"""

import argparse
import json
import os
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import random
import csv


class SampleDataGenerator:
    """Generates sample data with consistent schema."""

    # Consistent schema definition - CRITICAL for single table enforcement
    SCHEMA = {
        "transaction_id": str,
        "customer_id": str,
        "product_name": str,
        "quantity": int,
        "unit_price": float,
        "total_amount": float,
        "transaction_date": str,
        "status": str,
    }

    # Sample data values
    PRODUCTS = [
        "Laptop", "Mouse", "Keyboard", "Monitor", "Headphones",
        "Webcam", "USB Cable", "HDMI Cable", "Desk Chair", "Desk Lamp"
    ]
    STATUSES = ["completed", "pending", "cancelled", "refunded"]

    def __init__(self, output_dir: str = "generated_data"):
        """Initialize the data generator.
        
        Args:
            output_dir: Directory to store generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def generate_record(self, record_id: int) -> dict:
        """Generate a single data record with consistent schema.
        
        Args:
            record_id: Unique identifier for the record
            
        Returns:
            Dictionary containing record data
        """
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(10.0, 500.0), 2)
        total_amount = round(quantity * unit_price, 2)
        
        # Generate date within last 30 days
        days_ago = random.randint(0, 30)
        transaction_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        return {
            "transaction_id": f"TXN-{record_id:08d}",
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "product_name": random.choice(self.PRODUCTS),
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "transaction_date": transaction_date,
            "status": random.choice(self.STATUSES),
        }

    def generate_csv(self, filename: str, num_records: int = 100, compression: str = None) -> str:
        """Generate CSV file with sample data.
        
        Args:
            filename: Name of the output file (without extension)
            num_records: Number of records to generate
            compression: Compression type ('gzip' or None)
            
        Returns:
            Path to the generated file
        """
        if compression == "gzip":
            filepath = self.output_dir / f"{filename}.csv.gz"
            file_obj = gzip.open(filepath, 'wt', newline='')
        else:
            filepath = self.output_dir / f"{filename}.csv"
            file_obj = open(filepath, 'w', newline='')

        try:
            writer = csv.DictWriter(file_obj, fieldnames=self.SCHEMA.keys())
            writer.writeheader()
            
            for i in range(num_records):
                writer.writerow(self.generate_record(i))
                
            print(f"Generated: {filepath} ({num_records} records)")
            return str(filepath)
        finally:
            file_obj.close()

    def generate_json(self, filename: str, num_records: int = 100, compression: str = None) -> str:
        """Generate JSON file with sample data (newline-delimited JSON).
        
        Args:
            filename: Name of the output file (without extension)
            num_records: Number of records to generate
            compression: Compression type ('gzip' or None)
            
        Returns:
            Path to the generated file
        """
        if compression == "gzip":
            filepath = self.output_dir / f"{filename}.json.gz"
            file_obj = gzip.open(filepath, 'wt')
        else:
            filepath = self.output_dir / f"{filename}.json"
            file_obj = open(filepath, 'w')

        try:
            for i in range(num_records):
                record = self.generate_record(i)
                json.dump(record, file_obj)
                file_obj.write('\n')
                
            print(f"Generated: {filepath} ({num_records} records)")
            return str(filepath)
        finally:
            file_obj.close()

    def generate_parquet(self, filename: str, num_records: int = 100, compression: str = None) -> str:
        """Generate Parquet file with sample data.
        
        Note: Requires pandas and pyarrow libraries
        
        Args:
            filename: Name of the output file (without extension)
            num_records: Number of records to generate
            compression: Compression type ('snappy', 'gzip', or None)
            
        Returns:
            Path to the generated file
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Parquet generation. Install with: pip install pandas pyarrow")

        records = [self.generate_record(i) for i in range(num_records)]
        df = pd.DataFrame(records)
        
        # Ensure correct data types match schema
        df['quantity'] = df['quantity'].astype('int64')
        df['unit_price'] = df['unit_price'].astype('float64')
        df['total_amount'] = df['total_amount'].astype('float64')
        
        filepath = self.output_dir / f"{filename}.parquet"
        compression_type = compression if compression else None
        
        df.to_parquet(filepath, index=False, compression=compression_type)
        print(f"Generated: {filepath} ({num_records} records)")
        return str(filepath)


def main():
    """Main function to handle CLI arguments and generate data."""
    parser = argparse.ArgumentParser(
        description="Generate sample data for testing Glue crawler single table enforcement"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "parquet"],
        default="csv",
        help="Output file format (default: csv)"
    )
    parser.add_argument(
        "--compression",
        choices=["gzip", "snappy", "none"],
        default="none",
        help="Compression type (default: none). Note: snappy only works with parquet"
    )
    parser.add_argument(
        "--num-files",
        type=int,
        default=3,
        help="Number of files to generate (default: 3)"
    )
    parser.add_argument(
        "--records-per-file",
        type=int,
        default=100,
        help="Number of records per file (default: 100)"
    )
    parser.add_argument(
        "--output-dir",
        default="generated_data",
        help="Output directory for generated files (default: generated_data)"
    )

    args = parser.parse_args()

    # Validate compression for format
    if args.format != "parquet" and args.compression == "snappy":
        print("Warning: Snappy compression only works with Parquet format. Using gzip instead.")
        args.compression = "gzip"

    # Set compression to None if specified as "none"
    compression = None if args.compression == "none" else args.compression

    # Generate data
    generator = SampleDataGenerator(args.output_dir)
    
    print(f"\nGenerating {args.num_files} {args.format.upper()} files...")
    print(f"Format: {args.format}, Compression: {args.compression}, Records per file: {args.records_per_file}")
    print(f"Output directory: {args.output_dir}\n")

    generated_files = []
    for i in range(args.num_files):
        filename = f"sample_data_{i+1:03d}"
        
        if args.format == "csv":
            filepath = generator.generate_csv(filename, args.records_per_file, compression)
        elif args.format == "json":
            filepath = generator.generate_json(filename, args.records_per_file, compression)
        elif args.format == "parquet":
            filepath = generator.generate_parquet(filename, args.records_per_file, compression)
        
        generated_files.append(filepath)

    print(f"\n✓ Successfully generated {len(generated_files)} files")
    print(f"\nKey points for single table enforcement:")
    print("  1. All files use the SAME schema")
    print("  2. All files use the SAME format ({})".format(args.format.upper()))
    print("  3. All files use the SAME compression ({})".format(args.compression.upper()))
    print("  4. Files should be uploaded to the SAME S3 prefix")
    print("\nNext steps:")
    print(f"  1. Upload files to S3: python upload_to_s3.py --bucket YOUR_BUCKET --prefix third-party-data")
    print(f"  2. Run the Glue crawler")
    print(f"  3. Verify only ONE table was created in the Glue Data Catalog")


if __name__ == "__main__":
    main()
