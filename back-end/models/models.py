from pydantic import BaseModel

class RegisterRequest(BaseModel):
    """Schema for user registration requests."""
    first_name: str
    last_name: str
    email: str
    password: str
    phone_number: str
    address: str

class LoginRequest(BaseModel):
    """Schema for user login requests."""
    email: str
    password: str

class ChatRequest(BaseModel):
    """Schema for incoming chat queries."""
    query: str