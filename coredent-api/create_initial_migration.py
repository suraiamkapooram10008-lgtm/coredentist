#!/usr/bin/env python3
"""
Create initial Alembic migration for CoreDent PMS
This script generates the base migration that creates all tables from scratch.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command

def create_initial_migration():
    """Create the initial migration with all tables."""
    
    # Set up Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Generate initial migration
    print("Creating initial migration...")
    command.revision(
        alembic_cfg,
        message="Initial migration - create all tables",
        autogenerate=True,
        rev_id="001_initial"
    )
    
    print("Initial migration created successfully!")
    print("Next steps:")
    print("1. Review the generated migration file")
    print("2. Run: alembic upgrade head")

if __name__ == "__main__":
    create_initial_migration()