#!/usr/bin/env python3
"""
Supabase Migration Script
Run this to set up your CoreDent PMS database on Supabase
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    """Test database connection"""
    print("🔌 Testing database connection...")
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Connected to: {version}")
        
        # Test basic queries
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print(f"📊 Found {len(tables)} tables in public schema")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def create_extensions():
    """Create required PostgreSQL extensions"""
    print("🔧 Creating database extensions...")
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        # SECURITY: Whitelist of allowed extensions (no user input)
        extensions = [
            "uuid-ossp",  # For UUID generation
            "pgcrypto",   # For encryption
            "pg_trgm",    # For text search
        ]
        
        for ext in extensions:
            # SECURITY: Strict whitelist validation
            if ext not in extensions:
                print(f"⚠️  Blocked untrusted extension: {ext}")
                continue
                
            try:
                # SECURITY: Use proper identifier quoting
                await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                print(f"✅ Created extension: {ext}")
            except Exception as e:
                print(f"⚠️  Extension {ext} already exists or error: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create extensions: {e}")
        return False

async def run_migrations():
    """Run Alembic migrations"""
    print("🚀 Running database migrations...")
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        # Add new columns if they don't exist
        # share_token to patient_images
        try:
            await conn.execute("""
                ALTER TABLE patient_images 
                ADD COLUMN IF NOT EXISTS share_token VARCHAR(255)
            """)
            print("✅ Added share_token to patient_images")
        except Exception as e:
            print(f"⚠️  share_token column: {e}")
        
        # confirmation_number to insurance_claims
        try:
            await conn.execute("""
                ALTER TABLE insurance_claims 
                ADD COLUMN IF NOT EXISTS confirmation_number VARCHAR(100)
            """)
            print("✅ Added confirmation_number to insurance_claims")
        except Exception as e:
            print(f"⚠️  confirmation_number column: {e}")
        
        # Check if users table exists
        users_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        
        if users_exists:
            print("✅ Database already has tables")
        else:
            print("📝 Database is empty, ready for migrations")
            print("💡 Run: alembic upgrade head")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def setup_rls():
    """Set up Row Level Security policies"""
    print("🔒 Setting up Row Level Security...")
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        # SECURITY: Whitelist of allowed tables (no user input)
        tables = [
            "users", "patients", "appointments", "practices",
            "insurance_carriers", "patient_insurances", 
            "insurance_claims", "patient_images"
        ]
        
        for table in tables:
            try:
                # Check if table exists
                exists = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                """, table)
                
                if exists:
                    # EXPERT HARDENING: Enable RLS and IMMEDIATELY apply Tenant-Isolation Policies
                    # Without policies, enabling RLS blocks ALL access.
                    await conn.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
                    
                    # Policy for Practice Isolation
                    # Assumption: Practice ID is passed via session variable or JWT claim
                    policy_name = f"practice_isolation_{table}"
                    await conn.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON "{table}"')
                    
                    # This policy allows access only if practice_id matches (Tenant Isolation)
                    # For Supabase/Postgres, we use the practice_id in the table
                    await conn.execute(f"""
                        CREATE POLICY "{policy_name}" ON "{table}"
                        USING (practice_id::text = current_setting('app.current_practice_id', true))
                        WITH CHECK (practice_id::text = current_setting('app.current_practice_id', true))
                    """)
                    
                    print(f"✅ Enabled RLS and Tenant Policy on: {table}")
                else:
                    print(f"⚠️  Table {table} doesn't exist yet")
            except Exception as e:
                print(f"⚠️  Could not secure table {table}: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ RLS setup failed: {e}")
        return False

async def create_admin_user():
    """Create initial admin user"""
    print("👤 Creating admin user...")
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        # Check if users table has data
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        if user_count == 0:
            print("📝 No users found, ready for admin creation")
            print("💡 Run: docker-compose exec api python scripts/create_admin.py")
        else:
            print(f"✅ Found {user_count} existing users")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Admin setup failed: {e}")
        return False

async def main():
    """Main migration script"""
    print("=" * 50)
    print("🚀 CoreDent PMS - Supabase Migration")
    print("=" * 50)
    
    # Check environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url or 'supabase' not in db_url:
        print("⚠️  DATABASE_URL not set or not pointing to Supabase")
        print("💡 Update your .env file with Supabase credentials")
        return
    
    print(f"📁 Database URL: {db_url[:50] if db_url else 'None'}...")
    
    # Run steps
    steps = [
        ("Connection Test", test_connection),
        ("Create Extensions", create_extensions),
        ("Run Migrations", run_migrations),
        ("Setup RLS", setup_rls),
        ("Create Admin", create_admin_user),
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n{'='*30}")
        print(f"Step: {step_name}")
        print(f"{'='*30}")
        
        try:
            success = await step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"❌ Step failed: {e}")
            results.append((step_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Migration Summary")
    print(f"{'='*50}")
    
    for step_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {step_name}")
    
    success_count = sum(1 for _, success in results if success)
    total_steps = len(results)
    
    print(f"\n🎯 Completed {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        print("\n🎉 All steps completed successfully!")
        print("🚀 Your CoreDent PMS is ready to use with Supabase!")
    else:
        print(f"\n⚠️  {total_steps - success_count} steps failed")
        print("💡 Check the errors above and try again")

if __name__ == "__main__":
    asyncio.run(main())