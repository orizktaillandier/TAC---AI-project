#!/usr/bin/env python3
"""
Seed data script for the Automotive Ticket Classifier.
This script imports data from CSV files and seeds the database.
"""
import os
import sys
import argparse
import csv
import logging
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("seed_data.log"),
    ],
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models
try:
    from api.app.core.config import settings
    from api.app.db.models import Dealer, Syndicator, User
    from api.app.db.session import Base, SessionLocal
    from api.app.core.security import get_password_hash
except ImportError:
    logger.error("Failed to import modules. Make sure you are running this script from the project root directory.")
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Seed data script for the Automotive Ticket Classifier")
    parser.add_argument(
        "--syndicators-csv",
        type=str,
        default="data/syndicators.csv",
        help="Path to syndicators CSV file (default: data/syndicators.csv)",
    )
    parser.add_argument(
        "--dealers-csv",
        type=str,
        default="data/rep_dealer_mapping.csv",
        help="Path to dealers CSV file (default: data/rep_dealer_mapping.csv)",
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create admin user",
    )
    parser.add_argument(
        "--admin-email",
        type=str,
        default="admin@example.com",
        help="Admin email (default: admin@example.com)",
    )
    parser.add_argument(
        "--admin-password",
        type=str,
        default="password",
        help="Admin password (default: password)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate existing data before seeding",
    )
    return parser.parse_args()


def import_syndicators(db, csv_path, truncate=False):
    """Import syndicators from CSV file."""
    logger.info(f"Importing syndicators from {csv_path}...")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        return
    
    # Truncate existing data if requested
    if truncate:
        logger.info("Truncating existing syndicators...")
        db.query(Syndicator).delete()
        db.commit()
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        
        # Check if "Syndicator" column exists
        if "Syndicator" not in df.columns:
            logger.error("CSV file does not have a 'Syndicator' column")
            return
        
        # Process syndicators
        count = 0
        for _, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row["Syndicator"]):
                continue
            
            # Check if syndicator already exists
            name = row["Syndicator"].strip()
            existing = db.query(Syndicator).filter(Syndicator.name == name).first()
            if existing:
                continue
            
            # Create new syndicator
            syndicator = Syndicator(
                name=name,
                description="",
                is_active=True,
            )
            db.add(syndicator)
            count += 1
        
        # Commit changes
        db.commit()
        logger.info(f"Imported {count} syndicators")
    
    except Exception as e:
        logger.error(f"Error importing syndicators: {str(e)}")
        db.rollback()


def import_dealers(db, csv_path, truncate=False):
    """Import dealers from CSV file."""
    logger.info(f"Importing dealers from {csv_path}...")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        return
    
    # Truncate existing data if requested
    if truncate:
        logger.info("Truncating existing dealers...")
        db.query(Dealer).delete()
        db.commit()
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        
        # Check if required columns exist
        required_columns = ["Rep Name", "Dealer Name", "Dealer ID"]
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"CSV file does not have a '{col}' column")
                return
        
        # Process dealers
        count = 0
        for _, row in df.iterrows():
            # Skip rows with missing data
            if pd.isna(row["Dealer Name"]) or pd.isna(row["Dealer ID"]):
                continue
            
            # Check if dealer already exists
            dealer_id = str(row["Dealer ID"]).strip()
            existing = db.query(Dealer).filter(Dealer.dealer_id == dealer_id).first()
            if existing:
                # Update existing dealer
                existing.dealer_name = row["Dealer Name"].strip()
                existing.rep_name = row["Rep Name"].strip() if not pd.isna(row["Rep Name"]) else ""
                db.add(existing)
                continue
            
            # Create new dealer
            dealer = Dealer(
                dealer_id=dealer_id,
                dealer_name=row["Dealer Name"].strip(),
                rep_name=row["Rep Name"].strip() if not pd.isna(row["Rep Name"]) else "",
            )
            db.add(dealer)
            count += 1
        
        # Commit changes
        db.commit()
        logger.info(f"Imported {count} dealers")
    
    except Exception as e:
        logger.error(f"Error importing dealers: {str(e)}")
        db.rollback()


def create_admin_user(db, email, password):
    """Create admin user."""
    logger.info(f"Creating admin user with email {email}...")
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        logger.info(f"User with email {email} already exists")
        return
    
    # Create new user
    user = User(
        email=email,
        full_name="Admin User",
        hashed_password=get_password_hash(password),
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    
    # Commit changes
    try:
        db.commit()
        logger.info(f"Created admin user with email {email}")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()


def main():
    """Main function."""
    # Parse arguments
    args = parse_args()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Import syndicators
        import_syndicators(db, args.syndicators_csv, args.truncate)
        
        # Import dealers
        import_dealers(db, args.dealers_csv, args.truncate)
        
        # Create admin user
        if args.create_admin:
            create_admin_user(db, args.admin_email, args.admin_password)
        
        logger.info("Seed data process completed successfully")
    
    except Exception as e:
        logger.error(f"Seed data process failed: {str(e)}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()