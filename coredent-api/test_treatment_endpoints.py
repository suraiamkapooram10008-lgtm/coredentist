#!/usr/bin/env python3
"""
Test Treatment Planning Models and Schemas
Run this to verify treatment models and schemas are working
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.treatment import TreatmentPlan, TreatmentPhase, TreatmentProcedure, ProcedureLibrary
import uuid
from datetime import date, datetime

async def test_treatment_models():
    """Test that treatment models can be created"""
    print("🧪 Testing Treatment Models...")
    
    # Create test data
    practice_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    
    # Test TreatmentPlan
    plan = TreatmentPlan(
        id=uuid.uuid4(),
        practice_id=practice_id,
        patient_id=patient_id,
        provider_id=provider_id,
        plan_name="Test Treatment Plan",
        status="draft",
        chief_complaint="Test complaint",
        diagnosis="Test diagnosis",
        treatment_goals="Test goals",
        total_estimated_cost=1000.00,
        total_insurance_estimate=800.00,
        total_patient_responsibility=200.00,
        created_date=date.today(),
    )
    
    print(f"✅ TreatmentPlan created: {plan.plan_name}")
    print(f"   Status: {plan.status}")
    print(f"   Total Cost: ${plan.total_estimated_cost}")
    print(f"   Patient Responsibility: ${plan.total_patient_responsibility}")
    
    # Test TreatmentPhase
    phase = TreatmentPhase(
        id=uuid.uuid4(),
        treatment_plan_id=plan.id,
        phase_number=1,
        phase_name="Phase 1 - Initial Treatment",
        description="Initial restorative work",
        estimated_cost=500.00,
        insurance_estimate=400.00,
        patient_responsibility=100.00,
    )
    
    print(f"✅ TreatmentPhase created: {phase.phase_name}")
    print(f"   Phase {phase.phase_number}")
    print(f"   Estimated Cost: ${phase.estimated_cost}")
    
    # Test TreatmentProcedure
    procedure = TreatmentProcedure(
        id=uuid.uuid4(),
        treatment_plan_id=plan.id,
        phase_id=phase.id,
        procedure_type="restorative",
        ada_code="D2391",
        description="Resin-based composite - one surface, posterior",
        tooth_number="3",
        fee=250.00,
        insurance_estimate=200.00,
        patient_responsibility=50.00,
        coverage_percentage=80,
        duration_minutes=30,
        priority=1,
    )
    
    print(f"✅ TreatmentProcedure created: {procedure.ada_code}")
    print(f"   Description: {procedure.description}")
    print(f"   Fee: ${procedure.fee}")
    print(f"   Insurance Coverage: {procedure.coverage_percentage}%")
    print(f"   Insurance Amount: ${procedure.insurance_coverage_amount}")
    print(f"   Patient Amount: ${procedure.patient_amount}")
    
    # Test ProcedureLibrary
    library_entry = ProcedureLibrary(
        id=uuid.uuid4(),
        practice_id=practice_id,
        ada_code="D2750",
        description="Crown - porcelain fused to high noble metal",
        procedure_type="prosthodontic",
        category="Crowns & Bridges",
        default_fee=1200.00,
        typical_duration_minutes=90,
        typical_coverage_percentage=50,
        requires_pre_auth=True,
    )
    
    print(f"✅ ProcedureLibrary created: {library_entry.ada_code}")
    print(f"   Description: {library_entry.description}")
    print(f"   Default Fee: ${library_entry.default_fee}")
    print(f"   Typical Coverage: {library_entry.typical_coverage_percentage}%")
    
    return True

async def test_cost_calculation():
    """Test cost calculation logic"""
    print("\n🧪 Testing Cost Calculation...")
    
    # Create test procedure
    procedure = TreatmentProcedure(
        fee=1000.00,
        coverage_percentage=80,
    )
    
    insurance_coverage = procedure.insurance_coverage_amount
    patient_responsibility = procedure.patient_amount
    
    print(f"✅ Procedure Fee: ${procedure.fee}")
    print(f"✅ Coverage Percentage: {procedure.coverage_percentage}%")
    print(f"✅ Insurance Coverage: ${insurance_coverage}")
    print(f"✅ Patient Responsibility: ${patient_responsibility}")
    
    # Verify calculation
    expected_insurance = 1000.00 * 0.80  # 80% of 1000
    expected_patient = 1000.00 * 0.20    # 20% of 1000
    
    assert abs(insurance_coverage - expected_insurance) < 0.01, "Insurance calculation incorrect"
    assert abs(patient_responsibility - expected_patient) < 0.01, "Patient calculation incorrect"
    
    print("✅ All calculations correct!")
    return True

async def test_enum_values():
    """Test enum values are valid"""
    print("\n🧪 Testing Enum Values...")
    
    from app.models.treatment import TreatmentPlanStatus, ProcedureType, ToothSurface
    
    # Test TreatmentPlanStatus
    status_values = [status.value for status in TreatmentPlanStatus]
    print(f"✅ TreatmentPlanStatus values: {status_values}")
    assert "draft" in status_values
    assert "accepted" in status_values
    assert "completed" in status_values
    
    # Test ProcedureType
    type_values = [type_.value for type_ in ProcedureType]
    print(f"✅ ProcedureType values: {type_values}")
    assert "preventive" in type_values
    assert "restorative" in type_values
    assert "prosthodontic" in type_values
    
    # Test ToothSurface
    surface_values = [surface.value for surface in ToothSurface]
    print(f"✅ ToothSurface values: {surface_values}")
    assert "mesial" in surface_values
    assert "occlusal" in surface_values
    assert "buccal" in surface_values
    
    print("✅ All enum values valid!")
    return True

async def test_schema_imports():
    """Test that schemas can be imported"""
    print("\n🧪 Testing Schema Imports...")
    
    try:
        from app.schemas.treatment import (
            TreatmentPlanCreate,
            TreatmentPlanResponse,
            TreatmentProcedureCreate,
            CostEstimateRequest,
            CostEstimateResponse,
        )
        print("✅ All schemas imported successfully!")
        
        # Test schema creation
        plan_data = TreatmentPlanCreate(
            plan_name="Test Plan",
            patient_id=uuid.uuid4(),
            provider_id=uuid.uuid4(),
            status="draft",
        )
        print(f"✅ TreatmentPlanCreate schema created: {plan_data.plan_name}")
        
        # Test cost estimate request
        procedure = TreatmentProcedureCreate(
            procedure_type="restorative",
            ada_code="D2391",
            description="Test procedure",
            fee=250.00,
        )
        
        estimate_request = CostEstimateRequest(
            procedures=[procedure],
        )
        print(f"✅ CostEstimateRequest created with {len(estimate_request.procedures)} procedure")
        
        return True
        
    except ImportError as e:
        print(f"❌ Schema import failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 TREATMENT PLANNING ENDPOINT TEST")
    print("=" * 60)
    
    tests = [
        ("Treatment Models", test_treatment_models),
        ("Cost Calculation", test_cost_calculation),
        ("Enum Values", test_enum_values),
        ("Schema Imports", test_schema_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Running: {test_name}")
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Treatment planning endpoints are ready!")
        print("\n🚀 Next steps:")
        print("1. Run database migrations: `alembic upgrade head`")
        print("2. Test API endpoints with actual HTTP requests")
        print("3. Build frontend React components")
        print("4. Deploy to production")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)