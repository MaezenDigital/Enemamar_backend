from sqlalchemy.orm import Session
from app.domain.model.course import Payment
from app.utils.exceptions.exceptions import NotFoundError
from typing import Tuple, Optional, Any
from sqlalchemy import func

def _wrap_return(result: Any) -> Tuple[Any, None]:
    return result, None
def _wrap_error(e: Exception) -> Tuple[None, Exception]:
    return None, e

class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_payment(self, payment: Payment):
        """
        Save a new payment to the database.

        Args:
            payment (Payment): The payment object to save.

        Returns:
            Payment: The saved payment object.
        """
        try:
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            return _wrap_return(payment)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_payment(self, tx_ref: str):
        """
        Get a payment by transaction reference.

        Args:
            tx_ref (str): The transaction reference.

        Returns:
            Payment: The payment object if found, None otherwise.
        """
        try:
            payment = (
                self.db.query(Payment)
                .filter(Payment.tx_ref == tx_ref)
                .first()
            )
            return _wrap_return(payment)
        except Exception as e:
            return _wrap_error(e)

    def get_payment_by_id(self, payment_id: str):
        """
        Get a payment by ID.

        Args:
            payment_id (str): The payment ID.

        Returns:
            Payment: The payment object if found, None otherwise.
        """
        try:
            payment = (
                self.db.query(Payment)
                .filter(Payment.id == payment_id)
                .first()
            )
            return _wrap_return(payment)
        except Exception as e:
            return _wrap_error(e)

    def update_payment(self, tx_ref: str, status: str, ref_id: str):
        """
        Update a payment's status and reference ID.

        Args:
            tx_ref (str): The transaction reference.
            status (str): The new status.
            ref_id (str): The reference ID.

        Returns:
            Payment: The updated payment object.

        Raises:
            NotFoundError: If the payment is not found.
        """
        try:
            payment, err = self.get_payment(tx_ref)
            if err:
                return None, err
            if not payment:
                return None, NotFoundError(detail="Payment not found")
            payment.status = status
            payment.ref_id = ref_id
            self.db.commit()
            self.db.refresh(payment)
            return _wrap_return(payment)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_user_payments(
        self,
        user_id: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter: Optional[str] = "success",
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
    ):
        """
        Get all payments for a user, optional pagination, status & date filters.
        """
        try:
            query = self.db.query(Payment).filter(Payment.user_id == user_id)
            if filter:
                query = query.filter(Payment.status == filter)
            if year is not None:
                query = query.filter(func.extract('year', Payment.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Payment.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Payment.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Payment.updated_at) == day)

            if page is not None and page_size is not None:
                query = query.offset((page - 1) * page_size).limit(page_size)
            results = query.order_by(Payment.updated_at.desc()).all()
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)

    def get_user_payments_count(
        self,
        user_id: str,
        filter: Optional[str] = "success",
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
    ) -> int:
        """
        Get the count of payments for a user with optional status and date filtering.

        Args:
            user_id (str): The user ID.
            filter (Optional[str], optional): Filter by payment status. Defaults to None.
            year (Optional[int], optional): Filter by year of updated_at. Defaults to None.
            month (Optional[int], optional): Filter by month of updated_at. Defaults to None.
            week (Optional[int], optional): Filter by ISO week number of updated_at. Defaults to None.
            day (Optional[int], optional): Filter by day of updated_at. Defaults to None.

        Returns:
            int: The count of payments.
        """
        try:
            query = self.db.query(Payment).filter(Payment.user_id == user_id)
            if filter:
                query = query.filter(Payment.status == filter)
            if year is not None:
                query = query.filter(func.extract('year', Payment.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Payment.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Payment.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Payment.updated_at) == day)

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_course_payments(
        self,
        course_id: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter: Optional[str] = "success",
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
    ):
        """
        Get all payments for a course, optional pagination, status & date filters.

        Args:
            course_id (str): The course ID.
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The page size. Defaults to 10.
            status (Optional[str], optional): Filter by payment status. Defaults to None.
            year (Optional[int], optional): Filter by year of updated_at. Defaults to None.
            month (Optional[int], optional): Filter by month of updated_at. Defaults to None.
            week (Optional[int], optional): Filter by ISO week number of updated_at. Defaults to None.
            day (Optional[int], optional): Filter by day of updated_at. Defaults to None.

        Returns:
            List[Payment]: A list of payment objects.
        """
        try:
            query = self.db.query(Payment).filter(Payment.course_id == course_id)
            if filter:
                query = query.filter(Payment.status == filter)
            if year is not None:
                query = query.filter(func.extract('year', Payment.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Payment.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Payment.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Payment.updated_at) == day)

            if page is not None and page_size is not None:
                query = query.offset((page - 1) * page_size).limit(page_size)
            results = query.order_by(Payment.updated_at.desc()).all()
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)

    def get_course_payments_count(
        self,
        course_id: str,
        filter: Optional[str] = "success",
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
    ) -> int:
        """
        Get the count of payments for a course with optional status and date filtering.
        """
        try:
            query = self.db.query(Payment).filter(Payment.course_id == course_id)
            if filter:
                query = query.filter(Payment.status == filter)
            if year is not None:
                query = query.filter(func.extract('year', Payment.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Payment.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Payment.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Payment.updated_at) == day)

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_course_revenue(self, course_id: str):
        """
        Get the total revenue for a course.

        Args:
            course_id (str): The course ID.

        Returns:
            float: The total revenue.
        """
        try:
            total_revenue = (
                self.db.query(func.sum(Payment.amount))
                .filter(Payment.course_id == course_id)
                .filter(Payment.status == "success")
                .scalar()
            ) or 0.0
            return _wrap_return(total_revenue)
        except Exception as e:
            return _wrap_error(e)

    def get_course_revenue_with_date_filter(
        self,
        course_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Get the total revenue for a course with date filtering.

        Args:
            course_id (str): The course ID.
            year, month, week, day: Date filters based on payment updated_at.

        Returns:
            float: The total revenue.
        """
        try:
            query = (
                self.db.query(func.sum(Payment.amount))
                .filter(Payment.course_id == course_id)
                .filter(Payment.status == "success")
            )

            # Apply date filters on updated_at field
            if year is not None:
                query = query.filter(func.extract('year', Payment.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Payment.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Payment.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Payment.updated_at) == day)

            total_revenue = query.scalar() or 0.0
            return _wrap_return(total_revenue)
        except Exception as e:
            return _wrap_error(e)
    
    def get_monthly_revenue(
        self,
        year: int,
        month: int,
        course_id: Optional[str] = None
    ):
        """Get the total revenue for a specific month of a year, optionally filtered by course_id."""
        try:
            query = (
                self.db.query(func.sum(Payment.amount))
                .filter(func.extract('year', Payment.updated_at) == year)
                .filter(func.extract('month', Payment.updated_at) == month)
                .filter(Payment.status == "success")
            )
            if course_id is not None:
                query = query.filter(Payment.course_id == course_id)
            total_revenue = query.scalar() or 0.0
            return _wrap_return(total_revenue)
        except Exception as e:
            return _wrap_error(e)