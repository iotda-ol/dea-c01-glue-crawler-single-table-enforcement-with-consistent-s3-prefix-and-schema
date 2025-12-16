#!/usr/bin/env python3
"""
Validate schema consistency across data files.

This script checks that all files in a directory have the same schema,
which is critical for single table enforcement in Glue crawler.

Usage:
    python validate_schema.py --directory generated_data
"""

import argparse
import csv
import json
import gzip
from pathlib import Path
from typing import Dict, List, Set


class SchemaValidator:
    """Validates schema consistency across multiple data files."""

    def __init__(self):
        self.schemas: Dict[str, Set[str]] = {}
        self.file_formats: Dict[str, str] = {}
        self.compressions: Dict[str, str] = {}

    def detect_format(self, filepath: Path) -> str:
        """Detect file format from extension."""
        suffixes = filepath.suffixes
        
        if '.csv' in suffixes:
            return 'CSV'
        elif '.json' in suffixes:
            return 'JSON'
        elif '.parquet' in suffixes:
            return 'Parquet'
        else:
            return 'Unknown'

    def detect_compression(self, filepath: Path) -> str:
        """Detect compression type from extension."""
        suffix = filepath.suffix.lower()
        
        if suffix == '.gz':
            return 'gzip'
        elif suffix == '.bz2':
            return 'bzip2'
        elif suffix == '.snappy':
            return 'snappy'
        else:
            return 'none'

    def extract_csv_schema(self, filepath: Path) -> Set[str]:
        """Extract column names from CSV file."""
        try:
            if filepath.suffix.lower() == '.gz':
                with gzip.open(filepath, 'rt') as f:
                    reader = csv.reader(f)
                    header = next(reader)
            else:
                with open(filepath, 'r') as f:
                    reader = csv.reader(f)
                    header = next(reader)
            
            return set(header)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return set()

    def extract_json_schema(self, filepath: Path) -> Set[str]:
        """Extract field names from JSON file (newline-delimited)."""
        try:
            if filepath.suffix.lower() == '.gz':
                file_obj = gzip.open(filepath, 'rt')
            else:
                file_obj = open(filepath, 'r')
            
            with file_obj:
                # Read first line only
                first_line = file_obj.readline()
                if first_line:
                    record = json.loads(first_line)
                    return set(record.keys())
            
            return set()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return set()

    def extract_parquet_schema(self, filepath: Path) -> Set[str]:
        """Extract column names from Parquet file."""
        try:
            import pandas as pd
            df = pd.read_parquet(filepath, engine='pyarrow')
            return set(df.columns)
        except ImportError:
            print(f"Warning: pandas/pyarrow not installed, skipping {filepath}")
            return set()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return set()

    def validate_file(self, filepath: Path) -> bool:
        """Validate a single file and extract its schema."""
        file_format = self.detect_format(filepath)
        compression = self.detect_compression(filepath)
        
        self.file_formats[str(filepath)] = file_format
        self.compressions[str(filepath)] = compression
        
        # Extract schema based on format
        if file_format == 'CSV':
            schema = self.extract_csv_schema(filepath)
        elif file_format == 'JSON':
            schema = self.extract_json_schema(filepath)
        elif file_format == 'Parquet':
            schema = self.extract_parquet_schema(filepath)
        else:
            print(f"Unknown format for {filepath}")
            return False
        
        if not schema:
            print(f"Could not extract schema from {filepath}")
            return False
        
        self.schemas[str(filepath)] = schema
        return True

    def validate_directory(self, directory: str) -> Dict:
        """Validate all files in directory and return results."""
        path = Path(directory)
        
        if not path.exists():
            return {"error": f"Directory {directory} does not exist"}
        
        # Find all data files
        data_files = []
        for ext in ['*.csv', '*.csv.gz', '*.json', '*.json.gz', '*.parquet']:
            data_files.extend(path.glob(ext))
        
        if not data_files:
            return {"error": f"No data files found in {directory}"}
        
        print(f"Found {len(data_files)} files to validate\n")
        
        # Validate each file
        for filepath in sorted(data_files):
            print(f"Validating {filepath.name}...", end=' ')
            if self.validate_file(filepath):
                print("✓")
            else:
                print("✗")
        
        # Analyze results
        return self.analyze_results()

    def analyze_results(self) -> Dict:
        """Analyze validation results and identify issues."""
        results = {
            "total_files": len(self.schemas),
            "is_consistent": True,
            "issues": [],
            "summary": {}
        }
        
        if not self.schemas:
            results["is_consistent"] = False
            results["issues"].append("No files validated")
            return results
        
        # Check format consistency
        formats = set(self.file_formats.values())
        results["summary"]["formats"] = list(formats)
        
        if len(formats) > 1:
            results["is_consistent"] = False
            results["issues"].append(f"Multiple file formats detected: {formats}")
            results["format_breakdown"] = {}
            for filepath, fmt in self.file_formats.items():
                if fmt not in results["format_breakdown"]:
                    results["format_breakdown"][fmt] = []
                results["format_breakdown"][fmt].append(Path(filepath).name)
        
        # Check compression consistency
        compressions = set(self.compressions.values())
        results["summary"]["compressions"] = list(compressions)
        
        if len(compressions) > 1:
            results["is_consistent"] = False
            results["issues"].append(f"Multiple compression types detected: {compressions}")
            results["compression_breakdown"] = {}
            for filepath, comp in self.compressions.items():
                if comp not in results["compression_breakdown"]:
                    results["compression_breakdown"][comp] = []
                results["compression_breakdown"][comp].append(Path(filepath).name)
        
        # Check schema consistency
        if self.schemas:
            # Get first schema as reference
            reference_schema = list(self.schemas.values())[0]
            results["summary"]["reference_schema"] = sorted(reference_schema)
            results["summary"]["column_count"] = len(reference_schema)
            
            schema_mismatches = []
            for filepath, schema in self.schemas.items():
                if schema != reference_schema:
                    missing = reference_schema - schema
                    extra = schema - reference_schema
                    schema_mismatches.append({
                        "file": Path(filepath).name,
                        "missing_columns": sorted(missing),
                        "extra_columns": sorted(extra)
                    })
            
            if schema_mismatches:
                results["is_consistent"] = False
                results["issues"].append("Schema mismatches detected")
                results["schema_mismatches"] = schema_mismatches
        
        return results


