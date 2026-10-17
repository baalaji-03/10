"""
Database Initialization Script for Baalaji Pharmacy Management System
"""

import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import engine, Base, SessionLocal
from backend.app.seed import seed_database_defaults

def init():
    print("==================================================")
    print("Baalaji Pharmacy Management System - DB Initializer")
    print("==================================================")
    print(f"Connecting to database engine: {engine.url}")
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    print("Seeding default roles, pharmacy settings, sample catalog & admin user...")
    db = SessionLocal()
    try:
        seed_database_defaults(db)
        print("Seeding completed successfully!")
        print("Default Admin Account: admin / Admin@123")
        print("Default Pharmacist Account: pharmacist / Admin@123")
        print("Default Cashier Account: cashier / Admin@123")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()
    print("==================================================")

if __name__ == "__main__":
    init()
