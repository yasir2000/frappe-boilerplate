import os
import uuid
import aiofiles
from typing import Optional
from fastapi import UploadFile, HTTPException

class FileStorageManager:
    """
    File storage manager for handling file uploads and downloads
    """
    
    def __init__(self, upload_dir: str = None, max_file_size: int = None):
        self.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "./uploads")
        self.max_file_size = max_file_size or int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate file before upload"""
        # Check file size
        if file.size > self.max_file_size:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {self.max_file_size} bytes")
        
        # Check file type (you can customize this based on your needs)
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf',
            'text/plain', 'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="File type not allowed")
        
        return True
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to prevent conflicts"""
        file_extension = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4()}{file_extension}"
    
    async def save_file(self, file: UploadFile) -> dict:
        """Save an uploaded file"""
        self.validate_file(file)
        
        unique_filename = self.generate_unique_filename(file.filename)
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return {
                'filename': unique_filename,
                'original_filename': file.filename,
                'file_path': file_path,
                'file_size': file.size,
                'content_type': file.content_type
            }
        except Exception as e:
            # Clean up if save failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file"""
        file_path = os.path.join(self.upload_dir, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_path(self, filename: str) -> Optional[str]:
        """Get the full path to a file"""
        file_path = os.path.join(self.upload_dir, filename)
        if os.path.exists(file_path):
            return file_path
        return None
    
    def get_file_url(self, filename: str, base_url: str = "http://localhost:8000") -> str:
        """Get the URL to access a file"""
        return f"{base_url}/uploads/{filename}"

# Global instance
file_storage = FileStorageManager()
