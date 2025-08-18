#!/usr/bin/env python3
"""
Backup script for the Automotive Ticket Classifier.
This script creates a backup of the database and CSV files.
"""
import os
import sys
import argparse
import datetime
import shutil
import tarfile
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backup.log"),
    ],
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_DATA_DIR = "data"
DEFAULT_DB_NAME = "auto_classifier"
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Backup script for the Automotive Ticket Classifier")
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=DEFAULT_BACKUP_DIR,
        help=f"Backup directory (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=DEFAULT_DATA_DIR,
        help=f"Data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--db-name",
        type=str,
        default=DEFAULT_DB_NAME,
        help=f"Database name (default: {DEFAULT_DB_NAME})",
    )
    parser.add_argument(
        "--db-user",
        type=str,
        default=DEFAULT_DB_USER,
        help=f"Database user (default: {DEFAULT_DB_USER})",
    )
    parser.add_argument(
        "--db-host",
        type=str,
        default=DEFAULT_DB_HOST,
        help=f"Database host (default: {DEFAULT_DB_HOST})",
    )
    parser.add_argument(
        "--db-port",
        type=str,
        default=DEFAULT_DB_PORT,
        help=f"Database port (default: {DEFAULT_DB_PORT})",
    )
    parser.add_argument(
        "--db-password",
        type=str,
        help="Database password (if not provided, will try to read from PGPASSWORD environment variable)",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database backup",
    )
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip data backup",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress backup files",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=7,
        help="Number of days to keep backups (default: 7)",
    )
    return parser.parse_args()


def backup_database(db_name, db_user, db_host, db_port, db_password, backup_dir, timestamp):
    """Backup the database."""
    logger.info("Backing up database...")
    
    # Set environment variable for password
    env = os.environ.copy()
    if db_password:
        env["PGPASSWORD"] = db_password
    
    # Create backup filename
    backup_file = os.path.join(backup_dir, f"{db_name}_{timestamp}.sql")
    
    # Create pg_dump command
    cmd = [
        "pg_dump",
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "-f", backup_file,
        "-F", "p",  # Plain text format
    ]
    
    try:
        # Run pg_dump
        result = subprocess.run(cmd, env=env, check=True, capture_output=True)
        logger.info(f"Database backup successful: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup failed: {e.stderr.decode()}")
        return None
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        return None


def backup_data(data_dir, backup_dir, timestamp):
    """Backup the data directory."""
    logger.info("Backing up data...")
    
    # Create backup directory
    data_backup_dir = os.path.join(backup_dir, f"data_{timestamp}")
    os.makedirs(data_backup_dir, exist_ok=True)
    
    # Get list of files
    data_path = Path(data_dir)
    files = list(data_path.glob("**/*"))
    files = [f for f in files if f.is_file()]
    
    # Copy files
    for file_path in files:
        rel_path = file_path.relative_to(data_path)
        dest_path = Path(data_backup_dir) / rel_path
        
        # Create parent directories
        os.makedirs(dest_path.parent, exist_ok=True)
        
        # Copy file
        shutil.copy2(file_path, dest_path)
    
    logger.info(f"Data backup successful: {data_backup_dir}")
    return data_backup_dir


def compress_backup(backup_files, backup_dir, timestamp):
    """Compress backup files."""
    logger.info("Compressing backup...")
    
    # Create tarball filename
    tarball_file = os.path.join(backup_dir, f"backup_{timestamp}.tar.gz")
    
    # Create tarball
    with tarfile.open(tarball_file, "w:gz") as tar:
        for file_path in backup_files:
            arcname = os.path.basename(file_path)
            tar.add(file_path, arcname=arcname)
    
    logger.info(f"Compression successful: {tarball_file}")
    return tarball_file


def cleanup_old_backups(backup_dir, retention_days):
    """Clean up old backups."""
    logger.info(f"Cleaning up backups older than {retention_days} days...")
    
    # Get current time
    now = datetime.datetime.now()
    
    # Get all files and directories in backup directory
    backup_path = Path(backup_dir)
    items = list(backup_path.glob("*"))
    
    # Filter and delete old backups
    deleted_count = 0
    for item in items:
        # Get item modification time
        mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
        
        # Calculate age
        age = now - mtime
        
        # Delete if older than retention days
        if age.days > retention_days:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            deleted_count += 1
    
    logger.info(f"Deleted {deleted_count} old backups")


def main():
    """Main function."""
    # Parse arguments
    args = parse_args()
    
    # Create backup directory
    os.makedirs(args.backup_dir, exist_ok=True)
    
    # Get timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize backup files list
    backup_files = []
    
    # Backup database
    if not args.skip_db:
        db_password = args.db_password or os.environ.get("PGPASSWORD")
        db_backup = backup_database(
            args.db_name,
            args.db_user,
            args.db_host,
            args.db_port,
            db_password,
            args.backup_dir,
            timestamp,
        )
        if db_backup:
            backup_files.append(db_backup)
    
    # Backup data
    if not args.skip_data:
        data_backup = backup_data(args.data_dir, args.backup_dir, timestamp)
        if data_backup:
            backup_files.append(data_backup)
    
    # Compress backup
    if args.compress and backup_files:
        compress_backup(backup_files, args.backup_dir, timestamp)
    
    # Clean up old backups
    if args.retention > 0:
        cleanup_old_backups(args.backup_dir, args.retention)
    
    logger.info("Backup completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}", exc_info=True)
        sys.exit(1)