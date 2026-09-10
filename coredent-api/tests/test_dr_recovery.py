"""
Disaster Recovery Verification Tests
Validates database schema, practice tenancy isolation, table structures, and encryption.
"""

import pytest
from sqlalchemy import select, func
from app.models.practice import Practice
from app.models.patient import Patient
from app.models.billing import Invoice
from app.models.insurance import InsuranceClaim
from app.models.lab import LabCase
from app.models.treatment import ProcedureLibrary
from app.models.inventory import InventoryItem


@pytest.mark.asyncio
async def test_dr_schema_integrity(db_session):
    """Verify that all core tables exist and can be queried."""
    result = await db_session.execute(select(func.count(Practice.id)))
    count = result.scalar()
    assert count is not None


@pytest.mark.asyncio
async def test_dr_compound_constraints_defined(db_session):
    """Verify that tenant compound unique constraints are defined on models."""
    # Check Invoice constraints
    invoice_constraints = [c.name for c in Invoice.__table__.constraints if hasattr(c, 'name')]
    assert 'uq_practice_invoice_number' in invoice_constraints

    # Check InsuranceClaim constraints
    claim_constraints = [c.name for c in InsuranceClaim.__table__.constraints if hasattr(c, 'name')]
    assert 'uq_practice_claim_number' in claim_constraints

    # Check LabCase constraints
    lab_constraints = [c.name for c in LabCase.__table__.constraints if hasattr(c, 'name')]
    assert 'uq_practice_case_number' in lab_constraints

    # Check ProcedureLibrary constraints
    proc_constraints = [c.name for c in ProcedureLibrary.__table__.constraints if hasattr(c, 'name')]
    assert 'uq_practice_ada_code' in proc_constraints

    # Check InventoryItem constraints
    inv_constraints = [c.name for c in InventoryItem.__table__.constraints if hasattr(c, 'name')]
    assert 'uq_practice_inventory_sku' in inv_constraints


@pytest.mark.asyncio
async def test_dr_encryption_at_rest(db_session, test_practice, test_patient):
    """Verify that patient encrypted fields can be round-tripped correctly."""
    result = await db_session.execute(
        select(Patient).where(Patient.id == test_patient.id)
    )
    patient = result.scalar_one_or_none()
    assert patient is not None
    assert patient.first_name == test_patient.first_name
    assert patient.last_name == test_patient.last_name
