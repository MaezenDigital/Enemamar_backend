from app.utils.exceptions.exceptions import ValidationError, NotFoundError
from app.domain.schema.comment_review_schema import (
    CommentInput,
    CommentResponse,
    ReviewInput,
    ReviewResponse
)
from app.domain.model.course import Comment, Review
from app.repository.comment_review_repo import CommentReviewRepository
from app.repository.courseRepo import CourseRepository
from app.repository.userRepo import UserRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.config.database import get_db
from uuid import UUID

class CommentReviewService:
    def __init__(self, db):
        """
        Initialize the CommentReviewService with the database session and repositories.

        Args:
            db (Session): SQLAlchemy database session.
        """
        self.db = db
        self.comment_review_repo = CommentReviewRepository(db)
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)

    # Comment methods
    def add_comment(self, user_id: UUID, course_id: str, comment_input: CommentInput):
        """
        Add a new comment to a course.

        Args:
            user_id (UUID): ID of the user adding the comment.
            course_id (str): ID of the course to comment on.
            comment_input (CommentInput): Input data for creating a comment.

        Returns:
            dict: Response containing comment creation details and data.

        Raises:
            ValidationError: If the user or course is invalid or comment creation fails.
        """
        # Validate user
        _, err = self.user_repo.get_user_by_id(str(user_id))

        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid user ID")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))

        # Validate course
        _, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid course ID")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))

        # Create comment
         # Check if user is enrolled in the course
        is_enrolled, err = self.course_repo.get_enrollment(str(user_id), course_id)
        if err:
            raise ValidationError(detail="Failed to check enrollment", data=str(err))
        if not is_enrolled:
            raise ValidationError(detail="User must be enrolled in the course to comment")
        comment = Comment(
            content=comment_input.content,
            user_id=user_id,
            course_id=course_id
        )


        created_comment,err = self.comment_review_repo.create_comment(comment)
        if err:
            if isinstance(err, ValidationError):
                raise ValidationError(detail="Invalid comment data", data=str(err))
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Failed to create comment", data=str(err))
            raise ValidationError(detail="Failed to create comment", data=str(err))

        comment_response = CommentResponse.model_validate(created_comment)

        return {
            "detail": "Comment added successfully",
            "data": comment_response
        }



    def get_comment(self, comment_id: str):
        """
        Retrieve a comment by its ID.

        Args:
            comment_id (str): ID of the comment to retrieve.

        Returns:
            dict: Response containing comment details.

        Raises:
            ValidationError: If the comment ID is invalid or the comment is not found.
        """
        if not comment_id:
            raise ValidationError(detail="Comment ID is required")

        try:
            comment,err = self.comment_review_repo.get_comment(comment_id)
            if err:
                if isinstance(err, NotFoundError):
                    raise ValidationError(detail="Comment not found")
                if isinstance(err, IntegrityError):
                    raise ValidationError(detail="Invalid comment ID")
                raise ValidationError(detail="Failed to retrieve comment", data=str(err))

            comment_response = CommentResponse.model_validate(comment)
            return {
                "detail": "Comment retrieved successfully",
                "data": comment_response
            }
        except NotFoundError as e:
            raise ValidationError(detail=str(e))

    def get_course_comments(self, course_id: str, page: int = 1, page_size: int = 10):
        """
        Retrieve comments for a specific course.

        Args:
            course_id (str): ID of the course.
            page (int): Page number for pagination.
            page_size (int): Number of items per page.

        Returns:
            dict: Response containing paginated comments data and metadata.

        Raises:
            ValidationError: If the course ID is invalid or the course is not found.
        """
        if not course_id:
            raise ValidationError(detail="Course ID is required")

        # Validate course exists
        course, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))
        if not course:
            raise ValidationError(detail="Course not found")

        comments, err = self.comment_review_repo.get_comments_by_course(course_id, page, page_size)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found for comments")
            raise ValidationError(detail="Failed to retrieve course comments", data=str(err))

        comments_response = [CommentResponse.model_validate(comment) for comment in comments]

        total_count, err = self.comment_review_repo.get_comments_count_by_course(course_id)
        if err:
            raise ValidationError(detail="Failed to retrieve comment count", data=str(err))

        return {
            "detail": "Course comments retrieved successfully",
            "data": {
                "comments": comments_response,
                "page": page,
                "page_size": page_size,
                "total_items": total_count
            }
        }

    def get_user_comments(self, user_id: UUID, page: int = 1, page_size: int = 10):
        """
        Retrieve comments by a specific user.

        Args:
            user_id (UUID): ID of the user.
            page (int): Page number for pagination.
            page_size (int): Number of items per page.

        Returns:
            dict: Response containing paginated comments data and metadata.

        Raises:
            ValidationError: If the user ID is invalid or the user is not found.
        """
        if not user_id:
            raise ValidationError(detail="User ID is required")

        # Validate user
        user, err = self.user_repo.get_user_by_id(str(user_id))
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        comments, err = self.comment_review_repo.get_comments_by_user(str(user_id), page, page_size)
        if err:
            raise ValidationError(detail="Failed to retrieve user comments", data=str(err))

        comments_response = [CommentResponse.model_validate(comment) for comment in comments]

        total_count, err = self.comment_review_repo.get_comments_count_by_user(str(user_id))
        if err:
            raise ValidationError(detail="Failed to retrieve comment count", data=str(err))

        return {
            "detail": "User comments retrieved successfully",
            "data": {
                "comments": comments_response,
                "page": page,
                "page_size": page_size,
                "total_items": total_count
            }
        }

    def update_comment(self, comment_id: str, user_id: UUID, comment_input: CommentInput):
        """
        Update a comment.

        Args:
            comment_id (str): ID of the comment to update.
            user_id (UUID): ID of the user updating the comment.
            comment_input (CommentInput): Input data for updating the comment.

        Returns:
            dict: Response containing updated comment details.

        Raises:
            ValidationError: If the comment ID is invalid, the comment is not found,
                            or the user is not the author of the comment.
        """
        if not comment_id:
            raise ValidationError(detail="Comment ID is required")

        try:
            # Get the comment to check ownership
            comment, err = self.comment_review_repo.get_comment(comment_id)
            if err:
                if isinstance(err, NotFoundError):
                    raise ValidationError(detail="Comment not found")
                if isinstance(err, IntegrityError):
                    raise ValidationError(detail="Invalid comment ID")
                raise ValidationError(detail="Failed to retrieve comment", data=str(err))

            # Check if the user is the author of the comment
            if str(comment.user_id) != str(user_id):
                raise ValidationError(detail="You can only update your own comments")

            # Update the comment
            updated_comment, err = self.comment_review_repo.update_comment(comment_id, comment_input.content)
            if err:
                if isinstance(err, NotFoundError):
                    raise ValidationError(detail="Comment not found")
                if isinstance(err, IntegrityError):
                    raise ValidationError(detail="Invalid comment ID")
                raise ValidationError(detail="Failed to update comment", data=str(err))

            comment_response = CommentResponse.model_validate(updated_comment)

            return {
                "detail": "Comment updated successfully",
                "data": comment_response
            }
        except NotFoundError as e:
            raise ValidationError(detail=str(e))

    def delete_comment(self, comment_id: str, user_id: UUID):
        """
        Delete a comment.

        Args:
            comment_id (str): ID of the comment to delete.
            user_id (UUID): ID of the user deleting the comment.

        Returns:
            dict: Response indicating successful deletion.

        Raises:
            ValidationError: If the comment ID is invalid, the comment is not found,
                            or the user is not the author of the comment.
        """
        if not comment_id:
            raise ValidationError(detail="Comment ID is required")

        # Get the comment to check ownership
        comment, err = self.comment_review_repo.get_comment(comment_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Comment not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid comment ID")
            raise ValidationError(detail="Failed to retrieve comment", data=str(err))
        if not comment:
            raise ValidationError(detail="Comment not found")

        # Check if the user is the author of the comment
        if str(comment.user_id) != str(user_id):
            raise ValidationError(detail="You can only delete your own comments")

        # Delete the comment
        _, err = self.comment_review_repo.delete_comment(comment_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Comment not found to delete")
            raise ValidationError(detail="Failed to delete comment", data=str(err))

        return {
            "detail": "Comment deleted successfully"
        }

    # Review methods
    def add_review(self, user_id: UUID, course_id: str, review_input: ReviewInput):
        """
        Add a new review to a course.

        Args:
            user_id (UUID): ID of the user adding the review.
            course_id (str): ID of the course to review.
            review_input (ReviewInput): Input data for creating a review.

        Returns:
            dict: Response containing review creation details and data.

        Raises:
            ValidationError: If the user or course is invalid, the user has already reviewed the course,
                            or review creation fails.
        """
        # Validate user
        user, err = self.user_repo.get_user_by_id(str(user_id))
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        # Validate course
        course, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))
        if not course:
            raise ValidationError(detail="Course not found")

        # Validate rating
        if review_input.rating < 1 or review_input.rating > 5:
            raise ValidationError(detail="Rating must be between 1 and 5")

        # Create review
        review = Review(
            rating=review_input.rating,
            user_id=user_id,
            course_id=course_id
        )

        created_review, err = self.comment_review_repo.create_review(review)
        if err:
            if isinstance(err, ValidationError):
                raise ValidationError(detail=str(err))
            raise ValidationError(detail=f"Failed to add review", data=str(err))

        review_response = ReviewResponse.model_validate(created_review)
        return {
            "detail": "Review added successfully",
            "data": review_response
        }

    def get_review(self, review_id: str):
        """
        Retrieve a review by its ID.

        Args:
            review_id (str): ID of the review to retrieve.

        Returns:
            dict: Response containing review details.

        Raises:
            ValidationError: If the review ID is invalid or the review is not found.
        """
        if not review_id:
            raise ValidationError(detail="Review ID is required")

        review, err = self.comment_review_repo.get_review(review_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Review not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid review ID")
            raise ValidationError(detail="Failed to retrieve review", data=str(err))
        if not review:
            raise ValidationError(detail="Review not found")

        review_response = ReviewResponse.model_validate(review)
        return {
            "detail": "Review retrieved successfully",
            "data": review_response
        }

    def get_course_reviews(self, course_id: str, page: int = 1, page_size: int = 10):
        """
        Retrieve reviews for a specific course.

        Args:
            course_id (str): ID of the course.
            page (int): Page number for pagination.
            page_size (int): Number of items per page.

        Returns:
            dict: Response containing paginated reviews data and metadata.

        Raises:
            ValidationError: If the course ID is invalid or the course is not found.
        """
        if not course_id:
            raise ValidationError(detail="Course ID is required")

        # Validate course exists
        course, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))
        if not course:
            raise ValidationError(detail="Course not found")

        reviews, err = self.comment_review_repo.get_reviews_by_course(course_id, page, page_size)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found for reviews")
            raise ValidationError(detail="Failed to retrieve course reviews", data=str(err))

        reviews_response = [ReviewResponse.model_validate(review) for review in reviews]

        average_rating, err = self.comment_review_repo.get_average_rating_by_course(course_id)
        if err:
            raise ValidationError(detail="Failed to retrieve average rating", data=str(err))
        

        total_count, err = self.comment_review_repo.get_reviews_count_by_course(course_id)
        if err:
            raise ValidationError(detail="Failed to retrieve review count", data=str(err))

        return {
            "detail": "Course reviews retrieved successfully",
            "data": {
                "reviews": reviews_response,
                "average_rating": average_rating,
                "page": page,
                "page_size": page_size,
                "total_items": total_count
            }
        }

    def get_user_reviews(self, user_id: UUID, page: int = 1, page_size: int = 10):
        """
        Retrieve reviews by a specific user.

        Args:
            user_id (UUID): ID of the user.
            page (int): Page number for pagination.
            page_size (int): Number of items per page.

        Returns:
            dict: Response containing paginated reviews data and metadata.

        Raises:
            ValidationError: If the user ID is invalid or the user is not found.
        """
        if not user_id:
            raise ValidationError(detail="User ID is required")

        # Validate user
        user, err = self.user_repo.get_user_by_id(str(user_id))
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        reviews, err = self.comment_review_repo.get_reviews_by_user(str(user_id), page, page_size)
        if err:
            raise ValidationError(detail="Failed to retrieve user reviews", data=str(err))

        reviews_response = [ReviewResponse.model_validate(review) for review in reviews]

        total_count, err = self.comment_review_repo.get_reviews_count_by_user(str(user_id))
        if err:
            raise ValidationError(detail="Failed to retrieve review count", data=str(err))

        return {
            "detail": "User reviews retrieved successfully",
            "data": {
                "reviews": reviews_response,
                "page": page,
                "page_size": page_size,
                "total_items": total_count
            }
        }

    def update_review(self, review_id: str, user_id: UUID, review_input: ReviewInput):
        """
        Update a review.

        Args:
            review_id (str): ID of the review to update.
            user_id (UUID): ID of the user updating the review.
            review_input (ReviewInput): Input data for updating the review.

        Returns:
            dict: Response containing updated review details.

        Raises:
            ValidationError: If the review ID is invalid, the review is not found,
                            or the user is not the author of the review.
        """
        if not review_id:
            raise ValidationError(detail="Review ID is required")

        # Validate rating
        if review_input.rating < 1 or review_input.rating > 5:
            raise ValidationError(detail="Rating must be between 1 and 5")

        # Get the review to check ownership
        review, err = self.comment_review_repo.get_review(review_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Review not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid review ID")
            raise ValidationError(detail="Failed to retrieve review", data=str(err))
        if not review:
            raise ValidationError(detail="Review not found")

        # Check if the user is the author of the review
        if str(review.user_id) != str(user_id):
            raise ValidationError(detail="You can only update your own reviews")

        # Update the review
        updated_review, err = self.comment_review_repo.update_review(review_id, review_input.rating)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Review not found to update")
            if isinstance(err, ValidationError):
                raise ValidationError(detail=str(err))
            raise ValidationError(detail="Failed to update review", data=str(err))

        review_response = ReviewResponse.model_validate(updated_review)

        return {
            "detail": "Review updated successfully",
            "data": review_response
        }

    def delete_review(self, review_id: str, user_id: UUID):
        """
        Delete a review.

        Args:
            review_id (str): ID of the review to delete.
            user_id (UUID): ID of the user deleting the review.

        Returns:
            dict: Response indicating successful deletion.

        Raises:
            ValidationError: If the review ID is invalid, the review is not found,
                            or the user is not the author of the review.
        """
        if not review_id:
            raise ValidationError(detail="Review ID is required")

        # Get the review to check ownership
        review, err = self.comment_review_repo.get_review(review_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Review not found")
            if isinstance(err, IntegrityError):
                raise ValidationError(detail="Invalid review ID")
            raise ValidationError(detail="Failed to retrieve review", data=str(err))
        if not review:
            raise ValidationError(detail="Review not found")

        # Check if the user is the author of the review
        if str(review.user_id) != str(user_id):
            raise ValidationError(detail="You can only delete your own reviews")

        # Delete the review
        _, err = self.comment_review_repo.delete_review(review_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Review not found to delete")
            raise ValidationError(detail="Failed to delete review", data=str(err))

        return {
            "detail": "Review deleted successfully"
        }

    def get_user_review_for_course(self, user_id: UUID, course_id: str):
        """
        Get a user's review for a specific course.

        Args:
            user_id (UUID): ID of the user.
            course_id (str): ID of the course.

        Returns:
            dict: Response containing the user's review for the course, or None if not found.

        Raises:
            ValidationError: If the user or course ID is invalid.
        """
        if not user_id:
            raise ValidationError(detail="User ID is required")
        if not course_id:
            raise ValidationError(detail="Course ID is required")

        # Validate user
        user, err = self.user_repo.get_user_by_id(str(user_id))
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="User not found")
            raise ValidationError(detail="Failed to retrieve user", data=str(err))
        if not user:
            raise ValidationError(detail="User not found")

        # Validate course
        course, err = self.course_repo.get_course(course_id)
        if err:
            if isinstance(err, NotFoundError):
                raise ValidationError(detail="Course not found")
            raise ValidationError(detail="Failed to retrieve course", data=str(err))
        if not course:
            raise ValidationError(detail="Course not found")

        review, err = self.comment_review_repo.get_user_review_for_course(str(user_id), course_id)
        if err:
            raise ValidationError(detail="Failed to retrieve user review", data=str(err))
        if not review:
            return {
                "detail": "User has not reviewed this course",
                "data": None
            }

        review_response = ReviewResponse.model_validate(review)
        return {
            "detail": "User review retrieved successfully",
            "data": review_response
        }


def get_comment_review_service(db: Session = Depends(get_db)):
    return CommentReviewService(db)
