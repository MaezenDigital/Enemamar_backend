from app.utils.exceptions.exceptions import AuthError, NotFoundError,DuplicatedError,ValidationError
from sqlalchemy.orm import Session
from app.domain.model.user import User, RefreshToken
from app.domain.schema.authSchema import tokenLoginData, editUser
from app.utils.security.jwt_handler import create_access_token, create_refresh_token
from sqlalchemy.exc import DataError
from typing import Tuple, Optional, Any
from sqlalchemy import or_
from app.utils.security.hash import hash_password, verify_password

def _wrap_return(result: Any) -> Tuple[Any, Optional[Exception]]:
    return result, None
def _wrap_error(e: Exception) -> Tuple[None, Exception]:
    return None, e

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: User):
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_user_by_refresh(self, user_id: str, refresh_token: str):
        try:
            result = self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
            if not result:
                return None, None
            if not verify_password(refresh_token, result.token):
                raise AuthError(detail="Invalid refresh token: token not verified")
            return _wrap_return(result)
        except Exception as e:
            return _wrap_error(e)

    def delete_refresh(self, user_id: str, refresh_token: str):
        try:
            token_obj, err = self.get_user_by_refresh(user_id=user_id, refresh_token=refresh_token)
            if err:
                return None, err
            if not token_obj:
                return None, None
            self.db.delete(token_obj)
            self.db.commit()
            return _wrap_return({'deleted': True})
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_all_users(self, search: Optional[str] = None, page: int = 1, page_size: int = 10, filter: Optional[str] = None, is_active: Optional[bool] = None):
        try:
            query = self.db.query(User)

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.phone_number.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.profession.ilike(search_term)
                    )
                )

            if filter:
                # Filter by role (student, instructor, admin)
                query = query.filter(User.role.ilike(f"%{filter}%"))

            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)

    def get_user_by_id(self, user_id: str):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            return _wrap_return(user)
        except DataError as e:
            return _wrap_error(e)



    def get_user_by_phone(self, phone_number: str):
        try:
            user = self.db.query(User).filter(User.phone_number == phone_number).first()
            return _wrap_return(user)
        except DataError as e:
            return _wrap_error(e)

    def deactivate_user(self, user_id: int):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, None
            user.is_active = False
            self.db.commit()
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def activate_user(self, user_id: Optional[str] = None, phone_number: Optional[str] = None):
        try:
            user = None
            if user_id:
                user, err = self.get_user_by_id(user_id)
                if err:
                    return None, err
            elif phone_number:
                user, err = self.get_user_by_phone(phone_number)
                if err:
                    return None, err
            if not user:
                return None, None
            user.is_active = True
            self.db.commit()
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def delete_user(self, user_id: int):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User with this id does not exist")
            self.db.delete(user)
            self.db.commit()
            return _wrap_return({'deleted': True})
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    #update the role of the user
    def update_role(self, user_id: int, role: str):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, None
            user.role = role
            self.db.commit()
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def update_user(self,id:int, edit_user: editUser):
        try:
            user = self.db.query(User).filter(User.id == id).first()
            if not user:
                return None, None
            for key, value in edit_user.model_dump().items():
                if value:
                    setattr(user, key, value)
            self.db.commit()
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)


    def login(self, login_data: tokenLoginData):
        try:
            access_token = create_access_token(login_data.model_dump())
            refresh_token = create_refresh_token(login_data.model_dump())
            existing, err = self.get_refresh_token(login_data.id)
            if err:
                return None, err
            if existing:
                self.db.delete(existing)
            hashed = hash_password(refresh_token)
            self.db.add(RefreshToken(user_id=login_data.id, token=hashed))
            self.db.commit()
            return _wrap_return({'access_token': access_token, 'refresh_token': refresh_token})
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_refresh_token(self, user_id: str):
        try:
            token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
            return _wrap_return(token)
        except Exception as e:
            return _wrap_error(e)

    def update_password(self, phone_number: str, new_password: str):
        """Update user password by phone number"""
        try:
            user = self.db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                return None, None
            user.password = hash_password(new_password)
            self.db.commit()
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)



    def get_all_instructors(self, search: Optional[str] = None, page: int = 1, page_size: int = 10):
        try:
            query = self.db.query(User).filter(User.role == "instructor")
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.phone_number.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.profession.ilike(search_term)
                    )
                )
            offset = (page - 1) * page_size
            instructors = query.offset(offset).limit(page_size).all()
            return _wrap_return(instructors)
        except Exception as e:
            return _wrap_error(e)

    def get_instructor_by_id(self, instructor_id: str):
        try:
            instr = self.db.query(User).filter(User.id == instructor_id, User.role == "instructor").first()
            return _wrap_return(instr)
        except DataError as e:
            return _wrap_error(e)
        except Exception as e:
            return _wrap_error(e)

    def update_profile_picture(self, user_id: str, profile_picture_url: str):
        """
        Update the profile picture URL for a user.

        Args:
            user_id (str): The ID of the user.
            profile_picture_url (str): The URL of the profile picture.

        Returns:
            Tuple[User, Optional[Exception]]: The updated user or an error.
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, NotFoundError(detail="User not found")
            user.profile_picture = profile_picture_url
            self.db.commit()
            self.db.refresh(user)
            return _wrap_return(user)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_users_count(self, search: Optional[str] = None, filter: Optional[str] = None, is_active: Optional[bool] = None):
        """
        Get the total count of users with search and filter options.

        Args:
            search (Optional[str]): Search term for user fields.
            filter (Optional[str]): Filter term for user role.

        Returns:
            int: The total number of users matching the criteria.
        """
        try:
            query = self.db.query(User)

            if is_active is not None:
                query = query.filter(User.is_active == is_active)
        
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.phone_number.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.profession.ilike(search_term)
                    )
                )

            if filter:
                query = query.filter(User.role.ilike(f"%{filter}%"))

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_instructors_count(self, search: Optional[str] = None):
        """
        Get the total count of instructors with search options.

        Args:
            search (Optional[str]): Search term for instructor fields.

        Returns:
            int: The total number of instructors matching the criteria.
        """
        try:
            query = self.db.query(User).filter(User.role == "instructor")

            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        
                        User.phone_number.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.profession.ilike(search_term)
                    )
                )

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)
