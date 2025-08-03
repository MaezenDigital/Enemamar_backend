from app.utils.exceptions.exceptions import ValidationError, DuplicatedError, NotFoundError
import re
from app.domain.schema.authSchema import UserResponse, editUser
from app.domain.model.user import User
from app.repository.userRepo import UserRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile
from app.core.config.database import get_db
from typing import Optional
from app.utils.helper import normalize_phone_number
from app.utils.security.hash import hash_password, verify_password


#initalize the user service
class UserService:
    def __init__(self, db):
        # print("UserService")
        self.user_repo = UserRepository(db)

    #get all users
    def get_all_users(self, search: Optional[str] = None, page: int = 1, page_size: int = 10, filter: Optional[str] = None, is_active: Optional[bool] = None):
        # Ensure pagination defaults when parameters are None
        page = page or 1
        page_size = page_size or 10

        users, err = self.user_repo.get_all_users(search=search, page=page, page_size=page_size, filter=filter, is_active=is_active)
        if err:
            raise ValidationError(detail="Failed to retrieve users", data=str(err))

        # Get total count for pagination metadata
        total_count, err = self.user_repo.get_users_count(search=search, filter=filter, is_active=is_active)
        if err:
            raise ValidationError(detail="Failed to retrieve users count", data=str(err))

        users_response = [UserResponse.model_validate(user) for user in users]
        response = {
            "detail": "Users retrieved successfully",
            "data": users_response,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        return response

    #get user by id
    def get_user_by_id(self, user_id: int):
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)

        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User retrieved successfully", "data": user_response}
        return response

    #deactivate user
    def deactivate_user(self, user_id: int):
        user, err = self.user_repo.deactivate_user(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to deactivate user", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)

        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User deactivated successfully", "data": user_response}
        return response

    #activate user
    def activate_user(self, user_id: int):
        user, err = self.user_repo.activate_user(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to activate user", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)

        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User activated successfully", "data": user_response}
        return response

    #delete user
    def delete_user(self, user_id: int):
        # First check if user exists
        self.get_user_by_id(user_id)

        _, err = self.user_repo.delete_user(user_id)
        if err:
            raise ValidationError(detail="Failed to delete user", data=str(err))

        response = {"detail": "User deleted successfully"}
        return response

    #update role
    def update_role(self, user_id: str, role: str):
        user, err = self.user_repo.update_role(user_id, role)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to update user role", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)

        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User role updated successfully", "data": user_response}
        return response

    #get user by token
    def get_user_by_token(self, user_id):
        #split the token
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)
        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User retrieved successfully", "data": user_response}
        return response

    #edit user by token
    def edit_user_by_token(self, user_id, edit_data: editUser):
        #split the token
        if edit_data.phone_number:
            edit_data.phone_number = normalize_phone_number(edit_data.phone_number)
        
        if edit_data.password:
            edit_data.password = hash_password(edit_data.password)

        user, err = self.user_repo.update_user(user_id, edit_data)
        if err:
            if isinstance(err, IntegrityError) and "duplicate key" in str(err).lower():
                raise DuplicatedError(detail="User with this information already exists")
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="User with this id does not exist")
            raise ValidationError(detail="Failed to update user", data=str(err))
        #check if user exists
        if not user:
            raise NotFoundError(detail="User with this id does not exist")
        #convert the user to response model
        user_response = UserResponse.model_validate(user)

        # user_response = UserResponse(
        #     id=user.id,
        #     full_name=user.full_name,
        #     phone_number=user.phone_number,
        #     role=user.role,
        #     is_active=user.is_active
        # )
        #return the response
        response = {"detail": "User updated successfully", "data": user_response}
        return response

    #get all instructors
    def get_all_instructors(self, search: Optional[str] = None, page: int = 1, page_size: int = 10):
        # Ensure pagination defaults when parameters are None
        page = page or 1
        page_size = page_size or 10

        users, err = self.user_repo.get_all_instructors(search=search, page=page, page_size=page_size)
        if err:
            raise ValidationError(detail="Failed to retrieve instructors", data=str(err))

        # Get total count for pagination metadata
        total_count, err = self.user_repo.get_instructors_count(search=search)
        if err:
            raise ValidationError(detail="Failed to retrieve instructors count", data=str(err))

        users_response = [UserResponse.model_validate(user) for user in users]
        response = {
            "detail": "Instructors retrieved successfully",
            "data": users_response,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        return response

    #get instructor by id
    def get_instructor_by_id(self, instructor_id: str):
        user, err = self.user_repo.get_instructor_by_id(instructor_id)
        if err:
            if isinstance(err, NotFoundError):
                raise NotFoundError(detail="Instructor with this id does not exist")
            raise ValidationError(detail="Failed to retrieve instructor", data=str(err))
        if not user:
            raise NotFoundError(detail="Instructor with this id does not exist")
        user_response = UserResponse.model_validate(user)
        response = {"detail": "Instructor retrieved successfully", "data": user_response}
        return response

    def upload_profile_picture(self, user_id: str, profile_picture: UploadFile):
        """
        Upload a profile picture for a user.

        Args:
            user_id (str): The ID of the user.
            profile_picture (UploadFile): The profile picture file.

        Returns:
            dict: Response containing profile picture upload details.

        Raises:
            ValidationError: If the user ID is invalid or the profile picture upload fails.
        """
        import os
        from tempfile import NamedTemporaryFile
        from app.utils.bunny.bunnyStorage import BunnyCDNStorage
        from app.core.config.env import get_settings

        settings = get_settings()

        # Validate user exists
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        # Validate image format
        if not re.match(r"^image/(jpeg|png|jpg)$", profile_picture.content_type):
            raise ValidationError(detail="Invalid image format. Only JPEG and PNG are allowed.")

        try:
            # Initialize BunnyCDN storage
            storage = BunnyCDNStorage(
                settings.BUNNY_CDN_PROFILE_STORAGE_APIKEY,
                settings.BUNNY_CDN_PROFILE_STORAGE_ZONE,
                settings.BUNNY_CDN_PROFILE_PULL_ZONE
            )

            # Generate filename based on user's name
            name_base = user.first_name
            if user.last_name:
                name_base += f"_{user.last_name}"

            # Get original filename and extension
            original_filename = profile_picture.filename
            original_extension = ""
            if original_filename and "." in original_filename:
                original_extension = "." + original_filename.split(".")[-1]

            # Create a temporary file with the original content
            with NamedTemporaryFile("wb", delete=False) as tmp:
                tmp.write(profile_picture.file.read())
                tmp_path = tmp.name

            # Create a temporary file with the correct extension to help BunnyCDN detect the file type
            temp_file_with_ext = f"{tmp_path}{original_extension}"
            import shutil
            shutil.copy(tmp_path, temp_file_with_ext)

            # Upload and then remove temp files
            # The BunnyCDNStorage class will handle making the filename unique
            profile_picture_url = storage.upload_file(
                "",
                file_path=temp_file_with_ext,
                file_name=name_base
            )

            # Clean up temporary files
            os.unlink(temp_file_with_ext)
            os.unlink(tmp_path)

            # Update user's profile picture URL
            _, err = self.user_repo.update_profile_picture(user_id, profile_picture_url)
            if err:
                raise ValidationError(detail="Failed to update profile picture", data=str(err))

            return {
                "detail": "Profile picture uploaded successfully",
                "data": {
                    "profile_picture_url": profile_picture_url
                }
            }
        except Exception as e:
            raise ValidationError(detail="Failed to upload profile picture", data=str(e))

def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)