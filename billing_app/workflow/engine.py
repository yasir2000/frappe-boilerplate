from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from billing_app.models.database import WorkflowLog, Invoice

class WorkflowEngine:
    """
    Simple workflow engine for managing invoice states and transitions
    """
    
    VALID_TRANSITIONS = {
        "draft": ["sent", "cancelled"],
        "sent": ["paid", "overdue", "cancelled"],
        "paid": [],  # Terminal state
        "overdue": ["paid", "cancelled"],
        "cancelled": []  # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def get_valid_transitions(cls, from_status: str) -> list:
        """Get all valid transitions from a given status"""
        return cls.VALID_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def transition_invoice(cls, db: Session, invoice_id: int, to_status: str, user_id: int, notes: str = None) -> bool:
        """
        Attempt to transition an invoice to a new status
        Returns True if successful, False if transition is not allowed
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return False
        
        if not cls.can_transition(invoice.status, to_status):
            return False
        
        old_status = invoice.status
        invoice.status = to_status
        
        # Log the transition
        cls.log_action(db, invoice_id, "status_transition", old_status, to_status, user_id, notes)
        
        db.commit()
        return True
    
    @classmethod
    def log_action(cls, db: Session, invoice_id: int, action: str, from_status: Optional[str], 
                   to_status: Optional[str], user_id: Optional[int], notes: Optional[str] = None):
        """Log a workflow action"""
        log = WorkflowLog(
            invoice_id=invoice_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            user_id=user_id,
            notes=notes
        )
        db.add(log)
        db.commit()
    
    @classmethod
    def get_workflow_history(cls, db: Session, invoice_id: int):
        """Get the workflow history for an invoice"""
        return db.query(WorkflowLog).filter(WorkflowLog.invoice_id == invoice_id).order_by(WorkflowLog.created_at).all()
    
    @classmethod
    def auto_mark_overdue(cls, db: Session):
        """
        Automatically mark invoices as overdue if they pass their due date
        This should be run as a scheduled task
        """
        from datetime import datetime
        
        overdue_invoices = db.query(Invoice).filter(
            Invoice.due_date < datetime.utcnow(),
            Invoice.status == "sent"
        ).all()
        
        for invoice in overdue_invoices:
            if cls.can_transition(invoice.status, "overdue"):
                invoice.status = "overdue"
                cls.log_action(db, invoice.id, "auto_overdue", "sent", "overdue", None, "Automatically marked as overdue")
        
        db.commit()
        return len(overdue_invoices)
    
    @classmethod
    def send_invoice(cls, db: Session, invoice_id: int, user_id: int, email_sent: bool = False):
        """Send an invoice (transition from draft to sent)"""
        if cls.transition_invoice(db, invoice_id, "sent", user_id, "Invoice sent to customer"):
            # Here you could add email sending logic
            if email_sent:
                cls.log_action(db, invoice_id, "email_sent", None, None, user_id, "Invoice email sent")
            return True
        return False
    
    @classmethod
    def mark_paid(cls, db: Session, invoice_id: int, user_id: int, payment_reference: str = None):
        """Mark an invoice as paid"""
        notes = f"Payment received. Reference: {payment_reference}" if payment_reference else "Payment received"
        return cls.transition_invoice(db, invoice_id, "paid", user_id, notes)
    
    @classmethod
    def cancel_invoice(cls, db: Session, invoice_id: int, user_id: int, reason: str = None):
        """Cancel an invoice"""
        notes = f"Invoice cancelled. Reason: {reason}" if reason else "Invoice cancelled"
        return cls.transition_invoice(db, invoice_id, "cancelled", user_id, notes)
