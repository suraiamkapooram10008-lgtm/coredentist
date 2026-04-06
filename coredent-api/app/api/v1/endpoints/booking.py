"""
Online Booking Endpoints
Public and admin endpoints for online booking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Any
import json
import uuid as uuid_lib
import secrets
import string

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.core.email import email_service
from app.core.limiter import limiter
from app.core.audit import log_audit_event
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
from app.models.patient import Patient
from app.models.practice import Practice
from app.models.appointment import Appointment, AppointmentType
from app.schemas.booking import (
    BookingPageCreate,
    BookingPageUpdate,
    BookingPageResponse,
    BookingPageListResponse,
    BookingPagePublicResponse,
    OnlineBookingCreate,
    OnlineBookingUpdate,
    OnlineBookingResponse,
    OnlineBookingListResponse,
    WaitlistEntryCreate,
    WaitlistEntryUpdate,
    WaitlistEntryResponse,
    WaitlistEntryListResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    DayAvailability,
    TimeSlot,
    EmailVerificationRequest,
    PhoneVerificationRequest,
    VerificationResponse,
    BookingConfirmationRequest,
    BookingConfirmationResponse,
    BookingAnalytics,
)
from app.api.deps import verify_csrf

router = APIRouter()


# Helper Functions

def generate_confirmation_code() -> str:
    """Generate a unique confirmation code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def generate_verification_token() -> str:
    """Generate email verification token"""
    return secrets.token_urlsafe(32)


