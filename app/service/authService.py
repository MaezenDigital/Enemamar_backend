from app.utils.exceptions.exceptions import ValidationError, DuplicatedError, NotFoundError, AuthError
import re
import json
from app.domain.schema.authSchema import signUp, UserResponse, login,loginResponse, signUpResponse, tokenLoginData, ForgetPasswordRequest, VerifyOTPForPasswordReset, ResetPassword
from app.domain.model.user import User
from app.repository.userRepo import UserRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.config.database import get_db
from app.utils.security.hash import hash_password, verify_password
from app.utils.security.jwt_handler import verify_refresh_token, verify_access_token, create_access_token, create_refresh_token, create_password_reset_token, verify_password_reset_token
from app.utils.otp.sms import send_otp_sms, verify_otp_sms
from app.utils.helper import normalize_phone_number, format_phone_for_sending
from fastapi import Response, status
import time


class AuthService:
    def __init__(self, db):
        self.user_repo = UserRepository(db)

    def signUp(self, sign_up_data: signUp):
        # Validate and normalize phone number
        regex = r'^(?:\+251|0)?[79]\d{8}$'
        if not re.match(regex, sign_up_data.phone_number):
            raise ValidationError(detail="Invalid phone number")

        # Normalize phone number to raw form (e.g., 966934381)
        sign_up_data.phone_number = normalize_phone_number(sign_up_data.phone_number)

        self.verify_otp(sign_up_data.phone_number, sign_up_data.otp)
        # Convert sign_up_data to User ORM object
        user_obj = User(**sign_up_data.model_dump(exclude_none=True, exclude={'otp'}))

        user_obj.role = "user"  # Default role for new users

        # Hash the password
        user_obj.password = hash_password(user_obj.password)
        user_obj.is_active = True  # Set user as active by default
        # Check for duplicate entry using database constraints
        # Create user in repository and handle errors
        user, err = self.user_repo.create_user(user_obj)
        if err:
            if isinstance(err, ValueError):
                raise ValidationError(detail="Invalid phone number")
            if isinstance(err, IntegrityError):
                raise DuplicatedError(detail="User with this phone number already exists")
            raise ValidationError(detail="Failed to create user", data=str(err))
        if not user:
            raise ValidationError(detail="Failed to create user")
        
        user_response = UserResponse.model_validate(user, from_attributes=True)

        # Return response
        response = signUpResponse(detail="User created successfully", user=user_response)
        return response

    def login(self, login_data: login):
        print(login_data)
        # Fetch user by phone number and handle repo errors
        login_data.phone_number = normalize_phone_number(login_data.phone_number)
        user, err = self.user_repo.get_user_by_phone(login_data.phone_number)
        if err:
            raise ValidationError(detail="Error fetching user by phone number", data=str(err))

        # Check if user exists and is active
        if not user:
            raise NotFoundError(detail="User with this phone number does not exist")
        
        user_response = UserResponse.model_validate(user)
        if not user.is_active:
            return Response(
            content=json.dumps({"detail": "User is not active", "is_active": False}),
            status_code=status.HTTP_403_FORBIDDEN,
            media_type="application/json"
            )

        if not verify_password(login_data.password, user.password):
            raise ValidationError(detail="Incorrect password")
        
        # Create access token and refresh token
        token_data = tokenLoginData(id=user.id, role=user.role)
        tokens, err = self.user_repo.login(token_data)
        if err:
            raise ValidationError(detail="Login failed", data=str(err))
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        # Convert SQLAlchemy User object to Pydantic Response Model
        user_response = UserResponse.model_validate(user)
        login_response = loginResponse(detail="Login successful", access_token=access_token, refresh_token= refresh_token, user=user_response)
        return login_response
    
    def logout(self,refresh_token):
        decoded_token = verify_refresh_token(refresh_token)
        user_id = decoded_token.get("id")
        result, err = self.user_repo.delete_refresh(user_id, refresh_token)
        if err:
            raise ValidationError(detail="Error deleting refresh token", data=str(err))
        if not result:
            raise NotFoundError(detail="Refresh token not found for logout")
        return {"detail": "Successfully logged out"}



    def refresh_token(self, refresh_token: str):
        #get user id
        decoded_token = verify_refresh_token(refresh_token)
        user_id = decoded_token.get("id")
        #get refresh token
        token_obj, err = self.user_repo.get_user_by_refresh(user_id, refresh_token)
        if err:
            raise ValidationError(detail="Error validating refresh token", data=str(err))
        if not token_obj:
            raise AuthError(detail="Invalid refresh token or session expired")
        token_data = tokenLoginData(id=user_id, role=decoded_token.get("role"))
        access_token = create_access_token(token_data.model_dump())
        return {"access_token": access_token}

    def send_otp(self, phone_number: str):
        print("Sending OTP to phone number:", phone_number)
        formatted_phone_number = format_phone_for_sending(phone_number)
        attempts = 0
        max_attempts = 5
        delay = 1.5  # seconds

        while attempts < max_attempts:
            try:
                status_code, content = send_otp_sms(formatted_phone_number)
            except Exception as e:
                raise ValidationError(detail="Failed to send OTP", data=str(e))
            
            if status_code == 200:
                print("OTP sent successfully to:", formatted_phone_number)
                return {"detail": "OTP sent successfully", "status_code": status_code}
            else:
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(delay)
                else:
                    # decode bytes→JSON or utf-8, else leave as is
                    content_decoded = content
                    if isinstance(content, (bytes, bytearray)):
                        try:
                            content_decoded = json.loads(content)
                        except Exception:
                            content_decoded = content.decode("utf-8", errors="ignore")
                    raise ValidationError(detail="Failed to send OTP after multiple attempts", data=content_decoded)


    def verify_otp(self, phone_number: str, code: str):
        print("Verifying OTP for phone number:", phone_number)
        print("OTP code:", code)
        formatted_phone_number = format_phone_for_sending(phone_number)
        try:
            status_code, content = verify_otp_sms(formatted_phone_number, code)
        except Exception as e:
            raise ValidationError(detail="Error verifying OTP via SMS provider", data=str(e))
        
        if status_code == 200:
            pass
            # # Normalize phone number to raw form (e.g., 966934381)
            # phone_number = normalize_phone_number(formatted_phone_number)
            # # phone_number = re.sub(r'^(?:\+251|0)', '', phone_number)
                        
            # # Activate the user
            # print("Normalized phone number:", phone_number)
            # user, err = self.user_repo.activate_user(None, phone_number)
            # if err:
            #     raise ValidationError(detail="Error activating user after OTP", data=str(err))
            # if not user:
            #     raise NotFoundError(detail="User with this phone number does not exist")
            
            # return {"detail": "OTP verified successfully", "status_code": status_code}
        
        else:
            # decode bytes→JSON or utf-8, else leave as is
            content_decoded = content
            if isinstance(content, (bytes, bytearray)):
                try:
                    content_decoded = json.loads(content)
                except Exception:
                    content_decoded = content.decode("utf-8", errors="ignore")
            raise ValidationError(detail="Failed to verify OTP", data=content_decoded)


    def forget_password(self, forget_password_data: ForgetPasswordRequest):
        """Initiate password reset by sending OTP to user's phone"""
        # Normalize phone number
        phone_number = normalize_phone_number(forget_password_data.phone_number)

        # Get user by phone number
        user, err = self.user_repo.get_user_by_phone(phone_number)
        if err:
            raise ValidationError(detail="Error fetching user by phone number", data=str(err))
        if not user:
            raise NotFoundError(detail="User with this phone number does not exist")

        # Send OTP to user's phone number
        formatted_phone_number = format_phone_for_sending(phone_number)
        try:
            status_code, content = send_otp_sms(formatted_phone_number)
        except Exception as e:
            raise ValidationError(detail="Failed to send OTP for password reset", data=str(e))

        if status_code == 200:
            return {"detail": "OTP sent to your phone number for password reset"}
        else:
            # decode bytes→JSON or utf-8, else leave as is
            content_decoded = content
            if isinstance(content, (bytes, bytearray)):
                try:
                    content_decoded = json.loads(content)
                except Exception:
                    content_decoded = content.decode("utf-8", errors="ignore")
            raise ValidationError(detail="Failed to send OTP for password reset", data=content_decoded)


    def verify_otp_for_password_reset(self, verify_data: VerifyOTPForPasswordReset):
        """Verify OTP for password reset and return one-time use token"""
        # Normalize phone number for verification
        formatted_phone_number = format_phone_for_sending(verify_data.phone_number)

        try:
            status_code, content = verify_otp_sms(formatted_phone_number, verify_data.code)
        except Exception as e:
            raise ValidationError(detail="Failed to verify OTP for password reset", data=str(e))

        if status_code == 200:
            # Normalize phone number to raw form for database lookup
            phone_number = normalize_phone_number(formatted_phone_number)

            # Check if user exists with this phone number
            user, err = self.user_repo.get_user_by_phone(phone_number)
            if err:
                raise ValidationError(detail="Error fetching user by phone number", data=str(err))
            if not user:
                raise NotFoundError(detail="User with this phone number does not exist")

            # Generate one-time use password reset token
            reset_token = create_password_reset_token(phone_number)

            return {
                "detail": "OTP verified successfully for password reset",
                "status_code": status_code,
                "reset_token": reset_token
            }
        else:
            # decode bytes→JSON or utf-8, else leave as is
            content_decoded = content
            if isinstance(content, (bytes, bytearray)):
                try:
                    content_decoded = json.loads(content)
                except Exception:
                    content_decoded = content.decode("utf-8", errors="ignore")
            raise ValidationError(detail="Failed to verify OTP for password reset", data=content_decoded)

    def reset_password(self, reset_data: ResetPassword):
        """Reset user password using reset token"""
        # Verify the password reset token
        try:
            token_payload = verify_password_reset_token(reset_data.reset_token)
        except Exception as e:
            raise AuthError(detail="Invalid or expired password reset token", data=str(e))

        phone_number = token_payload.get("phone_number")

        if not phone_number:
            raise AuthError(detail="Invalid password reset token payload")

        # Update password in repository
        user, err = self.user_repo.update_password(phone_number, reset_data.new_password)
        if err:
            raise ValidationError(detail="Error updating password", data=str(err))
        if not user:
            raise NotFoundError(detail="User with this phone number does not exist")

        return {"detail": "Password reset successfully"}


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)