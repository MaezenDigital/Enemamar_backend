from fastapi import APIRouter, Depends, status
from app.domain.schema.courseSchema import (
    SearchParams,
    CourseResponse,
    EnrollmentResponse,
    EnrollResponse,
    CourseAnalysisResponse,
    DateFilterParams
)
from app.domain.schema.responseSchema import (
    CourseListResponse, CourseDetailResponse, EnrollmentResponse as EnrollmentResponseModel,
    BaseResponse, ErrorResponse, PaginatedResponse
)
from app.service.courseService import CourseService, get_course_service
from app.utils.middleware.dependancies import is_logged_in, is_admin, is_admin_or_instructor
from uuid import UUID
from typing import Dict, Any

# Course router
course_router = APIRouter(
    prefix="/courses",
    tags=["course"]
)

@course_router.get(
    "/",
    # response_model=CourseListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all courses",
    description="Retrieve a paginated list of all available courses with optional filtering and search.",
)
async def get_courses(
    search_params: SearchParams = Depends(),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve a paginated list of all available courses.

    This endpoint returns a list of all courses in the system with pagination support.
    You can filter and search courses based on various criteria.

    - **page**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 10, max: 100)
    - **search**: Optional search term to filter courses by title or description
    - **filter**: Optional filter parameter (e.g., 'price_low', 'price_high', 'newest')
    """
    return course_service.getCourses(
        page=search_params.page,
        page_size=search_params.page_size,
        search=search_params.search,
        filter=search_params.filter
    )

@course_router.get(
    "/enrolled",
    # response_model=CourseListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get enrolled courses",
    description="Retrieve a paginated list of courses enrolled by the current user.",
    
)
async def get_enrolled_courses(
    search_params: SearchParams = Depends(),
    decoded_token: dict = Depends(is_logged_in),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve a paginated list of courses enrolled by the current user.

    This endpoint returns all courses that the authenticated user has enrolled in,
    with pagination support and optional search functionality.

    - **page**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 10, max: 100)
    - **search**: Optional search term to filter enrolled courses by title or description

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = decoded_token.get("id")
    user_id = UUID(user_id)
    response = course_service.getEnrolledCourses(
        user_id=user_id,
        page=search_params.page,
        page_size=search_params.page_size,
        search=search_params.search
    )
    return response

@course_router.post(
    "/enroll/{course_id}",
    # response_model=EnrollmentResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in a course",
    description="Enroll the current user in a specific course.",
    
)
async def enroll_course(
    course_id: str,
    decoded_token: dict = Depends(is_logged_in),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Enroll the current user in a specific course.

    This endpoint creates an enrollment record linking the authenticated user to the specified course.
    If the course requires payment, this endpoint will initiate the payment process.

    - **course_id**: UUID of the course to enroll in

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = decoded_token.get("id")
    user_id = UUID(user_id)
    return course_service.enrollCourse(
        user_id=user_id,
        course_id=course_id
    )
@course_router.delete(
    "/enroll/{course_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Unenroll from a course",
    description="Unenroll the current user from a specific course.",
    
)
async def unenroll_course(
    course_id: str,
    decoded_token: dict = Depends(is_logged_in),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Unenroll the current user from a specific course.

    This endpoint removes the enrollment record linking the authenticated user to the specified course.

    - **course_id**: UUID of the course to unenroll from

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = decoded_token.get("id")
    user_id = UUID(user_id)
    return course_service.unenrollCourse(
        user_id=user_id,
        course_id=course_id
    )

@course_router.get(
    "/{course_id}",
    # response_model=CourseDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get course by ID",
    description="Retrieve detailed information about a specific course by its ID.",
    
)
async def get_course(
    course_id: str,
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve detailed information about a specific course.

    This endpoint returns comprehensive details about a course, including its lessons,
    instructor information, pricing, and other metadata.

    - **course_id**: UUID of the course to retrieve
    """
    is_admin = False  # Default to false, can be set to true if needed
    course_response = course_service.getCourse(course_id, is_admin)
    return course_response

@course_router.get(
    "/{course_id}/is_enrolled",
    status_code=status.HTTP_200_OK,
    summary="Check if current user is enrolled in a course",
    description="Returns `is_enrolled: true` if the authenticated user is enrolled, otherwise `false`."
)
async def is_user_enrolled(
    course_id: str,
    decoded_token: dict = Depends(is_logged_in),
    course_service: CourseService = Depends(get_course_service)
):
    user_id = str(decoded_token.get("id"))
    return course_service.is_user_enrolled(user_id, course_id)

