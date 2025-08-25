from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import aiofiles
from datetime import timedelta

from billing_app.models.database import get_db, User, Invoice, InvoiceItem, WorkflowLog, FileStorage
from billing_app.models.schemas import (
    UserCreate, User as UserSchema, Token, InvoiceCreate, Invoice as InvoiceSchema,
    InvoiceUpdate, WorkflowLogCreate, FileUploadResponse
)
from billing_app.auth.auth_handler import auth_handler, get_current_active_user, get_current_verified_user
from billing_app.workflow.engine import WorkflowEngine

router = APIRouter()

# Authentication endpoints
@router.post("/auth/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = auth_handler.get_password_hash(user.password)
    verification_token = str(uuid.uuid4())
    
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        verification_token=verification_token
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_handler.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = auth_handler.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/verify/{token}")
def verify_user(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "User verified successfully"}

@router.get("/auth/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Invoice endpoints
@router.post("/invoices", response_model=InvoiceSchema)
def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    # Calculate total from items
    total_from_items = sum(item.quantity * item.unit_price for item in invoice.items)
    
    # Create invoice
    db_invoice = Invoice(
        invoice_number=invoice.invoice_number,
        customer_id=invoice.customer_id,
        total_amount=total_from_items,
        tax_amount=invoice.tax_amount,
        due_date=invoice.due_date,
        description=invoice.description,
        status="draft"
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # Create invoice items
    for item in invoice.items:
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price
        )
        db.add(db_item)
    
    db.commit()
    
    # Log workflow action
    WorkflowEngine.log_action(
        db, db_invoice.id, "created", None, "draft", current_user.id, "Invoice created"
    )
    
    return db_invoice

@router.get("/invoices", response_model=List[InvoiceSchema])
def read_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceSchema)
def read_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    old_status = invoice.status
    
    for field, value in invoice_update.dict(exclude_unset=True).items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    # Log workflow action if status changed
    if invoice_update.status and old_status != invoice_update.status:
        WorkflowEngine.log_action(
            db, invoice.id, "status_changed", old_status, invoice_update.status, current_user.id
        )
    
    return invoice

# File upload endpoints
@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    # Validate file size
    max_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    if file.size > max_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    file_path = os.path.join(upload_dir, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Save to database
    db_file = FileStorage(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size,
        content_type=file.content_type,
        user_id=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.get("/files", response_model=List[FileUploadResponse])
def list_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    files = db.query(FileStorage).filter(FileStorage.user_id == current_user.id).offset(skip).limit(limit).all()
    return files
