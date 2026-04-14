#!/usr/bin/env python3
"""
Simple database creation script that bypasses encryption issues
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config_simple import settings

async def create_database():
    """Create database tables"""
    print("Creating database...")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    
    # Import models to register them
    from app.core.base import Base
    from app.models.user import User
    from app.models.practice import Practice
    from app.models.audit import Session
    from app.models.password_reset import PasswordResetToken
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database created successfully!")
    
    # Create default admin user
    from app.core.security import get_password_hash
    from datetime import datetime, timezone
    from app.models.user import UserRole
    
    async with engine.begin() as conn:
        # Check if admin user exists
        result = await conn.execute(
            text("SELECT COUNT(*) FROM users WHERE email = 'admin@coredent.com'")
        )
        count = result.scalar()
        
        if count == 0:
            # Create default practice
            await conn.execute(
                text("""
                INSERT INTO practices (id, name, address_street, phone, email, created_at, updated_at)
                VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Default Practice', 
                        '123 Main St', '555-0123', 'practice@coredent.com', 
                        datetime('now'), datetime('now'))
                """)
            )
            
            # Create admin user
            password_hash = get_password_hash("Admin123!@#")
            await conn.execute(
                text("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name, role, 
                    practice_id, is_active, is_email_verified, created_at, updated_at,
                    failed_login_attempts, locked_until, last_failed_login,
                    email_verification_token, password_changed_at
                ) VALUES (
                    '550e8400-e29b-41d4-a716-446655440001', 'admin@coredent.com', :password_hash,
                    'Admin', 'User', 'admin', '550e8400-e29b-41d4-a716-446655440000',
                    1, 1, datetime('now'), datetime('now'),
                    0, NULL, NULL, NULL, datetime('now')
                )
                """), {"password_hash": password_hash}
            )
            
            print("Created admin user: admin@coredent.com / Admin123!@#")
        else:
            print("Admin user already exists")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_database())