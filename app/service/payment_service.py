import json
from math import ceil
from app.utils.exceptions.exceptions import ValidationError, NotFoundError
from app.domain.schema.courseSchema import (
    PaymentData,
    PaymentResponse,
    CallbackPayload,
    CourseResponse,
)
from app.domain.model.course import Payment
from app.repository.payment_repo import PaymentRepository
from app.repository.courseRepo import CourseRepository
from app.repository.userRepo import UserRepository
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.config.database import get_db
from typing import Optional
from app.utils.chapa.chapa import pay_course, verify_payment, generete_tx_ref
from app.domain.schema.courseSchema import EnrollmentResponse
from app.core.config.env import get_settings
from app.utils.otp.sms import send_sms
settings = get_settings()
class PaymentService:
    def __init__(self, db: Session):
        self.payment_repo = PaymentRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)

    def initiate_payment(self, user_id, course_id):
        """
        Initiate a payment for a course.

        Args:
            user_id: The user ID.
            course_id: The course ID.

        Returns:
            dict: The payment response.

        Raises:
            ValidationError: If the payment fails.
        """
        # Validate user exists
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            raise ValidationError(detail="Error fetching user", data=str(err))
        if not user:
            raise NotFoundError(detail="User not found")

        # validate if user is not admin
        if user.role == "admin":
            raise ValidationError(detail="Admins cannot enroll in courses")
        # Validate course exists
        course, err = self.course_repo.get_course(course_id)

        course_dto = CourseResponse.model_validate(course)
        if err:
            raise ValidationError(detail="Error fetching course", data=str(err))
        if not course:
            raise NotFoundError(detail="Course not found")

        # Check if user is already enrolled
        enrollment, err = self.course_repo.get_enrollment(user_id, course_id)
        if err:
            raise ValidationError(detail="Error fetching enrollment", data=str(err))
        if enrollment:
            raise ValidationError(detail="User already enrolled in course")

        if course_dto.price > 0:
            callback = f"{settings.BASE_URL}/payment/callback"

            tx_ref = generete_tx_ref(12)
            amount = course_dto.price
            
            if course_dto.discount:
                amount = ceil(course_dto.price - ((course_dto.discount/100) * course_dto.price))

            data = PaymentData(
                tx_ref=tx_ref,
                user_id=user_id,
                course_id=course_id,
                first_name=user.first_name,
                last_name=user.last_name,
                amount=amount,
                title=course.title,
                callback_url=callback,
                phone_number="0"+user.phone_number
            )
            print("Payment data:", data)
            try:
                response = pay_course(data)
            except Exception as e:
                raise ValidationError(detail="Payment initiation failed", data=str(e))

            if response.get("status") != "success":
                raise ValidationError(detail=response['message'])

            payment = Payment(
                user_id=user_id,
                course_id=course_id,
                amount=amount,
                tx_ref=tx_ref
            )
            print("Payment object:", payment)

            payment, err = self.payment_repo.save_payment(payment)
            if err:
                raise ValidationError(detail="Error saving payment", data=str(err))

            return {"detail": "Payment initiated", "data": {"payment": PaymentResponse.model_validate(payment), "chapa_response": response}}

        else:
            # Enroll course for free
            enrollment,err = self.course_repo.enroll_course(user_id, course_id)
            if err:
                raise ValidationError(detail="Error enrolling course", data=str(err))
            if not enrollment:
                raise ValidationError(detail="Error enrolling course")
            # Check if user is already enrolled

            # Convert SQLAlchemy Enrollment object to Pydantic Response Model
            enrollment_response = EnrollmentResponse.model_validate(enrollment)

            return {"detail": "Course enrolled successfully", "data": enrollment_response}

    def process_payment_callback(self, payload: CallbackPayload):
        """
        Process a payment callback.

        Args:
            payload (CallbackPayload): The callback payload.

        Returns:
            dict: The enrollment response.

        Raises:
            ValidationError: If the payment fails.
        """
        # Validate payment exists
        # payment, err = self.payment_repo.get_payment(payload.trx_ref)
        # if err:
        #     raise ValidationError(detail="Error fetching payment", data=str(err))
        # if not payment:
        #     raise NotFoundError(detail="Payment not found")

        # Verify payment with payment provider
        try:
            response = verify_payment(payload.trx_ref)
        except Exception as e:
            raise ValidationError(detail="Payment verification failed")

        print(response["data"]["reference"])

        if response["status"] != "success":
            _, err = self.payment_repo.update_payment(payload.trx_ref, status=payload.status, ref_id=payload.reference)
            if err:
                raise ValidationError(detail="Error updating payment status to failed", data=str(err))
            raise ValidationError(detail="Payment failed")

        # Update payment status

        payment, err = self.payment_repo.update_payment(payload.trx_ref, status=payload.status, ref_id=payload.reference)
        if err:
            raise ValidationError(detail="Error updating payment status to success", data=str(err))
        payment = PaymentResponse.model_validate(payment)

        # Validate user exists
        user, err = self.user_repo.get_user_by_id(payment.user_id)
        if err:
            raise ValidationError(detail="Error fetching user after payment", data=str(err))
        if not user:
            raise NotFoundError(detail="User not found")

        # Validate course exists
        course,err = self.course_repo.get_course(payment.course_id)
        if err:
            raise ValidationError(detail="Error fetching course after payment", data=str(err))

        if not course:
            raise NotFoundError(detail="Course not found")

        # Enroll course
        enrollment, err = self.course_repo.enroll_course(user.id, course.id)
        
        if err:
            raise ValidationError(detail="Error enrolling course", data=str(err))
        if not enrollment:
            raise ValidationError(detail="Error enrolling course")

        try:
            message = f"You have successfully enrolled in {course.title}. Thank you for choosing our platform!"
            phone_number = f"0{user.phone_number}"
            print("Sending SMS to:", phone_number)
            print("Message:", message)
            status_code, content = send_sms(phone_number, message)

            print("SMS Status Code:", status_code)
            if status_code != 200:
                content_decoded = content
                if isinstance(content, (bytes, bytearray)):
                    try:
                        content_decoded = json.loads(content)
                    except Exception:
                        content_decoded = content.decode("utf-8", errors="ignore")
                print("Error sending SMS:", content_decoded)

        except Exception as e:
            print("Error sending SMS:", e)


        # Convert SQLAlchemy Enrollment object to Pydantic Response Model
        enrollment_response = EnrollmentResponse.model_validate(enrollment)

        return {"detail": "Course enrolled successfully", "data": enrollment_response}

    def get_user_payments(
        self,
        user_id: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Get payments for a user, optional pagination, status & date filters.
        """
        if not user_id:
            raise ValidationError(detail="User ID is required")
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            raise ValidationError(detail="Error fetching user", data=str(err))
        if not user:
            raise NotFoundError(detail="User not found")

        payments, err = self.payment_repo.get_user_payments(
            user_id, page, page_size, filter, year, month, week, day
        )
        if err:
            raise ValidationError(detail="Error fetching payments", data=str(err))
        payments_response = [PaymentResponse.model_validate(p) for p in payments]

        result = {
            "detail": "User payments fetched successfully",
            "data": payments_response
        }
        if page is not None and page_size is not None:
            total, err = self.payment_repo.get_user_payments_count(
                user_id, filter, year, month, week, day
            )
            if err:
                raise ValidationError(detail="Error fetching payments count", data=str(err))
            result["pagination"] = {
                "page": page,
                "page_size": page_size,
                "total_items": total
            }
        return result

    def checkAdminOrOwner(self, user_id, course_id):
        user, err = self.user_repo.get_user_by_id(user_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        if user.role == "admin":
            return True

        course, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))
        if not course:
            raise ValidationError(detail="Course not found")

        print("instructor_id", course.instructor_id)
        print("user_id", user_id)
        if str(course.instructor_id) == user_id:
            return True

        return False


    def get_payment(self, payment_id: str):
        """
        Get a payment by ID.

        Args:
            payment_id (str): The payment ID.

        Returns:
            dict: The payment response.

        Raises:
            ValidationError: If the payment ID is invalid or the payment is not found.
        """
        if not payment_id:
            raise ValidationError(detail="Payment ID is required")

        payment, err = self.payment_repo.get_payment_by_id(payment_id)
        if err:
            raise ValidationError(detail="Error fetching payment", data=str(err))
        if not payment:
            raise NotFoundError(detail="Payment not found")

        payment_response = PaymentResponse.model_validate(payment)

        return {
            "detail": "Payment fetched successfully",
            "data": payment_response
        }

    def get_course_payments(
        self,
        course_id: str,
        user_id: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Get payments for a course, optional pagination, status & date filters.
        """
        if not course_id:
            raise ValidationError(detail="Course ID is required")

        if not self.checkAdminOrOwner(user_id, course_id):
            raise ValidationError(detail="You are not authorized to view this course")

        payments, err = self.payment_repo.get_course_payments(
            course_id, page, page_size, filter, year, month, week, day
        )
        if err:
            raise ValidationError(detail="Error fetching course payments", data=str(err))
        payments_response = [PaymentResponse.model_validate(p) for p in payments]

        result = {
            "detail": "Course payments fetched successfully",
            "data": payments_response
        }
        if page is not None and page_size is not None:
            total, err = self.payment_repo.get_course_payments_count(
                course_id, filter, year, month, week, day
            )
            if err:
                raise ValidationError(detail="Error fetching course payments count", data=str(err))
            result["pagination"] = {
                "page": page,
                "page_size": page_size,
                "total_items": total
            }
        return result
def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    """
    Get a PaymentService instance.

    Args:
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        PaymentService: A PaymentService instance.
    """
    return PaymentService(db)
