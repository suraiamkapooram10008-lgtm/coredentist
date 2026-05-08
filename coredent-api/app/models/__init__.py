"""
Database Models
SQLAlchemy ORM models for all entities
"""

from app.core.base import Base
from app.models.user import User
from app.models.practice import Practice
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentType, Chair
from app.models.clinical import (
    ClinicalNote,
    NoteType,
    DentalChart,
    ToothCondition,
    ChartingEntry,
    ChartingSymbol,
    ConditionType,
    RestorationStatus,
    SurfaceCode,
    PerioChart,
    PerioChartEntry,
)
from app.models.billing import Invoice, Payment
from app.models.audit import AuditLog, Session
from app.models.insurance import (
    InsuranceCarrier,
    PatientInsurance,
    InsuranceClaim,
    InsurancePreAuthorization,
    Eligibility,
    ExplanationOfBenefits,
)
from app.models.imaging import PatientImage, ImageSeries, ImageTemplate
from app.models.treatment import (
    TreatmentPlan,
    TreatmentPhase,
    TreatmentProcedure,
    ProcedureLibrary,
    TreatmentPlanTemplate,
    TreatmentPlanNote,
    TreatmentPlanStatus,
    ProcedureType,
    ToothSurface,
)
from app.models.booking import (
    BookingPage,
    OnlineBooking,
    WaitlistEntry,
    BookingAvailability,
    BookingNotification,
    BookingPageStatus,
    BookingStatus,
    WaitlistStatus,
)
from app.models.inventory import (
    InventoryItem,
    InventoryTransaction,
    InventoryAlert,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    InventoryCategory,
    InventoryUnit,
    InventoryAlertType,
    VendorContract,
    VendorInvoice,
    ReorderRule,
)
from app.models.lab import (
    Lab,
    LabCase,
    LabInvoice,
    LabCommunication,
    LabCaseStatus,
    LabCaseType,
)
from app.models.referral import (
    ReferralSource1,
    Referral,
    ReferralCommunication,
    ReferralReport,
    ReferralStatus,
    ReferralType,
    ReferralSource,
)
from app.models.communication import (
    MessageTemplate,
    PatientMessage,
    ReminderSchedule,
    Conversation,
    ConversationMessage,
    MessageType,
    MessageDirection,
    MessageStatus,
    ReminderType,
)
from app.models.document import (
    DocumentTemplate,
    Document,
    DocumentSignature,
    SignatureField,
    DocumentCategory,
    DocumentStatus,
    SignatureStatus,
)
from app.models.marketing import (
    Campaign,
    MarketingTemplate,
    CampaignSegment,
    MarketingEmail,
    NewsletterSubscription,
    CampaignStatus,
    CampaignType,
    AudienceType,
)
from app.models.payment import (
    PaymentCard,
    RecurringBilling,
    PaymentTransaction,
    PaymentTerminal,
    PaymentSettings,
    PaymentMethod,
    PaymentStatus,
    CardType,
    RecurringBillingStatus,
)
from app.models.payroll import (
    EmployeeCompensation,
    CommissionStructure,
    Timesheet,
    PayrollPeriod,
    PayrollEntry,
    ProductionLog,
    PTOBalance,
    PTORequest,
    PayType,
    CommissionType,
    TimesheetStatus,
    PayrollPeriodStatus,
    PTOType,
    PTORequestStatus,
)
from app.models.emergency_token import EmergencyToken

from app.models.prescription import (
    Medication,
    PatientAllergy,
    PatientMedication,
    Prescription,
    PrescriptionTemplate,
    DrugInteraction,
    PrescriptionStatus,
    DrugSchedule,
    DrugForm,
    AllergySeverity,
    AllergenType,
    InteractionSeverity,
    FrequencyCode,
)

__all__ = [
    # Core
    "Base",
    "User",
    "Practice",
    "Patient",
    # Appointments
    "Appointment",
    "AppointmentType",
    "Chair",
    # Clinical
    "ClinicalNote",
    "NoteType",
    "DentalChart",
    "ToothCondition",
    "ChartingEntry",
    "ChartingSymbol",
    "ConditionType",
    "RestorationStatus",
    "SurfaceCode",
    "PerioChart",
    "PerioChartEntry",
    # Billing
    "Invoice",
    "Payment",
    # Audit
    "AuditLog",
    "Session",
    # Insurance
    "InsuranceCarrier",
    "PatientInsurance",
    "InsuranceClaim",
    "InsurancePreAuthorization",
    "Eligibility",
    "ExplanationOfBenefits",
    # Imaging
    "PatientImage",
    "ImageSeries",
    "ImageTemplate",
    # Treatment
    "TreatmentPlan",
    "TreatmentPhase",
    "TreatmentProcedure",
    "ProcedureLibrary",
    "TreatmentPlanTemplate",
    "TreatmentPlanNote",
    "TreatmentPlanStatus",
    "ProcedureType",
    "ToothSurface",
    # Booking
    "BookingPage",
    "OnlineBooking",
    "WaitlistEntry",
    "BookingAvailability",
    "BookingNotification",
    "BookingPageStatus",
    "BookingStatus",
    "WaitlistStatus",
    # Inventory
    "InventoryItem",
    "InventoryTransaction",
    "InventoryAlert",
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "InventoryCategory",
    "InventoryUnit",
    "InventoryAlertType",
    "VendorContract",
    "VendorInvoice",
    "ReorderRule",
    # Lab
    "Lab",
    "LabCase",
    "LabInvoice",
    "LabCommunication",
    "LabCaseStatus",
    "LabCaseType",
    # Referral
    "ReferralSource1",
    "Referral",
    "ReferralCommunication",
    "ReferralReport",
    "ReferralStatus",
    "ReferralType",
    "ReferralSource",
    # Communication
    "MessageTemplate",
    "PatientMessage",
    "ReminderSchedule",
    "Conversation",
    "ConversationMessage",
    "MessageType",
    "MessageDirection",
    "MessageStatus",
    "ReminderType",
    # Document
    "DocumentTemplate",
    "Document",
    "DocumentSignature",
    "SignatureField",
    "DocumentCategory",
    "DocumentStatus",
    "SignatureStatus",
    # Marketing
    "Campaign",
    "MarketingTemplate",
    "CampaignSegment",
    "MarketingEmail",
    "NewsletterSubscription",
    "CampaignStatus",
    "CampaignType",
    "AudienceType",
    # Payment Processing
    "PaymentCard",
    "RecurringBilling",
    "PaymentTransaction",
    "PaymentTerminal",
    "PaymentSettings",
    "PaymentMethod",
    "PaymentStatus",
    "CardType",
    "RecurringBillingStatus",
    # Emergency
    "EmergencyToken",
    # Prescription
    "Medication",
    "PatientAllergy",
    "PatientMedication",
    "Prescription",
    "PrescriptionTemplate",
    "DrugInteraction",
    "PrescriptionStatus",
    "DrugSchedule",
    "DrugForm",
    "AllergySeverity",
    "AllergenType",
    "InteractionSeverity",
    "FrequencyCode",
    # Payroll
    "EmployeeCompensation",
    "CommissionStructure",
    "Timesheet",
    "PayrollPeriod",
    "PayrollEntry",
    "ProductionLog",
    "PTOBalance",
    "PTORequest",
    "PayType",
    "CommissionType",
    "TimesheetStatus",
    "PayrollPeriodStatus",
    "PTOType",
    "PTORequestStatus",
]
