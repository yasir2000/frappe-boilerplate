from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class InvoiceItemBase(BaseModel):
    description: str
    quantity: float
    unit_price: float
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v < 0:
            raise ValueError('Unit price cannot be negative')
        return v

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItem(InvoiceItemBase):
    id: int
    total_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_number: str
    total_amount: float
    tax_amount: Optional[float] = 0.0
    due_date: Optional[datetime] = None
    description: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    customer_id: int
    items: List[InvoiceItemCreate]
    
    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v < 0:
            raise ValueError('Total amount cannot be negative')
        return v

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['draft', 'sent', 'paid', 'overdue', 'cancelled']:
            raise ValueError('Invalid status')
        return v

class Invoice(InvoiceBase):
    id: int
    customer_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[InvoiceItem] = []
    
    class Config:
        from_attributes = True

class WorkflowLogBase(BaseModel):
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    notes: Optional[str] = None

class WorkflowLogCreate(WorkflowLogBase):
    invoice_id: int
    user_id: Optional[int] = None

class WorkflowLog(WorkflowLogBase):
    id: int
    invoice_id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True
