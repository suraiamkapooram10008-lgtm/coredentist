#!/usr/bin/env python3
"""
Database Backup Script for CoreDent
HIPAA §164.308(a)(7)(ii)(A) — Data Backup Plan

Performs automated PostgreSQL backups with the following features:
- Daily full backups (pg_dump)
- Uploads to S3 with server-side encryption
- Retains last 30 days of backups
- Verifies backup integrity
- Logs all operations for audit trail

Usage:
    python scripts/backup_database.py          # Run backup manually
    python scripts/backup_database.py --verify # Verify latest backup

Environment Variables:
    DATABASE_URL          - PostgreSQL connection string
    AWS_ACCESS_KEY_ID     - AWS credentials
    AWS_SECRET_ACCESS_KEY - AWS credentials
    AWS_S3_BUCKET         - S3 bucket for backups
    AWS_REGION            - AWS region (default: us-east-1)
"""

import os
import sys
import subprocess
import gzip
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Configuration
BACKUP_RETENTION_DAYS = 30
CHUNK_SIZE = 8192


def get_db_url() -> str:
    """Get database URL from environment"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is required")
        sys.exit(1)
    return db_url


def get_s3_client():
    """Initialize S3 client"""
    try:
        return boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize S3 client: {e}")
        sys.exit(1)


def get_s3_bucket() -> str:
    """Get S3 bucket name"""
    bucket = os.getenv("AWS_S3_BUCKET")
    if not bucket:
        print("ERROR: AWS_S3_BUCKET environment variable is required")
        sys.exit(1)
    return bucket


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def run_pg_dump(db_url: str, output_path: str) -> bool:
    """Run pg_dump to create a database backup"""
    try:
        cmd = [
            "pg_dump",
            "--dbname", db_url,
            "--format", "custom",
            "--verbose",
            "--file", output_path,
        ]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"pg_dump completed: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pg_dump failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("ERROR: pg_dump not found. Install PostgreSQL client tools.")
        return False


def compress_file(input_path: str, output_path: str) -> bool:
    """Compress a file using gzip"""
    try:
        with open(input_path, "rb") as f_in:
            with gzip.open(output_path, "wb") as f_out:
                for chunk in iter(lambda: f_in.read(CHUNK_SIZE), b""):
                    f_out.write(chunk)
        print(f"Compressed: {input_path} -> {output_path}")
        return True
    except Exception as e:
        print(f"ERROR: Compression failed: {e}")
        return False


def upload_to_s3(s3_client, bucket: str, file_path: str, s3_key: str) -> bool:
    """Upload file to S3 with server-side encryption"""
    try:
        s3_client.upload_file(
            file_path,
            bucket,
            s3_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "StorageClass": "STANDARD_IA",  # Infrequent access for cost savings
            }
        )
        print(f"Uploaded to s3://{bucket}/{s3_key}")
        return True
    except ClientError as e:
        print(f"ERROR: S3 upload failed: {e}")
        return False


def verify_backup(s3_client, bucket: str, s3_key: str, local_hash: str) -> bool:
    """Verify backup integrity on S3"""
    try:
        # Get ETag (MD5) from S3
        response = s3_client.head_object(Bucket=bucket, Key=s3_key)
        s3_etag = response["ETag"].strip('"')
        print(f"S3 ETag: {s3_etag}")
        print(f"Local SHA-256: {local_hash}")
        
        # Download and verify hash
        temp_file = f"/tmp/verify_{os.path.basename(s3_key)}"
        s3_client.download_file(bucket, s3_key, temp_file)
        downloaded_hash = calculate_sha256(temp_file)
        
        if downloaded_hash == local_hash:
            print("✅ Backup integrity verified")
            os.remove(temp_file)
            return True
        else:
            print("❌ Backup integrity check FAILED")
            return False
    except Exception as e:
        print(f"ERROR: Verification failed: {e}")
        return False


def cleanup_old_backups(s3_client, bucket: str, prefix: str = "backups/"):
    """Delete backups older than retention period"""
    try:
        cutoff = datetime.now(timezone.utc).timestamp() - (BACKUP_RETENTION_DAYS * 86400)
        paginator = s3_client.get_paginator("list_objects_v2")
        
        deleted = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if obj["LastModified"].timestamp() < cutoff:
                    s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
                    deleted += 1
        
        if deleted:
            print(f"Cleaned up {deleted} old backups (> {BACKUP_RETENTION_DAYS} days)")
    except Exception as e:
        print(f"WARNING: Cleanup failed: {e}")


def main():
    """Main backup procedure"""
    import argparse
    parser = argparse.ArgumentParser(description="CoreDent Database Backup")
    parser.add_argument("--verify", action="store_true", help="Verify latest backup")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"CoreDent Database Backup - {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}\n")
    
    # Setup
    db_url = get_db_url()
    s3_client = get_s3_client()
    bucket = get_s3_bucket()
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"coredent_backup_{timestamp}"
    temp_dir = Path("/tmp/coredent_backups")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    dump_path = temp_dir / f"{backup_name}.dump"
    compressed_path = temp_dir / f"{backup_name}.dump.gz"
    s3_key = f"backups/{backup_name}.dump.gz"
    
    if args.verify:
        # Verify mode: check latest backup
        print("Verifying latest backup...")
        # TODO: Implement verification of latest backup from S3
        print("Verification mode not yet implemented")
        return
    
    # Step 1: Create dump
    print("Step 1: Creating database dump...")
    if not run_pg_dump(db_url, str(dump_path)):
        sys.exit(1)
    
    # Step 2: Compress
    print("\nStep 2: Compressing backup...")
    if not compress_file(str(dump_path), str(compressed_path)):
        sys.exit(1)
    
    # Step 3: Calculate hash
    print("\nStep 3: Calculating checksum...")
    file_hash = calculate_sha256(str(compressed_path))
    print(f"SHA-256: {file_hash}")
    
    # Step 4: Upload to S3
    print("\nStep 4: Uploading to S3...")
    if not upload_to_s3(s3_client, bucket, str(compressed_path), s3_key):
        sys.exit(1)
    
    # Step 5: Verify
    print("\nStep 5: Verifying backup integrity...")
    if not verify_backup(s3_client, bucket, s3_key, file_hash):
        sys.exit(1)
    
    # Step 6: Cleanup old backups
    print("\nStep 6: Cleaning up old backups...")
    cleanup_old_backups(s3_client, bucket)
    
    # Step 7: Cleanup local files
    print("\nStep 7: Cleaning up local files...")
    dump_path.unlink(missing_ok=True)
    compressed_path.unlink(missing_ok=True)
    
    print(f"\n{'='*60}")
    print("✅ Backup completed successfully")
    print(f"{'='*60}")
    print(f"Backup: s3://{bucket}/{s3_key}")
    print(f"SHA-256: {file_hash}")
    print(f"Retention: {BACKUP_RETENTION_DAYS} days")


if __name__ == "__main__":
    main()
