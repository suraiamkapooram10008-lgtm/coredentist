"""
Prescription Service
Business logic for prescription management, drug interaction checking,
and allergy verification.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import uuid
import httpx
import logging

from app.models.prescription import (
    Prescription,
    Medication,
    PatientAllergy,
    PatientMedication,
    PrescriptionTemplate,
    DrugInteraction,
    PrescriptionStatus,
    DrugSchedule,
    InteractionSeverity,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class PrescriptionService:
    """Handles prescription creation, validation, and safety checks"""

    # Common dental medications pre-seeded for quick access
    COMMON_DENTAL_MEDICATIONS = [
        {
            "name": "Amoxicillin",
            "generic_name": "amoxicillin",
            "drug_class": "Antibiotic - Penicillin",
            "form": "capsule",
            "strength": "500mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Dental infections, prophylaxis for endocarditis",
            "default_dosage": "500mg",
            "default_frequency": "tid",
            "default_duration_days": 7,
            "default_quantity": 21,
        },
        {
            "name": "Ibuprofen",
            "generic_name": "ibuprofen",
            "drug_class": "NSAID",
            "form": "tablet",
            "strength": "600mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Post-operative pain, inflammation",
            "default_dosage": "600mg",
            "default_frequency": "q6h",
            "default_duration_days": 5,
            "default_quantity": 20,
        },
        {
            "name": "Clindamycin",
            "generic_name": "clindamycin",
            "drug_class": "Antibiotic - Lincosamide",
            "form": "capsule",
            "strength": "300mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Dental infections (penicillin allergy alternative)",
            "default_dosage": "300mg",
            "default_frequency": "qid",
            "default_duration_days": 7,
            "default_quantity": 28,
        },
        {
            "name": "Acetaminophen with Codeine",
            "generic_name": "acetaminophen/codeine",
            "drug_class": "Analgesic - Opioid Combination",
            "form": "tablet",
            "strength": "300mg/30mg",
            "route": "oral",
            "schedule": "schedule_iii",
            "is_controlled": True,
            "common_dental_uses": "Moderate to severe dental pain",
            "default_dosage": "1-2 tablets",
            "default_frequency": "q4h",
            "default_duration_days": 3,
            "default_quantity": 18,
        },
        {
            "name": "Metronidazole",
            "generic_name": "metronidazole",
            "drug_class": "Antibiotic - Nitroimidazole",
            "form": "tablet",
            "strength": "500mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Periodontal infections, anaerobic infections",
            "default_dosage": "500mg",
            "default_frequency": "tid",
            "default_duration_days": 7,
            "default_quantity": 21,
        },
        {
            "name": "Chlorhexidine Gluconate",
            "generic_name": "chlorhexidine gluconate",
            "drug_class": "Antimicrobial Rinse",
            "form": "rinse",
            "strength": "0.12%",
            "route": "oral rinse",
            "schedule": "rx",
            "common_dental_uses": "Gingivitis, post-surgical rinse",
            "default_dosage": "15mL",
            "default_frequency": "bid",
            "default_duration_days": 14,
            "default_quantity": 1,
        },
        {
            "name": "Hydrocodone/Acetaminophen",
            "generic_name": "hydrocodone/acetaminophen",
            "drug_class": "Analgesic - Opioid Combination",
            "form": "tablet",
            "strength": "5mg/325mg",
            "route": "oral",
            "schedule": "schedule_ii",
            "is_controlled": True,
            "common_dental_uses": "Severe post-operative pain",
            "default_dosage": "1 tablet",
            "default_frequency": "q4h",
            "default_duration_days": 3,
            "default_quantity": 12,
        },
        {
            "name": "Penicillin V",
            "generic_name": "penicillin v potassium",
            "drug_class": "Antibiotic - Penicillin",
            "form": "tablet",
            "strength": "500mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Dental infections, periapical abscess",
            "default_dosage": "500mg",
            "default_frequency": "qid",
            "default_duration_days": 7,
            "default_quantity": 28,
        },
        {
            "name": "Dexamethasone",
            "generic_name": "dexamethasone",
            "drug_class": "Corticosteroid",
            "form": "tablet",
            "strength": "4mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Post-surgical swelling, oral surgery",
            "default_dosage": "4mg",
            "default_frequency": "qd",
            "default_duration_days": 3,
            "default_quantity": 3,
        },
        {
            "name": "Fluconazole",
            "generic_name": "fluconazole",
            "drug_class": "Antifungal",
            "form": "tablet",
            "strength": "100mg",
            "route": "oral",
            "schedule": "rx",
            "common_dental_uses": "Oral candidiasis (thrush)",
            "default_dosage": "100mg",
            "default_frequency": "qd",
            "default_duration_days": 14,
            "default_quantity": 14,
        },
    ]

    @staticmethod
    def generate_rx_number(practice_id: UUID) -> str:
        """Generate a unique prescription number"""
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"RX-{short_uuid}"

    @staticmethod
    async def seed_common_medications(db: AsyncSession) -> int:
        """Seed common dental medications into the database"""
        count = 0
        for med_data in PrescriptionService.COMMON_DENTAL_MEDICATIONS:
            # Check if medication already exists
            result = await db.execute(
                select(Medication).where(
                    Medication.name == med_data["name"],
                    Medication.strength == med_data["strength"],
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                schedule_val = med_data.pop("schedule", "rx")
                is_controlled = med_data.pop("is_controlled", False)
                medication = Medication(
                    schedule=DrugSchedule(schedule_val),
                    is_controlled=is_controlled,
                    **med_data
                )
                db.add(medication)
                count += 1
        if count > 0:
            await db.commit()
        return count

    @staticmethod
    async def search_medications_local(
        db: AsyncSession,
        query: str,
        limit: int = 20,
    ) -> List[Medication]:
        """Search local medication database"""
        search_pattern = f"%{query}%"
        result = await db.execute(
            select(Medication)
            .where(
                and_(
                    Medication.is_active == True,
                    or_(
                        Medication.name.ilike(search_pattern),
                        Medication.generic_name.ilike(search_pattern),
                        Medication.drug_class.ilike(search_pattern),
                    )
                )
            )
            .order_by(Medication.name)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def search_medications_openfda(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search OpenFDA drug database for medications"""
        results = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.fda.gov/drug/label.json",
                    params={
                        "search": f'openfda.brand_name:"{query}" OR openfda.generic_name:"{query}"',
                        "limit": limit,
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("results", []):
                        openfda = item.get("openfda", {})
                        results.append({
                            "name": (openfda.get("brand_name", [""])[0] or "").title(),
                            "generic_name": (openfda.get("generic_name", [""])[0] or "").lower(),
                            "ndc_code": (openfda.get("product_ndc", [""])[0] or ""),
                            "rxcui": (openfda.get("rxcui", [""])[0] or ""),
                            "drug_class": (openfda.get("pharm_class_epc", [""])[0] if openfda.get("pharm_class_epc") else ""),
                            "form": (openfda.get("dosage_form", [""])[0] or "").lower(),
                            "strength": "",
                            "route": (openfda.get("route", [""])[0] or "").lower(),
                            "manufacturer": (openfda.get("manufacturer_name", [""])[0] or ""),
                            "source": "openfda",
                        })
        except Exception as e:
            logger.warning(f"OpenFDA search failed: {e}")
        return results

    @staticmethod
    async def check_drug_interactions(
        db: AsyncSession,
        medication_name: str,
        patient_id: UUID,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Check for drug-drug interactions and allergy conflicts.
        Returns (interactions, allergy_warnings)
        """
        interactions = []
        allergy_warnings = []

        # Get patient's current active medications
        result = await db.execute(
            select(PatientMedication).where(
                and_(
                    PatientMedication.patient_id == patient_id,
                    PatientMedication.is_active == True,
                )
            )
        )
        current_meds = result.scalars().all()

        # Check drug interactions against current medications
        med_name_lower = medication_name.lower()
        for current_med in current_meds:
            current_name = current_med.medication_name.lower()

            # Check local interaction database
            result = await db.execute(
                select(DrugInteraction).where(
                    and_(
                        DrugInteraction.is_active == True,
                        or_(
                            and_(
                                func.lower(DrugInteraction.drug_a_name).contains(med_name_lower),
                                func.lower(DrugInteraction.drug_b_name).contains(current_name),
                            ),
                            and_(
                                func.lower(DrugInteraction.drug_a_name).contains(current_name),
                                func.lower(DrugInteraction.drug_b_name).contains(med_name_lower),
                            ),
                        )
                    )
                )
            )
            db_interactions = result.scalars().all()
            for interaction in db_interactions:
                interactions.append({
                    "drug_a": interaction.drug_a_name,
                    "drug_b": interaction.drug_b_name,
                    "severity": interaction.severity.value,
                    "description": interaction.description,
                    "clinical_effects": interaction.clinical_effects,
                    "management": interaction.management,
                    "source": interaction.source or "local",
                })

        # Check patient allergies
        result = await db.execute(
            select(PatientAllergy).where(
                and_(
                    PatientAllergy.patient_id == patient_id,
                    PatientAllergy.is_active == True,
                )
            )
        )
        allergies = result.scalars().all()

        for allergy in allergies:
            allergen_lower = allergy.allergen.lower()
            # Check if the prescribed medication matches any allergy
            if (allergen_lower in med_name_lower or
                med_name_lower in allergen_lower):
                allergy_warnings.append({
                    "allergen": allergy.allergen,
                    "allergen_type": allergy.allergen_type.value,
                    "reaction": allergy.reaction,
                    "severity": allergy.severity.value,
                    "message": f"Patient has a documented {allergy.severity.value} allergy to {allergy.allergen}",
                })

            # Check drug class allergies (e.g., "Penicillin" class)
            if allergy.allergen_type.value == "drug_class":
                # Check if the medication belongs to the allergic drug class
                med_result = await db.execute(
                    select(Medication).where(
                        func.lower(Medication.name) == med_name_lower
                    )
                )
                med = med_result.scalar_one_or_none()
                if med and med.drug_class and allergen_lower in med.drug_class.lower():
                    allergy_warnings.append({
                        "allergen": allergy.allergen,
                        "allergen_type": "drug_class",
                        "reaction": allergy.reaction,
                        "severity": allergy.severity.value,
                        "message": f"Medication belongs to drug class '{med.drug_class}' — patient allergic to '{allergy.allergen}'",
                    })

        return interactions, allergy_warnings

    @staticmethod
    async def create_prescription(
        db: AsyncSession,
        practice_id: UUID,
        provider: User,
        prescription_data: Dict[str, Any],
    ) -> Prescription:
        """Create a new prescription with safety checks"""

        patient_id = prescription_data.get("patient_id")

        # Generate Rx number
        rx_number = PrescriptionService.generate_rx_number(practice_id)

        # Determine if controlled substance
        medication_id = prescription_data.get("medication_id")
        is_controlled = False
        dea_schedule = None
        if medication_id:
            result = await db.execute(
                select(Medication).where(Medication.id == medication_id)
            )
            med = result.scalar_one_or_none()
            if med:
                is_controlled = med.is_controlled
                dea_schedule = med.schedule

        # Run interaction/allergy checks
        medication_name = prescription_data.get("medication_name", "")
        interactions, allergy_warnings = await PrescriptionService.check_drug_interactions(
            db, medication_name, patient_id
        )

        # Set prescribed date default
        prescribed_date = prescription_data.get("prescribed_date") or date.today()

        # Calculate expiration (1 year for non-controlled, 90 days for Schedule II)
        if is_controlled and dea_schedule == DrugSchedule.SCHEDULE_II:
            expiration_date = prescribed_date + timedelta(days=90)
        else:
            expiration_date = prescribed_date + timedelta(days=365)

        # Build prescription
        refills = prescription_data.get("refills", 0)
        # Schedule II drugs cannot have refills
        if is_controlled and dea_schedule == DrugSchedule.SCHEDULE_II:
            refills = 0

        prescription = Prescription(
            practice_id=practice_id,
            patient_id=patient_id,
            provider_id=provider.id,
            medication_id=medication_id,
            appointment_id=prescription_data.get("appointment_id"),
            rx_number=rx_number,
            medication_name=medication_name,
            generic_name=prescription_data.get("generic_name"),
            strength=prescription_data.get("strength"),
            form=prescription_data.get("form", "tablet"),
            route=prescription_data.get("route", "oral"),
            dosage=prescription_data["dosage"],
            frequency=prescription_data["frequency"],
            frequency_display=prescription_data.get("frequency_display"),
            duration_days=prescription_data.get("duration_days"),
            quantity=prescription_data["quantity"],
            quantity_unit=prescription_data.get("quantity_unit", "tablets"),
            refills=refills,
            refills_remaining=refills,
            sig=prescription_data.get("sig"),
            notes_to_pharmacist=prescription_data.get("notes_to_pharmacist"),
            internal_notes=prescription_data.get("internal_notes"),
            dispense_as_written=prescription_data.get("dispense_as_written", False),
            substitution_allowed=prescription_data.get("substitution_allowed", True),
            is_controlled=is_controlled,
            dea_schedule=dea_schedule,
            pharmacy_name=prescription_data.get("pharmacy_name"),
            pharmacy_phone=prescription_data.get("pharmacy_phone"),
            pharmacy_fax=prescription_data.get("pharmacy_fax"),
            pharmacy_address=prescription_data.get("pharmacy_address"),
            status=prescription_data.get("status", PrescriptionStatus.DRAFT),
            prescribed_date=prescribed_date,
            expiration_date=expiration_date,
            interaction_check_performed=True,
            interaction_check_results=interactions,
            allergy_check_performed=True,
            allergy_check_results=allergy_warnings,
            diagnosis_codes=prescription_data.get("diagnosis_codes", []),
        )

        db.add(prescription)
        await db.commit()
        await db.refresh(prescription)

        return prescription

    @staticmethod
    async def cancel_prescription(
        db: AsyncSession,
        prescription: Prescription,
        reason: str,
    ) -> Prescription:
        """Cancel an active prescription"""
        prescription.status = PrescriptionStatus.CANCELLED
        prescription.cancelled_date = date.today()
        prescription.cancellation_reason = reason
        await db.commit()
        await db.refresh(prescription)
        return prescription

    @staticmethod
    def get_frequency_display(code: str) -> str:
        """Convert frequency code to human-readable string"""
        frequency_map = {
            "qd": "Once daily",
            "bid": "Twice daily",
            "tid": "Three times daily",
            "qid": "Four times daily",
            "q4h": "Every 4 hours",
            "q6h": "Every 6 hours",
            "q8h": "Every 8 hours",
            "q12h": "Every 12 hours",
            "prn": "As needed",
            "once": "One time only",
            "weekly": "Once weekly",
        }
        return frequency_map.get(code, code)
