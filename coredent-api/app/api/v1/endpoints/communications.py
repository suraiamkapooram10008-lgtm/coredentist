"""
Communications API Endpoints
Patient messaging, SMS/email reminders, two-way messaging
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user, get_current_practice
from app.services.communications_service import CommunicationsEngine
from app.models.user import User
from app.models.practice import Practice
from app.models.communication import (
    MessageTemplate, PatientMessage, ReminderSchedule, 
    Conversation, ConversationMessage, MessageType, MessageStatus, ReminderType
)
from app.models.patient import Patient
from app.schemas.communication import (
    MessageTemplateCreate, MessageTemplateUpdate, MessageTemplate,
    PatientMessageCreate, PatientMessageUpdate, PatientMessage,
    ReminderScheduleCreate, ReminderScheduleUpdate, ReminderSchedule,
    ConversationCreate, ConversationUpdate, Conversation,
    ConversationMessageCreate, ConversationMessage,
    CommunicationSummary, MessageStats, ReminderStats
)

router = APIRouter()


# ============================================
# Message Templates
# ============================================

@router.get("/templates", response_model=List[MessageTemplate], tags=["Communications - Templates"])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    message_type: Optional[MessageType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """List all message templates for the current practice"""
    query = db.query(MessageTemplate).filter(
        MessageTemplate.practice_id == current_practice.id
    )

    if category:
        query = query.filter(MessageTemplate.category == category)
    if is_active is not None:
        query = query.filter(MessageTemplate.is_active == is_active)
    if message_type:
        query = query.filter(MessageTemplate.message_type == message_type)

    templates = query.order_by(MessageTemplate.is_default.desc(), MessageTemplate.name).offset(skip).limit(limit).all()
    return templates


@router.get("/templates/{template_id}", response_model=MessageTemplate, tags=["Communications - Templates"])
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get a specific template by ID"""
    template = db.query(MessageTemplate).filter(
        and_(
            MessageTemplate.id == template_id,
            MessageTemplate.practice_id == current_practice.id
        )
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post("/templates", response_model=MessageTemplate, status_code=status.HTTP_201_CREATED, tags=["Communications - Templates"])
def create_template(
    template: MessageTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Create a new message template"""
    # If this is set as default, unset other defaults
    if template.is_default:
        db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.practice_id == current_practice.id,
                MessageTemplate.message_type == template.message_type,
                MessageTemplate.is_default == True
            )
        ).update({"is_default": False})

    db_template = MessageTemplate(
        **template.model_dump(),
        practice_id=current_practice.id,
        variables=template.variables.model_dump_json() if template.variables else None
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.put("/templates/{template_id}", response_model=MessageTemplate, tags=["Communications - Templates"])
def update_template(
    template_id: str,
    template_update: MessageTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Update an existing template"""
    db_template = db.query(MessageTemplate).filter(
        and_(
            MessageTemplate.id == template_id,
            MessageTemplate.practice_id == current_practice.id
        )
    ).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    # If setting as default, unset other defaults
    if template_update.is_default:
        db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.practice_id == current_practice.id,
                MessageTemplate.message_type == db_template.message_type,
                MessageTemplate.is_default == True,
                MessageTemplate.id != template_id
            )
        ).update({"is_default": False})

    update_data = template_update.model_dump(exclude_unset=True)
    if 'variables' in update_data and update_data['variables'] is not None:
        update_data['variables'] = update_data['variables'].model_dump_json()

    for field, value in update_data.items():
        setattr(db_template, field, value)

    db.commit()
    db.refresh(db_template)
    return db_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Communications - Templates"])
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Delete a template"""
    db_template = db.query(MessageTemplate).filter(
        and_(
            MessageTemplate.id == template_id,
            MessageTemplate.practice_id == current_practice.id
        )
    ).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(db_template)
    db.commit()
    return None


# ============================================
# Patient Messages
# ============================================

@router.get("/messages", response_model=List[PatientMessage], tags=["Communications - Messages"])
def list_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    patient_id: Optional[str] = None,
    message_type: Optional[MessageType] = None,
    status: Optional[MessageStatus] = None,
    direction: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """List patient messages"""
    query = db.query(PatientMessage).filter(
        PatientMessage.practice_id == current_practice.id
    )

    if patient_id:
        query = query.filter(PatientMessage.patient_id == patient_id)
    if message_type:
        query = query.filter(PatientMessage.message_type == message_type)
    if status:
        query = query.filter(PatientMessage.status == status)
    if direction:
        query = query.filter(PatientMessage.direction == direction)
    if date_from:
        query = query.filter(PatientMessage.created_at >= date_from)
    if date_to:
        query = query.filter(PatientMessage.created_at <= date_to)

    messages = query.order_by(PatientMessage.created_at.desc()).offset(skip).limit(limit).all()
    return messages


@router.get("/messages/{message_id}", response_model=PatientMessage, tags=["Communications - Messages"])
def get_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get a specific message by ID"""
    message = db.query(PatientMessage).filter(
        and_(
            PatientMessage.id == message_id,
            PatientMessage.practice_id == current_practice.id
        )
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.post("/messages", response_model=PatientMessage, status_code=status.HTTP_201_CREATED, tags=["Communications - Messages"])
def send_message(
    message: PatientMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Send a message to a patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(
        and_(
            Patient.id == message.patient_id,
            Patient.practice_id == current_practice.id
        )
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get template if provided
    template = None
    if message.template_id:
        template = db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.id == message.template_id,
                MessageTemplate.practice_id == current_practice.id
            )
        ).first()
        if template:
            # Increment template usage
            template.times_used += 1

    # Set recipient info from patient if not provided
    recipient_phone = message.recipient_phone or patient.phone
    recipient_email = message.recipient_email or patient.email

    db_message = PatientMessage(
        **message.model_dump(exclude={'template_id', 'appointment_id', 'parent_message_id'}),
        practice_id=current_practice.id,
        user_id=current_user.id,
        recipient_phone=recipient_phone,
        recipient_email=recipient_email,
        status=MessageStatus.PENDING if not message.scheduled_at else MessageStatus.PENDING
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    from app.core.communication_queue import send_message_task
    send_message_task(str(db_message.id))

    return db_message


@router.put("/messages/{message_id}", response_model=PatientMessage, tags=["Communications - Messages"])
def update_message(
    message_id: str,
    message_update: PatientMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Update a message (e.g., mark as sent, update status)"""
    db_message = db.query(PatientMessage).filter(
        and_(
            PatientMessage.id == message_id,
            PatientMessage.practice_id == current_practice.id
        )
    ).first()

    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    update_data = message_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_message, field, value)

    db.commit()
    db.refresh(db_message)
    return db_message


# ============================================
# Reminder Schedules
# ============================================

@router.get("/reminders", response_model=List[ReminderSchedule], tags=["Communications - Reminders"])
def list_reminders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    reminder_type: Optional[ReminderType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """List all reminder schedules"""
    query = db.query(ReminderSchedule).filter(
        ReminderSchedule.practice_id == current_practice.id
    )

    if is_active is not None:
        query = query.filter(ReminderSchedule.is_active == is_active)
    if reminder_type:
        query = query.filter(ReminderSchedule.reminder_type == reminder_type)

    reminders = query.order_by(ReminderSchedule.name).offset(skip).limit(limit).all()
    return reminders


@router.get("/reminders/{reminder_id}", response_model=ReminderSchedule, tags=["Communications - Reminders"])
def get_reminder(
    reminder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get a specific reminder schedule"""
    reminder = db.query(ReminderSchedule).filter(
        and_(
            ReminderSchedule.id == reminder_id,
            ReminderSchedule.practice_id == current_practice.id
        )
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder schedule not found")

    return reminder


@router.post("/reminders", response_model=ReminderSchedule, status_code=status.HTTP_201_CREATED, tags=["Communications - Reminders"])
def create_reminder(
    reminder: ReminderScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Create a new reminder schedule"""
    # Verify template exists
    template = db.query(MessageTemplate).filter(
        and_(
            MessageTemplate.id == reminder.template_id,
            MessageTemplate.practice_id == current_practice.id
        )
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db_reminder = ReminderSchedule(
        **reminder.model_dump(),
        practice_id=current_practice.id,
        patient_types=reminder.patient_types.model_dump_json() if reminder.patient_types else None
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.put("/reminders/{reminder_id}", response_model=ReminderSchedule, tags=["Communications - Reminders"])
def update_reminder(
    reminder_id: str,
    reminder_update: ReminderScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Update a reminder schedule"""
    db_reminder = db.query(ReminderSchedule).filter(
        and_(
            ReminderSchedule.id == reminder_id,
            ReminderSchedule.practice_id == current_practice.id
        )
    ).first()

    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder schedule not found")

    update_data = reminder_update.model_dump(exclude_unset=True)
    if 'patient_types' in update_data and update_data['patient_types'] is not None:
        update_data['patient_types'] = update_data['patient_types'].model_dump_json()

    for field, value in update_data.items():
        setattr(db_reminder, field, value)

    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Communications - Reminders"])
def delete_reminder(
    reminder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Delete a reminder schedule"""
    db_reminder = db.query(ReminderSchedule).filter(
        and_(
            ReminderSchedule.id == reminder_id,
            ReminderSchedule.practice_id == current_practice.id
        )
    ).first()

    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder schedule not found")

    db.delete(db_reminder)
    db.commit()
    return None


# ============================================
# Conversations
# ============================================

@router.get("/conversations", response_model=List[Conversation], tags=["Communications - Conversations"])
def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """List all conversations"""
    query = db.query(Conversation).filter(
        Conversation.practice_id == current_practice.id
    )

    if status:
        query = query.filter(Conversation.status == status)
    if patient_id:
        query = query.filter(Conversation.patient_id == patient_id)

    conversations = query.order_by(Conversation.last_message_at.desc().nullsfirst()).offset(skip).limit(limit).all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=Conversation, tags=["Communications - Conversations"])
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get a specific conversation"""
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.practice_id == current_practice.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED, tags=["Communications - Conversations"])
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Create a new conversation"""
    # Verify patient exists
    patient = db.query(Patient).filter(
        and_(
            Patient.id == conversation.patient_id,
            Patient.practice_id == current_practice.id
        )
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if conversation already exists
    existing = db.query(Conversation).filter(
        and_(
            Conversation.practice_id == current_practice.id,
            Conversation.patient_id == conversation.patient_id,
            Conversation.channel == conversation.channel,
            Conversation.status == 'active'
        )
    ).first()

    if existing:
        return existing

    db_conversation = Conversation(
        **conversation.model_dump(),
        practice_id=current_practice.id,
        assigned_user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.put("/conversations/{conversation_id}", response_model=Conversation, tags=["Communications - Conversations"])
def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Update a conversation"""
    db_conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.practice_id == current_practice.id
        )
    ).first()

    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    update_data = conversation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_conversation, field, value)

    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[ConversationMessage], tags=["Communications - Conversations"])
def get_conversation_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get messages in a conversation"""
    # Verify conversation exists
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.practice_id == current_practice.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(ConversationMessage.created_at.asc()).offset(skip).limit(limit).all()

    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationMessage, status_code=status.HTTP_201_CREATED, tags=["Communications - Conversations"])
def send_conversation_message(
    conversation_id: str,
    message: ConversationMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Send a message in a conversation (Staff -> Patient)"""
    # Verify conversation exists
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.practice_id == current_practice.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    engine = CommunicationsEngine(db)

    # Actually send the SMS if channel is SMS
    if conversation.channel == MessageType.SMS:
        patient = db.query(Patient).get(conversation.patient_id)
        if patient and patient.phone:
            engine.send_sms(patient.phone, message.content, current_practice)

    db_message = ConversationMessage(
        **message.model_dump(),
        conversation_id=conversation_id,
        sender_id=current_user.id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Update conversation's last message info
    conversation.last_message_at = db_message.created_at
    conversation.last_message_preview = message.content[:255]
    if message.sender_type == 'patient':
        conversation.unread_count += 1
    db.commit()

    return db_message


# ============================================
# Engine & Webhooks
# ============================================

@router.post("/webhook/twilio", tags=["Communications - Webhooks"])
async def twilio_inbound_sms(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Twilio Incoming Webhook. 
    Routes inbound text messages from patients to the Two-Way SMS system.
    """
    engine = CommunicationsEngine(db)
    success = engine.handle_inbound_sms(From, To, Body, MessageSid)

    # Return empty TwiML response to acknowledge receipt
    return "<Response></Response>"

@router.post("/engine/run-recalls", tags=["Communications - Engine"])
def trigger_recall_engine(db: Session = Depends(get_db)):
    """
    Manually trigger the Automated Recall System Engine.
    In production, this is called by a cron job (e.g. AWS EventBridge) daily at 8AM.
    """
    engine = CommunicationsEngine(db)
    engine.process_automated_recalls()
    return {"status": "success", "message": "Automated recall engine executed"}


# ============================================
# Communication Settings
# ============================================

@router.get("/settings", response_model=CommunicationSummary, tags=["Communications - Settings"])
def get_communication_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Get communication settings and statistics"""
    # Message stats
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    messages_sent = db.query(PatientMessage).filter(
        and_(
            PatientMessage.practice_id == current_practice.id,
            PatientMessage.sent_at >= week_ago
        )
    ).count()

    messages_delivered = db.query(PatientMessage).filter(
        and_(
            PatientMessage.practice_id == current_practice.id,
            PatientMessage.status == MessageStatus.DELIVERED,
            PatientMessage.delivered_at >= week_ago
        )
    ).count()

    messages_failed = db.query(PatientMessage).filter(
        and_(
            PatientMessage.practice_id == current_practice.id,
            PatientMessage.status == MessageStatus.FAILED,
            PatientMessage.sent_at >= week_ago
        )
    ).count()

    delivery_rate = (messages_delivered / messages_sent * 100) if messages_sent > 0 else 0.0

    # Reminder stats
    reminders_scheduled = db.query(ReminderSchedule).filter(
        and_(
            ReminderSchedule.practice_id == current_practice.id,
            ReminderSchedule.is_active == True
        )
    ).count()

    reminders_pending = db.query(PatientMessage).filter(
        and_(
            PatientMessage.practice_id == current_practice.id,
            PatientMessage.status == MessageStatus.PENDING,
            PatientMessage.scheduled_at.isnot(None)
        )
    ).count()

    # Conversation stats
    active_conversations = db.query(Conversation).filter(
        and_(
            Conversation.practice_id == current_practice.id,
            Conversation.status == 'active'
        )
    ).count()

    unread_messages = db.query(Conversation).filter(
        and_(
            Conversation.practice_id == current_practice.id,
            Conversation.status == 'active'
        )
    ).with_entities(Conversation.unread_count).scalar() or 0

    return CommunicationSummary(
        messages=MessageStats(
            total_sent=messages_sent,
            total_delivered=messages_delivered,
            total_failed=messages_failed,
            delivery_rate=round(delivery_rate, 1),
            total_cost="0.00"  # Would need to calculate from message costs
        ),
        reminders=ReminderStats(
            total_scheduled=reminders_scheduled,
            total_sent=0,  # Would need to track separately
            total_delivered=0,
            pending=reminders_pending,
            failed=0
        ),
        active_conversations=active_conversations,
        unread_messages=unread_messages
    )