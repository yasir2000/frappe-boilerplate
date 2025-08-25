from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from billing_app.auth.auth_handler import AuthHandler
from billing_app.api.routes import router
from billing_app.websockets.ws_manager import WebSocketManager
from billing_app.models.database import engine, Base

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=os.getenv("APP_NAME", "Billing Application"),
    version=os.getenv("VERSION", "1.0.0"),
    description="A comprehensive billing application with authentication, validation, and workflow management"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(upload_dir, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# Include routers
app.include_router(router, prefix="/api/v1")

# WebSocket manager
ws_manager = WebSocketManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket, client_id: str):
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_personal_message(f"Echo: {data}", client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(client_id)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Billing Application API",
        "version": os.getenv("VERSION", "1.0.0"),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "billing-app"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
