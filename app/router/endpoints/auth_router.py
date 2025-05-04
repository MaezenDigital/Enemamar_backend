from fastapi import APIRouter, HTTPException, Request, Depends, Header, status
from app.domain.schema.authSchema import signUp, login, RefreshTokenRequest, signUpResponse, loginResponse, TokenResponse, UserResponse
from app.service.authService import AuthService, get_auth_service
from app.utils.middleware.dependancies import is_admin, is_logged_in
from typing import Dict, Any

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@auth_router.post(
    "/otp/send",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send OTP",
    description="Send a one-time password (OTP) to the provided phone number for verification.",
    responses={
        200: {
            "description": "OTP sent successfully",
            "content": {
                "application/json": {
                    "example": {"detail": "OTP sent successfully"}
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid phone number format"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to send OTP"}
                }
            }
        }
    }
)
async def send_otp(phone_number: str, auth_service: AuthService = Depends(get_auth_service)):
    """
    Send a one-time password (OTP) to the provided phone number for verification.

    The OTP will be sent via SMS and can be used for user verification or account activation.

    - **phone_number**: The phone number to send the OTP to (format: +251XXXXXXXXX or 09XXXXXXXX)
    """
    return auth_service.send_otp(phone_number=phone_number)

@auth_router.post(
    "/otp/verify",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
    description="Verify the OTP code sent to the provided phone number.",
    responses={
        200: {
            "description": "OTP verified successfully",
            "content": {
                "application/json": {
                    "example": {"detail": "OTP verified successfully", "status_code": 200}
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid OTP code"}
                }
            }
        },
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this phone number does not exist"}
                }
            }
        }
    }
)
async def verify_otp(phone_number: str, code: str, auth_service: AuthService = Depends(get_auth_service)):
    """
    Verify the OTP code sent to the provided phone number.

    This endpoint validates the OTP code and activates the user account if verification is successful.

    - **phone_number**: The phone number to verify OTP for (format: +251XXXXXXXXX or 09XXXXXXXX)
    - **code**: The 6-digit OTP code received via SMS
    """
    return auth_service.verify_otp(phone_number=phone_number, code=code)

@auth_router.post(
    "/signup",
    response_model=signUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with the provided information.",
    responses={
        201: {
            "description": "User created successfully",
            "model": signUpResponse
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or phone number"}
                }
            }
        },
        409: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this email or phone number already exists"}
                }
            }
        }
    }
)
async def signup(sign_up_info: signUp, auth_service: AuthService = Depends(get_auth_service)):
    """
    Register a new user account.

    This endpoint creates a new user with the provided information. The user will need to verify
    their phone number using OTP before the account is fully activated.

    - **sign_up_info**: User registration information including name, phone number, and password
    """
    user_response = auth_service.signUp(sign_up_info)
    return user_response

@auth_router.post(
    "/login",
    response_model=loginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description="Log in a user with email/phone and password to get access tokens.",
    responses={
        200: {
            "description": "Login successful",
            "model": loginResponse
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Either email or phone_number must be provided"}
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect password"}
                }
            }
        },
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        }
    }
)
async def login_endpoint(
    login_info: login,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate a user and generate access tokens.

    This endpoint authenticates a user using either email or phone number with password,
    and returns JWT access and refresh tokens for API authorization.

    - **login_info**: Login credentials (email/phone and password)
    """
    try:
        login_info.validate()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return auth_service.login(login_info)

@auth_router.post(
    "/logout",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Log out a user",
    description="Invalidate the user's refresh token to log them out.",
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {"detail": "Successfully logged out"}
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to logout, refresh token not found"}
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token"}
                }
            }
        }
    }
)
async def logout(refresh_token: str = Header(None), auth_service: AuthService = Depends(get_auth_service)):
    """
    Log out a user by invalidating their refresh token.

    This endpoint invalidates the provided refresh token, effectively logging the user out
    and preventing the token from being used to generate new access tokens.

    - **refresh_token**: The refresh token to invalidate (provided in header)
    """
    return auth_service.logout(refresh_token=refresh_token)

@auth_router.post(
    "/refresh",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token.",
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token, user has been logged out"}
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token"}
                }
            }
        }
    }
)
async def refresh_token(
    refresh_token_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Generate a new access token using a valid refresh token.

    This endpoint validates the provided refresh token and generates a new access token
    without requiring the user to log in again with their credentials.

    - **refresh_token_request**: Object containing the refresh token
    """
    return auth_service.refresh_token(refresh_token=refresh_token_request.refresh_token)
