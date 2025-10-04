from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    completed: bool = Field(False, description="Completion status")

class TodoCreate(TodoBase):
    """Schema for creating a new todo"""
    pass

class TodoUpdate(BaseModel):
    """Schema for updating an existing todo"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(TodoBase):
    """Schema for todo responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
