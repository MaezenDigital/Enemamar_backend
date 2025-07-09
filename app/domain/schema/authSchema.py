from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from app.domain.model.user import User
from datetime import datetime


class signUp(BaseModel):
    """User registration schema"""
    password: str = Field(
        ...,
        description="User's password (min 8 characters)",
        min_length=8,
        examples=["securepassword123"]
    )
    first_name: str = Field(
        ...,
        description="User's first name",
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        description="User's last name",
        examples=["Doe"]
    )
    phone_number: str = Field(
        ...,
        description="User's phone number (format: 09XXXXXXXX or +251XXXXXXXXX)",
        examples=["0912345678", "+251912345678"]
    )
    role: Optional[str] = Field(
        None,
        description="User role (student, instructor, admin)",
        examples=["student"]
    )
    otp: str = Field(
        ...,
        description="One-time password for verification",
        examples=["123456"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "0912345678",
                "otp": "123456"
            }
        }
    }

class login(BaseModel):
    """User login schema"""
    password: str = Field(
        ...,
        description="User's password",
        examples=["securepassword123"]
    )
    phone_number: str = Field(
        ...,
        description="User's phone number",
        examples=["0912345678", "+251912345678"]
    )

    def validate(self):
        """Validate login credentials"""
        if not self.password:
            raise ValueError("Password must be provided.")
        if not self.phone_number:
            raise ValueError("Phone number must be provided.")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "phone_number": "0912345678",
                "password": "securepassword123"
            }
        }
    }

class UserResponse(BaseModel):
    """User profile response schema"""
    id: UUID = Field(
        ...,
        description="Unique user identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    first_name: str = Field(
        ...,
        description="User's first name",
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        description="User's last name",
        examples=["Doe"]
    )
    phone_number: str = Field(
        ...,
        description="User's phone number",
        examples=["0912345678"]
    )
    role: str = Field(
        ...,
        description="User's role (student, instructor, admin)",
        examples=["student"]
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
        examples=[True]
    )
    profile_picture: Optional[str] = Field(
        None,
        description="URL to user's profile picture",
        examples=["https://example.com/profile.jpg"]
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Account creation timestamp",
        examples=["2023-01-01T12:00:00Z"]
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last account update timestamp",
        examples=["2023-01-02T12:00:00Z"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "0912345678",
                "role": "student",
                "is_active": True,
                "profile_picture": "https://example.com/profile.jpg",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-02T12:00:00Z"
            }
        }
    }

class editUser(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = Field(
        None,
        description="New first name",
        examples=["Johnny"]
    )
    last_name: Optional[str] = Field(
        None,
        description="New last name",
        examples=["Doe"]
    )
    phone_number: Optional[str] = Field(
        None,
        description="New phone number",
        examples=["0987654321"]
    )

    password: Optional[str] = Field(
        None,
        description="New password (min 8 characters)",
        examples=["newsecurepassword123"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "first_name": "Johnny",
                "last_name": "Doe",
                "phone_number": "0987654321",
                "password": "newsecurepassword123"
            }
        }
    }

class signUpResponse(BaseModel):
    """User registration response schema"""
    detail: str = Field(
        ...,
        description="Response message",
        examples=["User created successfully"]
    )
    user: UserResponse = Field(
        ...,
        description="Created user details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "User created successfully",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone_number": "0912345678",
                    "role": "student",
                    "is_active": True
                }
            }
        }
    }

class loginResponse(BaseModel):
    """User login response schema"""
    detail: str = Field(
        ...,
        description="Response message",
        examples=["Login successful"]
    )
    access_token: str = Field(
        ...,
        description="JWT access token for API authorization",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    user: UserResponse = Field(
        ...,
        description="Logged in user details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone_number": "0912345678",
                    "role": "student",
                    "is_active": True
                }
            }
        }
    }

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(
        ...,
        description="JWT access token for API authorization",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }

class tokenLoginData(BaseModel):
    """Token payload schema"""
    id: UUID = Field(
        ...,
        description="User ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    role: str = Field(
        ...,
        description="User role",
        examples=["student", "instructor", "admin"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "student"
            }
        }
    }

class UpdateRoleRequest(BaseModel):
    """Role update request schema"""
    role: str = Field(
        ...,
        description="New role to assign",
        examples=["instructor", "admin", "student"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "role": "instructor"
            }
        }
    }

class RefreshTokenRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class ForgetPasswordRequest(BaseModel):
    """Forget password request schema"""
    phone_number: str = Field(
        ...,
        description="User's phone number for password reset (format: 09XXXXXXXX or +251XXXXXXXXX)",
        examples=["0912345678", "+251912345678"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "phone_number": "0912345678"
            }
        }
    }


class VerifyOTPForPasswordReset(BaseModel):
    """Verify OTP for password reset schema"""
    phone_number: str = Field(
        ...,
        description="User's phone number (format: 09XXXXXXXX or +251XXXXXXXXX)",
        examples=["0912345678", "+251912345678"]
    )
    code: str = Field(
        ...,
        description="6-digit OTP code received via SMS",
        min_length=6,
        max_length=6,
        examples=["123456"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "phone_number": "0912345678",
                "code": "123456"
            }
        }
    }


class ResetPassword(BaseModel):
    """Reset password schema"""
    reset_token: str = Field(
        ...,
        description="Password reset token received after OTP verification",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    new_password: str = Field(
        ...,
        description="New password (min 8 characters)",
        min_length=8,
        examples=["newsecurepassword123"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "newsecurepassword123"
            }
        }
    }