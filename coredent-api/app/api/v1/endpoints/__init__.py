"""
API Endpoints Package
All endpoint modules must be imported here for auto-discovery.
"""

from . import auth
from . import patients
from . import appointments
from . import billing
from . import insurance
from . import imaging
from . import treatment
from . import booking
from . import inventory
from . import labs
from . import referrals
from . import reports
from . import payments
from . import edi
from . import accounting
from . import staff
from . import subscriptions
from . import settings as settings_ep
from . import clinic
from . import communications
from . import clinical
from . import patient_portal
from . import documents
from . import health
from . import compliance
from . import mfa
from . import emergency
from . import prescriptions
from . import payroll
from . import stripe
from . import enterprise

__all__ = [
    "auth",
    "patients",
    "appointments",
    "billing",
    "insurance",
    "imaging",
    "treatment",
    "booking",
    "inventory",
    "labs",
    "referrals",
    "reports",
    "payments",
    "edi",
    "accounting",
    "staff",
    "subscriptions",
    "settings_ep",
    "clinic",
    "communications",
    "clinical",
    "patient_portal",
    "documents",
    "health",
    "compliance",
    "mfa",
    "emergency",
    "prescriptions",
    "payroll",
    "stripe",
    "enterprise",
]