def print_results(results: Dict):
    """Print validation results in a readable format."""
    print("\n" + "=" * 60)
    print("Schema Validation Results")
    print("=" * 60)
    
    if "error" in results:
        print(f"\n❌ Error: {results['error']}")
        return
    
    print(f"\nTotal files validated: {results['total_files']}")
    
    if results["is_consistent"]:
        print("\n✅ SUCCESS! All files have consistent schema, format, and compression")
        print("\nSummary:")
        print(f"  Format: {results['summary']['formats'][0]}")
        print(f"  Compression: {results['summary']['compressions'][0]}")
        print(f"  Columns ({results['summary']['column_count']}):")
        for col in results['summary']['reference_schema']:
            print(f"    - {col}")
        
        print("\n✓ These files are ready for Glue crawler single table enforcement")
    else:
        print("\n❌ INCONSISTENCIES DETECTED!")
        print("\nIssues found:")
        for i, issue in enumerate(results['issues'], 1):
            print(f"  {i}. {issue}")
        
        if "format_breakdown" in results:
            print("\nFormat breakdown:")
            for fmt, files in results['format_breakdown'].items():
                print(f"  {fmt}:")
                for f in files:
                    print(f"    - {f}")
        
        if "compression_breakdown" in results:
            print("\nCompression breakdown:")
            for comp, files in results['compression_breakdown'].items():
                print(f"  {comp}:")
                for f in files:
                    print(f"    - {f}")
        
        if "schema_mismatches" in results:
            print("\nSchema mismatches:")
            for mismatch in results['schema_mismatches']:
                print(f"  {mismatch['file']}:")
                if mismatch['missing_columns']:
                    print(f"    Missing: {', '.join(mismatch['missing_columns'])}")
                if mismatch['extra_columns']:
                    print(f"    Extra: {', '.join(mismatch['extra_columns'])}")
        
        print("\n⚠️  These files will likely create multiple tables in Glue")
        print("Fix issues before running crawler for single table enforcement")
    
    print("\n" + "=" * 60)


def main():
    """Main function to handle CLI arguments and run validation."""
    parser = argparse.ArgumentParser(
        description="Validate schema consistency across data files"
    )
    parser.add_argument(
        "--directory",
        default="generated_data",
        help="Directory containing data files to validate (default: generated_data)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Run validation
    validator = SchemaValidator()
    results = validator.validate_directory(args.directory)

    # Print results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)

    # Exit with appropriate code
    if "error" in results or not results.get("is_consistent", False):
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
