"""
Inventory Endpoints
CRUD operations for inventory management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List, Optional, Any
import json

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
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
)
from app.api.deps import verify_csrf

router = APIRouter()


# Inventory Item Endpoints

@router.get("/items/")
async def list_inventory_items(
    category: Optional[InventoryCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    low_stock: Optional[bool] = Query(None, description="Filter low stock items"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List inventory items for the practice
    """
    query = select(InventoryItem).where(InventoryItem.practice_id == current_user.practice_id)
    
    if category:
        query = query.where(InventoryItem.category == category)
    
    if search:
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(
            (InventoryItem.name.ilike(search_pattern)) | 
            (InventoryItem.sku.ilike(search_pattern))
        )
    
    query = query.order_by(InventoryItem.name)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Filter low stock if requested
    if low_stock:
        items = [item for item in items if item.is_low_stock]
    
    return {"items": items, "count": len(items)}


@router.get("/items/{item_id}")
async def get_inventory_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get inventory item by ID
    """
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.practice_id == current_user.practice_id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    return item


@router.post("/items/")
async def create_inventory_item(
    item_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new inventory item
    """
    item = InventoryItem(
        practice_id=current_user.practice_id,
        **item_data
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    return item


@router.put("/items/{item_id}")
async def update_inventory_item(
    item_id: str,
    item_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update inventory item
    """
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.practice_id == current_user.practice_id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    for field, value in item_data.items():
        setattr(item, field, value)
    
    await db.commit()
    await db.refresh(item)
    
    return item


@router.delete("/items/{item_id}")
async def delete_inventory_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete inventory item
    """
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.practice_id == current_user.practice_id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    await db.delete(item)
    await db.commit()
    
    return {"message": "Inventory item deleted successfully"}


# Inventory Transaction Endpoints

@router.get("/transactions/")
async def list_inventory_transactions(
    item_id: Optional[str] = Query(None, description="Filter by item"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List inventory transactions
    """
    query = select(InventoryTransaction).where(
        InventoryTransaction.practice_id == current_user.practice_id
    )
    
    if item_id:
        query = query.where(InventoryTransaction.item_id == item_id)
    
    if transaction_type:
        query = query.where(InventoryTransaction.transaction_type == transaction_type)
    
    if start_date:
        query = query.where(InventoryTransaction.created_at >= start_date)
    
    if end_date:
        query = query.where(InventoryTransaction.created_at <= end_date)
    
    query = query.order_by(InventoryTransaction.created_at.desc())
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return {"transactions": transactions, "count": len(transactions)}


@router.post("/transactions/")
async def create_inventory_transaction(
    transaction_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create inventory transaction (add or remove stock)
    """
    # Get the item
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == transaction_data.get("item_id"),
            InventoryItem.practice_id == current_user.practice_id,
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    # Calculate new quantity
    quantity = transaction_data.get("quantity", 0)
    transaction_type = transaction_data.get("transaction_type")
    previous_quantity = item.current_quantity
    
    if transaction_type == "IN":
        new_quantity = previous_quantity + quantity
    elif transaction_type == "OUT":
        new_quantity = previous_quantity - quantity
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )
    else:
        new_quantity = quantity  # ADJUST
    
    # Update item quantity
    item.current_quantity = new_quantity
    
    # Create transaction record
    transaction = InventoryTransaction(
        practice_id=current_user.practice_id,
        user_id=current_user.id,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        **transaction_data
    )
    db.add(transaction)
    
    # Check for low stock alert
    if item.needs_reorder:
        # Create alert
        alert = InventoryAlert(
            item_id=item.id,
            practice_id=current_user.practice_id,
            alert_type=InventoryAlertType.REORDER_POINT,
            message=f"Item {item.name} is at or below reorder point"
        )
        db.add(alert)
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


# Supplier Endpoints

@router.get("/suppliers/")
async def list_suppliers(
    search: Optional[str] = Query(None, description="Search by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List suppliers
    """
    query = select(Supplier).where(Supplier.practice_id == current_user.practice_id)
    
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)
    
    if search:
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(Supplier.name.ilike(search_pattern))
    
    query = query.order_by(Supplier.name)
    
    result = await db.execute(query)
    suppliers = result.scalars().all()
    
    return {"suppliers": suppliers, "count": len(suppliers)}


@router.post("/suppliers/")
async def create_supplier(
    supplier_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new supplier
    """
    supplier = Supplier(
        practice_id=current_user.practice_id,
        **supplier_data
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    
    return supplier


# Alerts Endpoints

@router.get("/alerts/")
async def list_inventory_alerts(
    item_id: Optional[str] = Query(None, description="Filter by item"),
    alert_type: Optional[InventoryAlertType] = Query(None, description="Filter by alert type"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List inventory alerts
    """
    query = select(InventoryAlert).where(
        InventoryAlert.practice_id == current_user.practice_id
    )
    
    if item_id:
        query = query.where(InventoryAlert.item_id == item_id)
    
    if alert_type:
        query = query.where(InventoryAlert.alert_type == alert_type)
    
    if is_resolved is not None:
        query = query.where(InventoryAlert.is_resolved == is_resolved)
    
    query = query.order_by(InventoryAlert.created_at.desc())
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_inventory_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Resolve inventory alert
    """
    result = await db.execute(
        select(InventoryAlert).where(
            InventoryAlert.id == alert_id,
            InventoryAlert.practice_id == current_user.practice_id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    
    await db.commit()
    await db.refresh(alert)
    
    return alert
