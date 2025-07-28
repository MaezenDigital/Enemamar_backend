from sqlalchemy.orm import Session, joinedload
from app.domain.model.course import Course, Enrollment, Lesson, Video, Comment, Review, Payment
from app.domain.schema.courseSchema import CourseAnalysisResponse
from app.utils.exceptions.exceptions import NotFoundError, ValidationError
from sqlalchemy import or_, func
from typing import Tuple, Optional, Any, List
from app.repository.payment_repo import PaymentRepository
from app.repository.lesson_repo import LessonRepository
from math import ceil

def _wrap_return(result: Any) -> Tuple[Any, None]:
    return result, None
def _wrap_error(e: Exception) -> Tuple[None, Exception]:
    return None, e

class CourseRepository:
    """
    Repository class for handling course-related database operations.
    """

    def __init__(self, db: Session):
        """
        Initialize the CourseRepository.

        Args:
            db (Session): The database session.
        """
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.lesson_repo = LessonRepository(db)

    def create_course(self, course: Course):
        """
        Create a new course in the database.

        Args:
            course (Course): The course object to be created.

        Returns:
            Course: The created course object.
        """
        try:
            self.db.add(course)
            self.db.commit()
            self.db.refresh(course)
            return _wrap_return(course)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_course_with_lessons(self, course_id: str):
        """
        Get a course with its lessons and instructor.

        Args:
            course_id (str): The ID of the course.

        Returns:
            Course: The course object with lessons and instructor loaded.

        Raises:
            NotFoundError: If the course is not found.
        """
        try:
            course = (
                self.db.query(Course)
                .options(
                    joinedload(Course.lessons),
                    joinedload(Course.instructor)
                )
                .filter(Course.id == course_id)
                .first()
            )
            if not course:
                return None, NotFoundError(detail="Course not found")
            
            return _wrap_return(course)
        except Exception as e:
            return _wrap_error(e)

    def get_course(self, course_id: str):
        """
        Get a course by its ID.

        Args:
            course_id (str): The ID of the course.

        Returns:
            Course: The course object with lessons and instructor loaded.
        """
        return self.get_course_with_lessons(course_id)

    def get_courses(self, page: int = 1, page_size: int = 10, search: Optional[str] = None, filter: Optional[str] = None):
        """
        Get all courses with pagination, search, and filter options.

        Args:
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The number of items per page. Defaults to 10.
            search (Optional[str], optional): Search term for course title, description, or tags. Defaults to None.
            filter (Optional[str], optional): Filter term for course tags. Defaults to None.

        Returns:
            List[Course]: A list of course objects.
        """
        query = (
            self.db.query(Course)
            .options(
                joinedload(Course.instructor)  # Only load instructor relationship
            )
        )

        if search:
            # Fuzzy search using ILIKE for case-insensitive matching
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term),
                    func.array_to_string(Course.tags, ' ').ilike(search_term)
                )
            )

        if filter:
            query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter}%"))

        try:
            results = (query
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all())
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)

    def enroll_course(self, user_id: str, course_id: str):
        """
        Enroll a user in a course.

        Args:
            user_id (str): The ID of the user.
            course_id (str): The ID of the course.

        Returns:
            Enrollment: The created enrollment object.

        Raises:
            NotFoundError: If the course is not found.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None, NotFoundError(detail="Course not found")
            
            enrollment = Enrollment(user_id=user_id, course_id=course_id)
            self.db.add(enrollment)
            self.db.commit()
            self.db.refresh(enrollment)
            return _wrap_return(enrollment)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_enrolled_courses(self, user_id: str, page: int = 1, page_size: int = 10, search: Optional[str] = None):
        """
        Get all courses enrolled by a user with pagination and search options.

        Args:
            user_id (str): The ID of the user.
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The number of items per page. Defaults to 10.
            search (Optional[str], optional): Search term for course title or description. Defaults to None.

        Returns:
            List[Enrollment]: A list of enrollment objects with associated courses.
        """
        query = (
            self.db.query(Enrollment)
            .options(joinedload(Enrollment.course))
            .filter(Enrollment.user_id == user_id)
        )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term)
                )
            )

        try:
            items = (query
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all())
            return _wrap_return(items)
        except Exception as e:
            return _wrap_error(e)

    def get_enrolled_users(
        self,
        course_id: str,
        year: Optional[int]   = None,
        month: Optional[int]  = None,
        week: Optional[int]   = None,
        day: Optional[int]    = None,
        page: Optional[int]   = None,
        page_size: Optional[int] = None,
    ):
        """
        Get enrollments for a course, filtered by date on `Enrollment.created_at`,
        and optionally paginated only if page & page_size are provided.
        """
        query = (
            self.db.query(Enrollment)
            .filter(Enrollment.course_id == course_id)
        )
        if year is not None:
            query = query.filter(func.extract('year', Enrollment.enrolled_at) == year)
        if month is not None:
            query = query.filter(func.extract('month', Enrollment.enrolled_at) == month)
        if week is not None:
            query = query.filter(func.extract('week', Enrollment.enrolled_at) == week)
        if day is not None:
            query = query.filter(func.extract('day', Enrollment.enrolled_at) == day)

        try:
            if page is not None and page_size is not None:
                query = query.offset((page - 1) * page_size).limit(page_size)
            results = query.all()
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)

    def get_enrollment(self, user_id: str, course_id: str):
        """
        Get an enrollment by user ID and course ID.

        Args:
            user_id (str): The ID of the user.
            course_id (str): The ID of the course.

        Returns:
            Enrollment: The enrollment object.

        Raises:
            NotFoundError: If the enrollment is not found.
        """
        try:
            enrollment = (self.db.query(Enrollment)
                .filter(Enrollment.user_id == user_id)
                .filter(Enrollment.course_id == course_id)
                .first())
            if not enrollment:
                return None, None
            return _wrap_return(enrollment)
        except Exception as e:
            return _wrap_error(e)

    def get_enrolled_users_count(self, course_id: str) -> int:
        """
        Get the count of users enrolled in a course.

        Args:
            course_id (str): The ID of the course.

        Returns:
            int: The number of enrolled users.
        """
        try:
            count = self.db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_courses_by_instructor(self, instructor_id: str):
        """
        Get all courses by an instructor with course analysis.

        Args:
            instructor_id (str): The ID of the instructor.

        Returns:
            List[CourseAnalysisResponse]: A list of course analysis responses.
        """
        try:
            courses = self.db.query(Course).filter(Course.instructor_id == instructor_id).all()
            analyses = []
            for c in courses:
                # Call without date filters for backward compatibility
                analysis, err = self.course_analysis(c.id)
                if err:
                    return None, err
                analyses.append(analysis)
            return _wrap_return(analyses)
        except Exception as e:
            return _wrap_error(e)

    def course_analysis(
        self,
        course_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Perform analysis on a course with optional time filtering.

        Args:
            course_id (str): The ID of the course.
            year, month, week, day: Date filters for enrollment and payment calculations.

        Returns:
            CourseAnalysisResponse: The course analysis response.

        Raises:
            NotFoundError: If the course is not found.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None, NotFoundError(detail="Course not found")
            lessons_count, err = self.get_lessons_count(course_id)
            if err:
                return None, err

            # Get enrollment count with date filtering
            enrolled_count, err = self.get_enrolled_users_count_with_date_filter(
                course_id=course_id,
                year=year,
                month=month,
                week=week,
                day=day
            )
            if err:
                return None, err

            for lesson in course.lessons:
                lesson.video = None

            # Get revenue with date filtering
            revenue, err = self.get_course_revenue_with_date_filter(
                course_id=course_id,
                year=year,
                month=month,
                week=week,
                day=day
            )
            if err:
                return None, err

            analysis = CourseAnalysisResponse(
                course=course, view_count=course.view_count,
                no_of_enrollments=enrolled_count, no_of_lessons=lessons_count,
                revenue=revenue)
            return _wrap_return(analysis)
        except Exception as e:
            return _wrap_error(e)

    def get_total_courses_count(self, search: Optional[str] = None, filter_tag: Optional[str] = None):
        """
        Get the total count of courses with search and filter options.

        Args:
            search (Optional[str], optional): Search term for course title or description. Defaults to None.
            filter_tag (Optional[str], optional): Filter term for course tags. Defaults to None.

        Returns:
            int: The total number of courses matching the criteria.
        """
        try:
            query = (
                self.db.query(Course)
                .options(joinedload(Course.instructor))            )
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Course.title.ilike(search_term),
                        Course.description.ilike(search_term)
                    )
                )

            if filter_tag:
                query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter_tag}%"))

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_total_enrolled_users_count(self, course_id):
        """
        Get the total count of users enrolled in a course.

        Args:
            course_id: The ID of the course.

        Returns:
            int: The total number of enrolled users.
        """
        try:
            count = self.db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_user_courses_count(self, user_id: str, search: Optional[str] = None):
        """
        Get the count of courses enrolled by a user with search option.

        Args:
            user_id (str): The ID of the user.
            search (Optional[str], optional): Search term for course title or description. Defaults to None.

        Returns:
            int: The number of courses enrolled by the user matching the criteria.
        """
        try:
            count = self.db.query(Enrollment).filter(Enrollment.user_id == user_id).count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_course_revenue(self, course_id: str):
        return self.payment_repo.get_course_revenue(course_id)

    def get_course_revenue_with_date_filter(
        self,
        course_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Get course revenue with date filtering.
        """
        return self.payment_repo.get_course_revenue_with_date_filter(
            course_id=course_id,
            year=year,
            month=month,
            week=week,
            day=day
        )

    def get_enrolled_users_count_with_date_filter(
        self,
        course_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None
    ):
        """
        Get enrollment count with date filtering.
        """
        try:
            query = self.db.query(Enrollment).filter(Enrollment.course_id == course_id)

            # Apply date filters on enrolled_at field
            if year is not None:
                query = query.filter(func.extract('year', Enrollment.enrolled_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Enrollment.enrolled_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Enrollment.enrolled_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Enrollment.enrolled_at) == day)

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_lessons_count(self, course_id: str) -> int:
        return self.lesson_repo.get_lessons_count(course_id)

    def save_thumbnail(self, course_id: str, thumbnail_url: str):
        """
        Persist a thumbnail URL on a course.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None, NotFoundError(detail="Course not found for thumbnail")
            course.thumbnail_url = thumbnail_url
            self.db.commit()
            return _wrap_return(course)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def update_course(self, course_id: str, course_data: dict):
        """
        Update a course in the database.

        Args:
            course_id (str): The ID of the course to update.
            course_data (dict): Dictionary containing the fields to update.

        Returns:
            Course: The updated course object.

        Raises:
            NotFoundError: If the course is not found.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None, NotFoundError(detail="Course not found")

            # Update only the fields that are provided
            for key, value in course_data.items():
                if hasattr(course, key) and value is not None:
                    setattr(course, key, value)

            self.db.commit()
            self.db.refresh(course)
            return _wrap_return(course)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def delete_course(self, course_id: str):
        """
        Delete a course from the database.

        With CASCADE DELETE configured in the model, this will automatically delete:
        - Enrollments
        - Payments
        - Comments
        - Reviews
        - Lessons and their videos

        Args:
            course_id (str): The ID of the course to delete.

        Returns:
            Course: The deleted course object.

        Raises:
            NotFoundError: If the course is not found.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None, NotFoundError(detail="Course not found")

            # With CASCADE DELETE configured in the model, deleting the course
            # will automatically delete all related records
            self.db.delete(course)
            self.db.commit()
            return _wrap_return(course)
        except Exception as e:
            self.db.rollback()
            return _wrap_error(e)

    def get_all_courses_analytics(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        search: Optional[str] = None,
        filter: Optional[str] = None
    ):
        """
        Get analytics for all courses with date filtering and pagination.

        Args:
            year, month, week, day: Date filters based on course updated_at
            page, page_size: Pagination parameters
            search: Search term for course title or description
            filter: Filter term for course tags

        Returns:
            Tuple[List[CourseAnalysisResponse], Exception]: List of course analytics or error
        """
        try:
            query = (
                self.db.query(Course)
                .options(joinedload(Course.instructor))
            )

            # Apply date filters on updated_at field
            if year is not None:
                query = query.filter(func.extract('year', Course.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Course.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Course.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Course.updated_at) == day)

            # Apply search filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Course.title.ilike(search_term),
                        Course.description.ilike(search_term)
                    )
                )

            if filter:
                query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter}%"))

            # Apply pagination if provided
            if page is not None and page_size is not None:
                query = query.offset((page - 1) * page_size).limit(page_size)

            courses = query.all()

            # Generate analytics for each course
            analytics_list = []
            for course in courses:
                # Call without date filters since this method handles its own date filtering
                analysis, err = self.course_analysis(course.id)
                if err:
                    return None, err
                analytics_list.append(analysis)

            return _wrap_return(analytics_list)
        except Exception as e:
            return _wrap_error(e)

    def get_instructor_courses_analytics(
        self,
        instructor_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        search: Optional[str] = None,
        filter: Optional[str] = None
    ):
        """
        Get analytics for courses assigned to a specific instructor with date filtering and pagination.

        Args:
            instructor_id: ID of the instructor
            year, month, week, day: Date filters based on course created_at
            page, page_size: Pagination parameters
            search: Search term for course title or description
            filter: Filter term for course tags

        Returns:
            Tuple[List[CourseAnalysisResponse], Exception]: List of course analytics or error
        """
        try:
            query = (
                self.db.query(Course)
                .options(joinedload(Course.instructor))
                .filter(Course.instructor_id == instructor_id)
            )

            # Apply date filters on created_at field
            if year is not None:
                query = query.filter(func.extract('year', Course.created_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Course.created_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Course.created_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Course.created_at) == day)

            # Apply search filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Course.title.ilike(search_term),
                        Course.description.ilike(search_term)
                    )
                )

            if filter:
                query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter}%"))

            # Apply pagination if provided
            if page is not None and page_size is not None:
                query = query.offset((page - 1) * page_size).limit(page_size)

            courses = query.all()

            # Generate analytics for each course
            analytics_list = []
            for course in courses:
                # Call without date filters since this method handles its own date filtering
                analysis, err = self.course_analysis(course.id)
                if err:
                    return None, err
                analytics_list.append(analysis)

            return _wrap_return(analytics_list)
        except Exception as e:
            return _wrap_error(e)

    def get_all_courses_analytics_count(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
        search: Optional[str] = None,
        filter: Optional[str] = None
    ):
        """
        Get total count of courses for admin analytics with filters.
        """
        try:
            query = self.db.query(Course)

            # Apply date filters on updated_at field
            if year is not None:
                query = query.filter(func.extract('year', Course.updated_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Course.updated_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Course.updated_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Course.updated_at) == day)

            # Apply search filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Course.title.ilike(search_term),
                        Course.description.ilike(search_term)
                    )
                )

            if filter:
                query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter}%"))

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_instructor_courses_analytics_count(
        self,
        instructor_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        day: Optional[int] = None,
        search: Optional[str] = None,
        filter: Optional[str] = None
    ):
        """
        Get total count of courses for instructor analytics with filters.
        """
        try:
            query = (
                self.db.query(Course)
                .filter(Course.instructor_id == instructor_id)
            )

            # Apply date filters on created_at field
            if year is not None:
                query = query.filter(func.extract('year', Course.created_at) == year)
            if month is not None:
                query = query.filter(func.extract('month', Course.created_at) == month)
            if week is not None:
                query = query.filter(func.extract('week', Course.created_at) == week)
            if day is not None:
                query = query.filter(func.extract('day', Course.created_at) == day)

            # Apply search filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Course.title.ilike(search_term),
                        Course.description.ilike(search_term)
                    )
                )

            if filter:
                query = query.filter(func.array_to_string(Course.tags, ' ').ilike(f"%{filter}%"))

            count = query.count()
            return _wrap_return(count)
        except Exception as e:
            return _wrap_error(e)

    def get_instructor_enrollments(self, instructor_id: str, days: int = 7):
        """
        Get all enrollments for courses taught by the given instructor within the past `days` days, sorted by enrollment date descending.
        """
        from datetime import datetime, timezone, timedelta
        # build query joining Enrollment to Course and filtering by instructor
        query = (
            self.db.query(Enrollment)
            .join(Course, Enrollment.course)
            .options(joinedload(Enrollment.user), joinedload(Enrollment.course))
            .filter(Course.instructor_id == instructor_id)
        )
        # calculate cutoff timestamp
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        # apply date filter and ordering
        query = query.filter(Enrollment.enrolled_at >= cutoff).order_by(Enrollment.enrolled_at.desc())
        try:
            results = query.all()
            return _wrap_return(results)
        except Exception as e:
            return _wrap_error(e)
    
    def course_instructor(self, course_id: str):
        """
        Get the instructor of a course by course ID.

        Args:
            course_id (str): The ID of the course.

        Returns:
            Instructor: The instructor object associated with the course.

        Raises:
            NotFoundError: If the course or instructor is not found.
        """
        try:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if not course or not course.instructor_id:
                return None, NotFoundError(detail="Course or instructor not found")
            return _wrap_return(course.instructor_id)
        except Exception as e:
            return _wrap_error(e)
