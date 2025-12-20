#!/usr/bin/env python3
"""
Upload generated sample data to S3 with proper prefix structure.

This script ensures files are uploaded to a consistent S3 prefix,
which is critical for single table enforcement in Glue crawler.

Usage:
    python upload_to_s3.py --bucket my-bucket --prefix third-party-data
"""

import argparse
import sys
from pathlib import Path
from typing import List
import os


def upload_files_to_s3(bucket: str, prefix: str, files: List[str], aws_profile: str = None):
    """Upload files to S3 with consistent prefix structure.
    
    Args:
        bucket: S3 bucket name
        prefix: S3 prefix (folder) for data files
        files: List of file paths to upload
        aws_profile: AWS profile name (optional)
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("Error: boto3 is required. Install with: pip install boto3")
        sys.exit(1)

    # Initialize S3 client
    session_kwargs = {}
    if aws_profile:
        session_kwargs['profile_name'] = aws_profile
    
    session = boto3.Session(**session_kwargs)
    s3_client = session.client('s3')

    # Verify bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket)
        print(f"✓ Bucket '{bucket}' is accessible\n")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Error: Bucket '{bucket}' does not exist")
        elif error_code == '403':
            print(f"Error: Access denied to bucket '{bucket}'")
        else:
            print(f"Error: {e}")
        sys.exit(1)

    # Ensure prefix doesn't start with / but ends with /
    prefix = prefix.strip('/')
    if prefix:
        prefix += '/'

    print(f"Uploading files to s3://{bucket}/{prefix}\n")

    uploaded_count = 0
    failed_count = 0

    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            print(f"✗ File not found: {filepath}")
            failed_count += 1
            continue

        # Use just the filename for S3 key (no subdirectories)
        # This ensures all files are at the same level in S3
        s3_key = f"{prefix}{path.name}"

        try:
            # Upload file
            file_size = path.stat().st_size
            print(f"Uploading {path.name} ({file_size:,} bytes)...", end=' ')
            
            s3_client.upload_file(
                str(path),
                bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            print(f"✓ s3://{bucket}/{s3_key}")
            uploaded_count += 1
            
        except ClientError as e:
            print(f"✗ Failed: {e}")
            failed_count += 1
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            failed_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Upload Summary:")
    print(f"  Successful: {uploaded_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {uploaded_count + failed_count}")
    print(f"{'='*60}\n")

    if uploaded_count > 0:
        print("✓ Files uploaded successfully to consistent S3 prefix")
        print(f"\nS3 Location: s3://{bucket}/{prefix}")
        print("\nCritical points for single table enforcement:")
        print("  1. All files are in the SAME S3 prefix")
        print("  2. No subdirectories or date-based partitions at this level")
        print("  3. All files should have consistent schema and format")
        print("\nNext steps:")
        print("  1. Configure Glue crawler to target: s3://{}/{}".format(bucket, prefix))
        print("  2. Run the crawler")
        print("  3. Verify a single table was created in Glue Data Catalog")
    
    if failed_count > 0:
        sys.exit(1)


def find_generated_files(directory: str = "generated_data") -> List[str]:
    """Find all generated data files in the specified directory.
    
    Args:
        directory: Directory containing generated files
        
    Returns:
        List of file paths
    """
    path = Path(directory)
    if not path.exists():
        return []
    
    # Common data file extensions
    extensions = ['.csv', '.json', '.parquet', '.gz']
    files = []
    
    for ext in extensions:
        files.extend(path.glob(f"*{ext}"))
    
    return [str(f) for f in files]


def main():
    """Main function to handle CLI arguments and upload files."""
    parser = argparse.ArgumentParser(
        description="Upload sample data files to S3 with consistent prefix structure"
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="S3 bucket name (required)"
    )
    parser.add_argument(
        "--prefix",
        default="third-party-data",
        help="S3 prefix (folder) for data files (default: third-party-data)"
    )
    parser.add_argument(
        "--files",
        nargs='+',
        help="Specific files to upload. If not specified, uploads all files from generated_data directory"
    )
    parser.add_argument(
        "--directory",
        default="generated_data",
        help="Directory containing generated files (default: generated_data)"
    )
    parser.add_argument(
        "--profile",
        help="AWS profile name to use (optional)"
    )

    args = parser.parse_args()

    # Determine files to upload
    if args.files:
        files_to_upload = args.files
        print(f"Uploading {len(files_to_upload)} specified file(s)...")
    else:
        files_to_upload = find_generated_files(args.directory)
        if not files_to_upload:
            print(f"Error: No files found in '{args.directory}' directory")
            print("\nPlease generate sample data first:")
            print("  python generate_sample_data.py --format csv --num-files 3")
            sys.exit(1)
        print(f"Found {len(files_to_upload)} file(s) in '{args.directory}' directory...")

    # Upload files
    upload_files_to_s3(
        bucket=args.bucket,
        prefix=args.prefix,
        files=files_to_upload,
        aws_profile=args.profile
    )


if __name__ == "__main__":
    main()
