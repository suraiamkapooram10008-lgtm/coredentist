"""
Check if subscription tables exist in the database
Run this script to verify the subscription tables were created
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

# Get database URL from environment or use default
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set!")
    print("\nPlease set it in Railway Dashboard or run:")
    print("  export DATABASE_URL=postgresql://user:password@host:port/database")
    sys.exit(1)

print(f"🔍 Checking database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Get all tables
    all_tables = inspector.get_table_names()
    
    # Subscription tables we expect
    subscription_tables = [
        "subscription_plans",
        "subscriptions",
        "usage_meters",
        "usage_records",
        "dunning_events",
        "cancellation_surveys"
    ]
    
    print(f"\n📊 Total tables in database: {len(all_tables)}")
    print("\n" + "=" * 60)
    print("📋 SUBSCRIPTION TABLES STATUS:")
    print("=" * 60)
    
    all_exist = True
    for table in subscription_tables:
        exists = table in all_tables
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status} - {table}")
        if not exists:
            all_exist = False
    
    print("\n" + "=" * 60)
    if all_exist:
        print("✅ ALL subscription tables exist! Migration was successful.")
    else:
        print("❌ Some subscription tables are MISSING!")
        print("\n📝 To create them, run:")
        print("   alembic upgrade head")
        print("\nOr in Railway Dashboard:")
        print("   1. Go to Backend service → Shell")
        print("   2. Run: alembic upgrade head")
    
    # Show all tables for reference
    print("\n" + "=" * 60)
    print("📋 ALL TABLES IN DATABASE:")
    print("=" * 60)
    for table in sorted(all_tables):
        print(f"  - {table}")
        
except Exception as e:
    print(f"\n❌ Error connecting to database: {e}")
    print("\nPossible issues:")
    print("  1. DATABASE_URL is incorrect")
    print("  2. Database is not accessible from your location")
    print("  3. Network/firewall issues")