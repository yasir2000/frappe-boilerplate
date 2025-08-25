# Billing Application

A comprehensive billing application built with FastAPI that includes authentication, validation, verification, WebSocket support, workflow engine, and file storage capabilities.

## Features

- **User Authentication**: JWT-based authentication with registration, login, and email verification
- **Data Validation**: Comprehensive input validation using Pydantic models
- **User Verification**: Email-based user verification system
- **WebSocket Support**: Real-time updates for invoice status changes and notifications
- **Workflow Engine**: State-based workflow management for invoice processing
- **File Storage**: Secure file upload and management system
- **Invoice Management**: Complete CRUD operations for invoices and invoice items

## Project Structure

```
billing_app/
├── auth/
│   └── auth_handler.py      # Authentication and authorization logic
├── api/
│   └── routes.py           # API endpoints
├── models/
│   ├── database.py         # Database models and configuration
│   └── schemas.py          # Pydantic schemas for validation
├── websockets/
│   └── ws_manager.py       # WebSocket connection management
├── workflow/
│   └── engine.py           # Workflow state management
└── storage/
    └── file_manager.py     # File upload and storage management
```

## Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   Copy `.env.example` to `.env` and update the configuration values:
   ```
   DATABASE_URL=sqlite:///./billing.db
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/verify/{token}` - Verify user email
- `GET /api/v1/auth/me` - Get current user info

### Invoices
- `POST /api/v1/invoices` - Create new invoice
- `GET /api/v1/invoices` - List invoices
- `GET /api/v1/invoices/{invoice_id}` - Get specific invoice
- `PUT /api/v1/invoices/{invoice_id}` - Update invoice

### File Management
- `POST /api/v1/files/upload` - Upload file
- `GET /api/v1/files` - List user files

### WebSocket
- `WS /ws/{client_id}` - WebSocket connection for real-time updates

## Workflow States

The invoice workflow supports the following states and transitions:

- **draft** → sent, cancelled
- **sent** → paid, overdue, cancelled
- **paid** (terminal state)
- **overdue** → paid, cancelled
- **cancelled** (terminal state)

## Usage Examples

### 1. User Registration
```python
import requests

response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
})
```

### 2. Login
```python
response = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "john_doe",
    "password": "SecurePass123"
})
token = response.json()["access_token"]
```

### 3. Create Invoice
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/api/v1/invoices", 
    headers=headers,
    json={
        "invoice_number": "INV-001",
        "customer_id": 1,
        "total_amount": 100.00,
        "items": [
            {
                "description": "Web Development",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }
)
```

### 4. WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client123');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## Security Features

- Password hashing using bcrypt
- JWT token-based authentication
- Input validation and sanitization
- File type and size validation
- CORS protection
- SQL injection prevention through ORM

## Development

To extend the application:

1. **Add new models** in `billing_app/models/database.py`
2. **Create new schemas** in `billing_app/models/schemas.py`
3. **Add API endpoints** in `billing_app/api/routes.py`
4. **Extend workflow** in `billing_app/workflow/engine.py`

## Testing

Run the application and test the endpoints using the interactive API documentation at http://localhost:8000/docs

## License

This project is open source and available under the MIT License.