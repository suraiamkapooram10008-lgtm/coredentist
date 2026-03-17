#!/usr/bin/env python3
"""
Create Initial Admin User
Run this script to create the first admin user for the system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.practice import Practice


async def create_admin():
    """Create admin user and practice"""
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True,
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create practice
        practice = Practice(
            id=uuid4(),
            name="Demo Dental Practice",
            email="info@demodental.com",
            phone="555-0123",
            address_street="123 Main Street",
            address_city="Springfield",
            address_state="IL",
            address_zip="62701",
            timezone="America/Chicago",
            currency="USD",
        )
        session.add(practice)
        await session.flush()
        
        # Create admin user
        admin = User(
            id=uuid4(),
            email="admin@coredent.com",
            password_hash=get_password_hash("Admin123!"),
            first_name="Admin",
            last_name="User",
            role=UserRole.OWNER,
            practice_id=practice.id,
            is_active=True,
        )
        session.add(admin)
        
        await session.commit()
        
        print("\n" + "="*60)
        print("✅ Admin user created successfully!")
        print("="*60)
        print(f"\nPractice: {practice.name}")
        print(f"Practice ID: {practice.id}")
        print(f"\nAdmin Email: {admin.email}")
        print(f"Admin Password: Admin123!")
        print(f"Admin ID: {admin.id}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("="*60 + "\n")
    
    await engine.dispose()


if __name__ == "__main__":
    print("\n🚀 Creating admin user...\n")
    asyncio.run(create_admin())