def generate_verification_code() -> str:
    """Generate 6-digit phone verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


# Booking Page Endpoints (Admin)

@router.get("/pages/", response_model=BookingPageListResponse)
async def list_booking_pages(
    request: Request,
    status: Optional[BookingPageStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List booking pages for the current practice
    """
    query = select(BookingPage).where(BookingPage.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(BookingPage.status == status)
    
    query = query.order_by(BookingPage.created_at.desc())
    
    result = await db.execute(query)
    pages = result.scalars().all()
    
    return BookingPageListResponse(
        pages=pages,
        count=len(pages),
    )


@router.post("/pages/", response_model=BookingPageResponse)
async def create_booking_page(
    page_data: BookingPageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new booking page
    """
    # Check for duplicate slug
    result = await db.execute(
        select(BookingPage).where(BookingPage.page_slug == page_data.page_slug)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking page with this slug already exists",
        )
    
    # Convert business_hours to dict
    business_hours_dict = {}
    if page_data.business_hours:
        for day, hours in page_data.business_hours.items():
            business_hours_dict[day] = hours.dict()
    
    # Convert intake_form_fields to list of dicts
    intake_form_fields_list = []
    if page_data.intake_form_fields:
        intake_form_fields_list = [field.dict() for field in page_data.intake_form_fields]
    
    page = BookingPage(
        practice_id=current_user.practice_id,
        page_slug=page_data.page_slug,
        page_title=page_data.page_title,
        welcome_message=page_data.welcome_message,
        logo_url=page_data.logo_url,
        primary_color=page_data.primary_color,
        background_image_url=page_data.background_image_url,
        allow_new_patients=page_data.allow_new_patients,
        allow_existing_patients=page_data.allow_existing_patients,
        require_phone_verification=page_data.require_phone_verification,
        require_email_verification=page_data.require_email_verification,
        booking_window_days=page_data.booking_window_days,
        min_notice_hours=page_data.min_notice_hours,
        max_bookings_per_day=page_data.max_bookings_per_day,
        allowed_appointment_types=[str(id) for id in page_data.allowed_appointment_types],
        allowed_providers=[str(id) for id in page_data.allowed_providers],
        business_hours=business_hours_dict,
        blocked_dates=[d.isoformat() for d in page_data.blocked_dates],
        intake_form_fields=intake_form_fields_list,
        require_insurance_info=page_data.require_insurance_info,
        require_medical_history=page_data.require_medical_history,
        send_confirmation_email=page_data.send_confirmation_email,
        send_confirmation_sms=page_data.send_confirmation_sms,
        send_reminder_email=page_data.send_reminder_email,
        send_reminder_sms=page_data.send_reminder_sms,
        reminder_hours_before=page_data.reminder_hours_before,
        status=page_data.status,
        meta_title=page_data.meta_title,
        meta_description=page_data.meta_description,
        meta_keywords=page_data.meta_keywords,
    )
    
    db.add(page)
    await db.commit()
    await db.refresh(page)
    
    return page


@router.get("/pages/{page_id}", response_model=BookingPageResponse)
async def get_booking_page(
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get booking page by ID
    """
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.id == page_id,
            BookingPage.practice_id == current_user.practice_id,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found",
        )
    
    return page


@router.put("/pages/{page_id}", response_model=BookingPageResponse)
async def update_booking_page(
    page_id: str,
    page_data: BookingPageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update booking page
    """
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.id == page_id,
            BookingPage.practice_id == current_user.practice_id,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found",
        )
    
    update_data = page_data.dict(exclude_unset=True)
    
    # Convert business_hours if provided
    if 'business_hours' in update_data and update_data['business_hours']:
        business_hours_dict = {}
        for day, hours in update_data['business_hours'].items():
            business_hours_dict[day] = hours.dict() if hasattr(hours, 'dict') else hours
        update_data['business_hours'] = business_hours_dict
    
    # Convert intake_form_fields if provided
    if 'intake_form_fields' in update_data and update_data['intake_form_fields']:
        intake_form_fields_list = []
        for field in update_data['intake_form_fields']:
            intake_form_fields_list.append(field.dict() if hasattr(field, 'dict') else field)
        update_data['intake_form_fields'] = intake_form_fields_list
    
    # Convert dates if provided
    if 'blocked_dates' in update_data and update_data['blocked_dates']:
        update_data['blocked_dates'] = [d.isoformat() if hasattr(d, 'isoformat') else d for d in update_data['blocked_dates']]
    
    for field, value in update_data.items():
        setattr(page, field, value)
    
    await db.commit()
    await db.refresh(page)
    
    return page


# Public Booking Page Endpoint

@router.get("/public/{page_slug}", response_model=BookingPagePublicResponse)
async def get_public_booking_page(
    page_slug: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get public booking page by slug (no authentication required)
    """
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.page_slug == page_slug,
            BookingPage.status == BookingPageStatus.ACTIVE,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found or inactive",
        )
    
    # Increment view count
    page.total_views += 1
    await db.commit()
    
    # Return only public-facing data
    return BookingPagePublicResponse(
        page_slug=page.page_slug,
        page_title=page.page_title,
        welcome_message=page.welcome_message,
        logo_url=page.logo_url,
        primary_color=page.primary_color,
        background_image_url=page.background_image_url,
        allow_new_patients=page.allow_new_patients,
        allow_existing_patients=page.allow_existing_patients,
        require_phone_verification=page.require_phone_verification,
        require_email_verification=page.require_email_verification,
        booking_window_days=page.booking_window_days,
        min_notice_hours=page.min_notice_hours,
        business_hours=page.business_hours,
        blocked_dates=page.blocked_dates,
        intake_form_fields=page.intake_form_fields,
        require_insurance_info=page.require_insurance_info,
        require_medical_history=page.require_medical_history,
    )


# Online Booking Endpoints

@router.post("/public/{page_slug}/book", response_model=OnlineBookingPublicResponse)
@limiter.limit("2/hour")
async def create_online_booking(
    request: Request,
    page_slug: str,
    booking_data: OnlineBookingCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new online booking (public endpoint, no authentication)
    """
    # Get booking page
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.page_slug == page_slug,
            BookingPage.status == BookingPageStatus.ACTIVE,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found or inactive",
        )
    
    # EXPERT HARDENING: Anti-Spam / Ghost Booking Prevention
    # Check if this email or phone already has a pending booking in the last 24 hours
    cooldown_window = datetime.now() - timedelta(hours=24)
    duplicate_check = await db.execute(
        select(OnlineBooking).where(
            and_(
                OnlineBooking.practice_id == page.practice_id,
                or_(
                    OnlineBooking.email == booking_data.email,
                    OnlineBooking.phone == booking_data.phone
                ),
                OnlineBooking.status == BookingStatus.PENDING,
                OnlineBooking.submitted_at >= cooldown_window
            )
        )
    )
    if duplicate_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A booking request from this email or phone is already pending. Please wait for confirmation or contact the office."
        )
    
    # Validate booking window
    min_date = date.today() + timedelta(hours=page.min_notice_hours // 24)
    max_date = date.today() + timedelta(days=page.booking_window_days)
    
    if booking_data.requested_date < min_date or booking_data.requested_date > max_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested date must be between {min_date} and {max_date}",
        )
    
    # Check if date is blocked
    if booking_data.requested_date.isoformat() in page.blocked_dates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested date is not available",
        )
    
    # Generate confirmation code
    confirmation_code = generate_confirmation_code()
    
    # Generate verification tokens if required
    email_verification_token = generate_verification_token() if page.require_email_verification else None
    phone_verification_code = generate_verification_code() if page.require_phone_verification else None
    
    # Create booking
    booking = OnlineBooking(
        booking_page_id=page.id,
        practice_id=page.practice_id,
        confirmation_code=confirmation_code,
        email_verification_token=email_verification_token,
        phone_verification_code=phone_verification_code,
        **booking_data.dict()
    )
    
    db.add(booking)
    
    # Update page statistics
    page.total_bookings += 1
    page.conversion_rate = int((page.total_bookings / page.total_views) * 100) if page.total_views > 0 else 0
    
    await db.commit()
    await db.refresh(booking)
    
    # Send confirmation email
    try:
        await email_service.send_appointment_confirmation(
            to=booking.email,
            patient_name=booking.patient_name,
            appointment_date=booking.requested_date.strftime('%B %d, %Y'),
            appointment_time=booking.requested_time.strftime('%I:%M %p') if booking.requested_time else 'TBD',
            procedure=booking.appointment_type or 'Dental Appointment'
        )
    except Exception as e:
        # Log but don't fail the booking
        import logging
        logging.warning(f"Failed to send confirmation email: {e}")
    
    return booking


@router.get("/bookings/", response_model=OnlineBookingListResponse)
async def list_online_bookings(
    request: Request,
    status: Optional[BookingStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    is_new_patient: Optional[bool] = Query(None, description="Filter by new patient"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List online bookings for the current practice
    """
    query = select(OnlineBooking).where(OnlineBooking.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(OnlineBooking.status == status)
    
    if start_date:
        query = query.where(OnlineBooking.requested_date >= start_date)
    
    if end_date:
        query = query.where(OnlineBooking.requested_date <= end_date)
    
    if is_new_patient is not None:
        query = query.where(OnlineBooking.is_new_patient == is_new_patient)
    
    query = query.order_by(OnlineBooking.submitted_at.desc())
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    # HIPAA: Log online booking list access
    await log_audit_event(
        db, current_user, "list_online_bookings", "online_booking", None, request
    )
    await db.commit()
    
    return OnlineBookingListResponse(
        bookings=bookings,
        count=len(bookings),
    )


@router.get("/bookings/{booking_id}", response_model=OnlineBookingResponse)
async def get_online_booking(
    request: Request,
    booking_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get online booking by ID
    """
    result = await db.execute(
        select(OnlineBooking).where(
            OnlineBooking.id == booking_id,
            OnlineBooking.practice_id == current_user.practice_id,
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # HIPAA: Log online booking access
    await log_audit_event(
        db, current_user, "view_online_booking", "online_booking", booking.id, request
    )
    await db.commit()
    
    return booking


@router.put("/bookings/{booking_id}", response_model=OnlineBookingResponse)
async def update_online_booking(
    booking_id: str,
    booking_data: OnlineBookingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update online booking
    """
    result = await db.execute(
        select(OnlineBooking).where(
            OnlineBooking.id == booking_id,
            OnlineBooking.practice_id == current_user.practice_id,
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    update_data = booking_data.dict(exclude_unset=True)
    
    # Handle status changes
    if 'status' in update_data:
        new_status = update_data['status']
        if new_status == BookingStatus.CONFIRMED and not booking.confirmed_at:
            booking.confirmed_at = datetime.now()
        elif new_status == BookingStatus.DECLINED and not booking.declined_at:
            booking.declined_at = datetime.now()
        elif new_status == BookingStatus.CANCELLED and not booking.cancelled_at:
            booking.cancelled_at = datetime.now()
            booking.cancelled_by = "staff"
    
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    await db.commit()
    await db.refresh(booking)
    
    return booking


@router.post("/bookings/{booking_id}/confirm", response_model=BookingConfirmationResponse)
async def confirm_booking(
    booking_id: str,
    confirmation_data: BookingConfirmationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Confirm a booking and optionally create an appointment
    """
    result = await db.execute(
        select(OnlineBooking).where(
            OnlineBooking.id == booking_id,
            OnlineBooking.practice_id == current_user.practice_id,
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Update booking status
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = datetime.now()
    
    appointment_id = None
    
    # Create appointment if requested
    if confirmation_data.create_appointment:
        # Create or link patient
        patient_id = booking.patient_id
        
        if not patient_id and booking.is_new_patient:
            # Create new patient
            patient = Patient(
                practice_id=booking.practice_id,
                first_name=booking.first_name,
                last_name=booking.last_name,
                email=booking.email,
                phone=booking.phone,
                date_of_birth=booking.date_of_birth,
                status="active",
            )
            db.add(patient)
            await db.flush()
            patient_id = patient.id
            booking.patient_id = patient_id
        
        # Create appointment
        appointment = Appointment(
            practice_id=booking.practice_id,
            patient_id=patient_id,
            provider_id=booking.provider_id,
            appointment_type_id=booking.appointment_type_id,
            start_time=datetime.combine(booking.requested_date, booking.requested_time),
            end_time=datetime.combine(booking.requested_date, booking.requested_time) + timedelta(minutes=booking.duration_minutes or 30),
            status="scheduled",
            notes=f"Online booking: {booking.reason or booking.chief_complaint}",
        )
        db.add(appointment)
        await db.flush()
        
        appointment_id = appointment.id
        booking.appointment_id = appointment_id
    
    await db.commit()
    
    # Send confirmation email if requested
    if booking.send_confirmation_email:
        try:
            await email_service.send_appointment_confirmation(
                to=booking.email,
                patient_name=booking.patient_name,
                appointment_date=booking.requested_date.strftime('%B %d, %Y'),
                appointment_time=booking.requested_time.strftime('%I:%M %p') if booking.requested_time else 'TBD',
                procedure=booking.appointment_type or 'Dental Appointment'
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to send confirmation email: {e}")
    
    return BookingConfirmationResponse(
        booking_id=booking.id,
        appointment_id=appointment_id,
        confirmation_code=booking.confirmation_code,
        status=booking.status,
        message="Booking confirmed successfully",
    )


# Availability Endpoints

@router.post("/public/{page_slug}/availability", response_model=AvailabilityResponse)
@limiter.limit("10/minute")
async def get_availability(
    request: Request,
    page_slug: str,
    availability_request: AvailabilityRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get available time slots (public endpoint)
    """
    # Get booking page
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.page_slug == page_slug,
            BookingPage.status == BookingPageStatus.ACTIVE,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found or inactive",
        )
    
    # Generate availability for requested date range
    days = []
    current_date = availability_request.start_date
    total_slots = 0
    
    while current_date <= availability_request.end_date:
        day_name = current_date.strftime("%A").lower()
        
        # Check if day is in business hours
        if day_name in page.business_hours and page.business_hours[day_name].get('enabled', False):
            # Check if date is not blocked
            if current_date.isoformat() not in page.blocked_dates:
                slots = []
                
                # Get business hours for this day
                day_hours = page.business_hours[day_name].get('slots', [])
                
                for slot_config in day_hours:
                    start_time_str = slot_config.get('start', '09:00')
                    end_time_str = slot_config.get('end', '17:00')
                    
                    # Parse times
                    start_hour, start_minute = map(int, start_time_str.split(':'))
                    end_hour, end_minute = map(int, end_time_str.split(':'))
                    
                    # Generate time slots
                    current_time = time(start_hour, start_minute)
                    end_time_obj = time(end_hour, end_minute)
                    
                    while current_time < end_time_obj:
                        # Check if slot is available (simplified - would check actual appointments in production)
                        slot = TimeSlot(
                            start_time=current_time,
                            end_time=(datetime.combine(date.today(), current_time) + timedelta(minutes=availability_request.duration_minutes)).time(),
                            duration_minutes=availability_request.duration_minutes,
                            is_available=True,
                            provider_id=availability_request.provider_id,
                            provider_name=None,  # Would fetch from database
                        )
                        slots.append(slot)
                        total_slots += 1
                        
                        # Move to next slot
                        current_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=availability_request.duration_minutes)).time()
                
                day_availability = DayAvailability(
                    date=current_date,
                    day_of_week=day_name.capitalize(),
                    is_available=len(slots) > 0,
                    slots=slots,
                )
                days.append(day_availability)
        
        current_date += timedelta(days=1)
    
    return AvailabilityResponse(
        days=days,
        total_slots=total_slots,
    )


# Waitlist Endpoints

@router.post("/public/{page_slug}/waitlist", response_model=WaitlistEntryResponse)
@limiter.limit("5/hour")
async def add_to_waitlist(
    request: Request,
    page_slug: str,
    waitlist_data: WaitlistEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add to waitlist (public endpoint)
    """
    # Get booking page
    result = await db.execute(
        select(BookingPage).where(
            BookingPage.page_slug == page_slug,
            BookingPage.status == BookingPageStatus.ACTIVE,
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking page not found or inactive",
        )
    
    # Create waitlist entry
    entry = WaitlistEntry(
        booking_page_id=page.id,
        practice_id=page.practice_id,
        expires_at=datetime.now() + timedelta(days=30),  # 30 days expiration
        **waitlist_data.dict()
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return entry


@router.get("/waitlist/", response_model=WaitlistEntryListResponse)
async def list_waitlist_entries(
    status: Optional[WaitlistStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List waitlist entries for the current practice
    """
    query = select(WaitlistEntry).where(WaitlistEntry.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(WaitlistEntry.status == status)
    
    query = query.order_by(WaitlistEntry.priority, WaitlistEntry.created_at)
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return WaitlistEntryListResponse(
        entries=entries,
        count=len(entries),
    )


@router.put("/waitlist/{entry_id}", response_model=WaitlistEntryResponse)
async def update_waitlist_entry(
    entry_id: str,
    entry_data: WaitlistEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update waitlist entry
    """
    result = await db.execute(
        select(WaitlistEntry).where(
            WaitlistEntry.id == entry_id,
            WaitlistEntry.practice_id == current_user.practice_id,
        )
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )
    
    update_data = entry_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    await db.commit()
    await db.refresh(entry)
    
    return entry


@router.post("/waitlist/{entry_id}/notify")
async def notify_waitlist_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Notify waitlist entry about availability
    """
    result = await db.execute(
        select(WaitlistEntry).where(
            WaitlistEntry.id == entry_id,
            WaitlistEntry.practice_id == current_user.practice_id,
        )
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )
    
    # Update notification tracking
    entry.notified_count += 1
    entry.last_notified_at = datetime.now()
    entry.status = WaitlistStatus.NOTIFIED
    
    await db.commit()
    
    # Send waitlist notification email
    try:
        await email_service.send_appointment_confirmation(
            to=entry.email,
            patient_name=entry.patient_name,
            appointment_date=entry.requested_date.strftime('%B %d, %Y') if entry.requested_date else 'TBD',
            appointment_time='TBD',
            procedure=entry.appointment_type or 'Dental Appointment'
        )
    except Exception as e:
        import logging
        logging.warning(f"Failed to send waitlist notification: {e}")
    
    return {"message": "Notification sent successfully"}


# Verification Endpoints

@router.post("/public/verify-email", response_model=VerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify email address (public endpoint)
    """
    result = await db.execute(
        select(OnlineBooking).where(OnlineBooking.id == verification_data.booking_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    if booking.email_verification_token != verification_data.verification_token:
        return VerificationResponse(
            verified=False,
            message="Invalid verification token",
        )
    
    booking.email_verified = True
    await db.commit()
    
    return VerificationResponse(
        verified=True,
        message="Email verified successfully",
    )


@router.post("/public/verify-phone", response_model=VerificationResponse)
async def verify_phone(
    verification_data: PhoneVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify phone number (public endpoint)
    """
    result = await db.execute(
        select(OnlineBooking).where(OnlineBooking.id == verification_data.booking_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    if booking.phone_verification_code != verification_data.verification_code:
        return VerificationResponse(
            verified=False,
            message="Invalid verification code",
        )
    
    booking.phone_verified = True
    await db.commit()
    
    return VerificationResponse(
        verified=True,
        message="Phone verified successfully",
    )


# Analytics Endpoint

@router.get("/analytics/", response_model=BookingAnalytics)
async def get_booking_analytics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get booking analytics for the current practice
    """
    query = select(OnlineBooking).where(OnlineBooking.practice_id == current_user.practice_id)
    
    if start_date:
        query = query.where(OnlineBooking.submitted_at >= datetime.combine(start_date, time.min))
    
    if end_date:
        query = query.where(OnlineBooking.submitted_at <= datetime.combine(end_date, time.max))
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    # Calculate analytics
    total_bookings = len(bookings)
    confirmed_bookings = sum(1 for b in bookings if b.status == BookingStatus.CONFIRMED)
    pending_bookings = sum(1 for b in bookings if b.status == BookingStatus.PENDING)
    declined_bookings = sum(1 for b in bookings if b.status == BookingStatus.DECLINED)
    cancelled_bookings = sum(1 for b in bookings if b.status == BookingStatus.CANCELLED)
    new_patients = sum(1 for b in bookings if b.is_new_patient)
    existing_patients = total_bookings - new_patients
    
    # Get total views from booking pages
    pages_result = await db.execute(
        select(BookingPage).where(BookingPage.practice_id == current_user.practice_id)
    )
    pages = pages_result.scalars().all()
    total_views = sum(p.total_views for p in pages)
    
    # Calculate conversion rate
    conversion_rate = (total_bookings / total_views * 100) if total_views > 0 else 0
    
    # Calculate average response time
    response_times = []
    for booking in bookings:
        if booking.confirmed_at:
            response_time = (booking.confirmed_at - booking.submitted_at).total_seconds() / 3600
            response_times.append(response_time)
    
    average_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Popular times (simplified)
    popular_times = {}
    for booking in bookings:
        hour = booking.requested_time.hour
        time_slot = f"{hour:02d}:00"
        popular_times[time_slot] = popular_times.get(time_slot, 0) + 1
    
    # Popular appointment types (simplified)
    popular_appointment_types = {}
    
    # Referral sources
    referral_sources = {}
    for booking in bookings:
        if booking.referral_source:
            referral_sources[booking.referral_source] = referral_sources.get(booking.referral_source, 0) + 1
    
    return BookingAnalytics(
        total_bookings=total_bookings,
        total_views=total_views,
        conversion_rate=conversion_rate,
        confirmed_bookings=confirmed_bookings,
        pending_bookings=pending_bookings,
        declined_bookings=declined_bookings,
        cancelled_bookings=cancelled_bookings,
        new_patients=new_patients,
        existing_patients=existing_patients,
        average_response_time_hours=average_response_time,
        popular_times=popular_times,
        popular_appointment_types=popular_appointment_types,
        referral_sources=referral_sources,
    )