from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: Optional[str] = None
    mobile: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6)
    state: str
    district: str
    village: Optional[str] = None
    primary_crop: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserLogin(BaseModel):
    username: str  # mobile or email
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    mobile: str
    state: str
    district: str
    village: Optional[str] = None
    primary_crop: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