# Analysis router
analysis_router = APIRouter(
    prefix="/analysis",
    tags=["course"]
)
@analysis_router.get(
    "/yearly",
    # response_model=YearAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get yearly course analysis",
    description="Retrieve yearly analysis of courses including revenue, enrollments, and course counts.",
    dependencies=[Depends(is_admin)]
)
async def get_yearly_analysis(
    year: int,
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve yearly analysis of courses including:
    - Total revenue generated
    - Total enrollments across all courses
    - Total number of courses created

    **Date Filtering**:
    - **year**: Filter by year (e.g., 2024)

    Only accessible to users with admin role.
    """
    
    return course_service.get_yearly_analysis(year) 

@analysis_router.get(
    "/instructor/courses",
    status_code=status.HTTP_200_OK,
    summary="Get instructor courses analytics",
    description="Retrieve analytics for courses assigned to the authenticated instructor.",
    dependencies=[Depends(is_admin_or_instructor)]
)
async def get_instructor_courses_analytics(
    params: DateFilterParams = Depends(),
    decoded_token: dict = Depends(is_admin_or_instructor),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve analytics for courses assigned to the authenticated instructor.

    This endpoint returns analytics data for courses taught by the current instructor including:
    - Course details (id, title, instructor info)
    - Total revenue (sum of successful payments)
    - Total enrollments count
    - View count and lessons count

    **Date Filtering** (based on course created_at):
    - **year**: Filter by year (e.g., 2024)
    - **month**: Filter by month (1-12)
    - **week**: Filter by week of year (1-53)
    - **day**: Filter by day of month (1-31)

    **Search & Filter**:
    - **search**: Search in course title or description
    - **filter**: Filter by course tags

    **Pagination**:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)

    Accessible to users with instructor or admin role.
    The instructor will only see analytics for their own courses.
    """
    instructor_id = decoded_token.get("id")

    return course_service.get_instructor_courses_analytics(
        instructor_id=str(instructor_id),
        year=params.year,
        month=params.month,
        week=params.week,
        day=params.day,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        filter=params.filter
    )


@analysis_router.get(
    "/instructor/{instructor_id}",
    # response_model=CourseListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get courses by instructor",
    description="Retrieve a list of courses taught by a specific instructor.",
    
)
async def get_courses_by_instructor(
    instructor_id: str,
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve a list of courses taught by a specific instructor.

    This endpoint returns all courses that are associated with the specified instructor.

    - **instructor_id**: UUID of the instructor whose courses to retrieve
    """
    return course_service.get_intructor_course(
        instructor_id,
    )


@analysis_router.get(
    "/courses",
    status_code=status.HTTP_200_OK,
    summary="Get all courses analytics (Admin only)",
    description="Retrieve analytics for all courses in the system with date filtering and pagination.",
    dependencies=[Depends(is_admin)]
)
async def get_all_courses_analytics(
    params: DateFilterParams = Depends(),
    course_service: CourseService = Depends(get_course_service),
    decoded_token: dict = Depends(is_admin)
):
    """
    Retrieve analytics for all courses in the system (Admin only).

    This endpoint returns analytics data for all courses including:
    - Course details (id, title, instructor info)
    - Total revenue (sum of successful payments)
    - Total enrollments count
    - View count and lessons count

    **Date Filtering** (based on course updated_at):
    - **year**: Filter by year (e.g., 2024)
    - **month**: Filter by month (1-12)
    - **week**: Filter by week of year (1-53)
    - **day**: Filter by day of month (1-31)

    **Search & Filter**:
    - **search**: Search in course title or description
    - **filter**: Filter by course tags

    **Pagination**:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)

    Only accessible to users with admin role.
    """
    return course_service.get_all_courses_analytics(
        year=params.year,
        month=params.month,
        week=params.week,
        day=params.day,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        filter=params.filter
    )

@analysis_router.get(
    "/{course_id}",
    # response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get course analysis",
    description="Retrieve analytics and statistics for a specific course with optional time filtering.",
    
)
async def get_courses_analysis(
    course_id: str,
    params: DateFilterParams = Depends(),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Retrieve analytics and statistics for a specific course with optional time filtering.

    This endpoint returns detailed analytics about a course, including enrollment statistics,
    completion rates, revenue data, and other metrics useful for instructors and administrators.

    **Date Filtering** (affects enrollment and payment calculations):
    - **year**: Filter by year (e.g., 2024)
    - **month**: Filter by month (1-12)
    - **week**: Filter by week of year (1-53)
    - **day**: Filter by day of month (1-31)

    - **course_id**: UUID of the course to analyze
    """
    return course_service.get_courses_analysis(
        course_id=course_id,
        year=params.year,
        month=params.month,
        week=params.week,
        day=params.day
    )
