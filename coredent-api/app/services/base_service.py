"""
Base Service Class
Provides common functionality for all services
"""

from typing import Optional, TypeVar, Generic, Type, List, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.base import Base

T = TypeVar('T', bound=Base)


class BaseService(Generic[T]):
    """Base service with common CRUD operations"""
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[T]:
        """Get all entities with pagination and filters"""
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[dict] = None) -> int:
        """Count entities with optional filters"""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def create(self, obj: T) -> T:
        """Create new entity"""
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj
    
    async def update(self, obj: T) -> T:
        """Update existing entity"""
        await self.db.flush()
        await self.db.refresh(obj)
        return obj
    
    async def delete(self, obj: T) -> None:
        """Delete entity"""
        await self.db.delete(obj)
        await self.db.flush()
