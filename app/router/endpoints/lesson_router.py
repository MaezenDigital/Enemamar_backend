from fastapi import APIRouter, Depends, status
from app.domain.schema.courseSchema import (
    PaginationParams,
    MultipleLessonInput,
    VideoInput,
)
from app.domain.schema.responseSchema import (
    LessonListResponse, LessonDetailResponse, BaseResponse,
    ErrorResponse
)
from app.service.lesson_service import LessonService, get_lesson_service
from app.utils.middleware.dependancies import is_admin, is_logged_in
from typing import Dict, Any, List

# Public lesson router
lesson_router = APIRouter(
    prefix="/lesson",
    tags=["lesson"]
)

# Protected lesson router (admin only)
protected_lesson_router = APIRouter(
    prefix="/protected/lesson",
    tags=["lesson"],
    dependencies=[Depends(is_admin)]
)

@lesson_router.get(
    "/{course_id}",
    # response_model=LessonListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all lessons for a course",
    description="Retrieve a paginated list of all lessons for a specific course with generated video URLs.",
    # responses={
    #     200: {
    #         "description": "Lessons retrieved successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Lessons fetched successfully",
    #                     "data": [
    #                         {
    #                             "id": "8d854347-ba90-422d-901e-2752ba47a6f1",
    #                             "title": "Introduction to Python",
    #                             "description": "Learn the basics of Python programming",
    #                             "duration": 30,
    #                             "video_url": "https://iframe.mediadelivery.net/embed/393657/3e52de58-dc2b-4269-a0f5-f181f004964a?token=37430fd202c1738a588a156ae76278c4fd88ece01bea21cc47f2abf83e88ead5&expires=1746350479",
    #                             "order": 1,
    #                             "created_at": "2025-05-04T10:57:36.144121+03:00",
    #                             "updated_at": None
    #                         },
    #                         {
    #                             "id": "9e965458-cb91-533e-b12f-3863ba58b7g2",
    #                             "title": "Python Data Types",
    #                             "description": "Learn about Python data types and structures",
    #                             "duration": 45,
    #                             "video_url": "https://iframe.mediadelivery.net/embed/393657/4f63ef69-ed3c-5370-b1g6-g292g115075b?token=48541ge313d2849b699b267bf87389d5ge99fdf12cfb32dd58g3bcg94f99fbe6&expires=1746350479",
    #                             "order": 2,
    #                             "created_at": "2025-05-04T11:30:22.144121+03:00",
    #                             "updated_at": None
    #                         }
    #                     ],
    #                     "pagination": {
    #                         "total": 10,
    #                         "page": 1,
    #                         "page_size": 10,
    #                         "total_pages": 1
    #                     }
    #                 }
    #             }
    #         }
    #     },
    #     401: {
    #         "description": "Unauthorized",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Missing or invalid token"}
    #             }
    #         }
    #     },
    #     403: {
    #         "description": "Forbidden",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Not enrolled in this course"}
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Course not found"}
    #             }
    #         }
    #     }
    # }
)
async def get_lessons(
    course_id: str,
    decoded_token: dict = Depends(is_logged_in),
    search_params: PaginationParams = Depends(),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Retrieve a paginated list of all lessons for a specific course.

    This endpoint returns all lessons associated with the specified course,
    with pagination support. The user must be enrolled in the course to access its lessons.

    - **course_id**: UUID of the course whose lessons to retrieve
    - **page**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 10, max: 100)

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = decoded_token.get("id")
    return lesson_service.get_lessons(
        course_id,
        user_id,
        search_params.page,
        search_params.page_size
    )

@lesson_router.get(
    "/{course_id}/{lesson_id}",
    # response_model=LessonDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get lesson by ID",
    description="Retrieve detailed information about a specific lesson with generated video URL.",
    
)
async def get_lesson_by_id(
    course_id: str,
    lesson_id: str,
    decoded_token: dict = Depends(is_logged_in),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Retrieve detailed information about a specific lesson.

    This endpoint returns comprehensive details about a lesson, including its content,
    video URL (if available), and other metadata. The user must be enrolled in the course
    to access its lessons.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson to retrieve

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = decoded_token.get("id")
    return lesson_service.get_lesson_by_id(course_id, lesson_id, user_id)

@lesson_router.get(
    "/{course_id}/{lesson_id}/first",
    # response_model=LessonDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get lesson by ID",
    description="Retrieve detailed information about a first oreder lesson with generated video URL.",
    
)
async def get_lesson_by_id(
    course_id: str,
    lesson_id: str,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Retrieve detailed information about a specific lesson.

    This endpoint returns comprehensive details about a lesson, including its content,
    video URL (if available), and other metadata. The user must be enrolled in the course
    to access its lessons.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson to retrieve

    Authentication is required via JWT token in the Authorization header.
    """
    user_id = ""
    return lesson_service.get_lesson_by_id(course_id, lesson_id, user_id)

@protected_lesson_router.delete(
    "/videos/{video_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a video",
    description="Delete a video from a lesson.",
    # responses={
    #     200: {
    #         "description": "Video deleted successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Video deleted successfully"
    #                 }
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Video not found"}
    #             }
    #         }
    #     }
    # }
)
async def delete_video(
    video_id: str,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Delete a video from a lesson.

    This endpoint permanently removes a video from a lesson.
    This operation cannot be undone.

    - **video_id**: UUID of the video to delete
    """
    return lesson_service.delete_video(video_id)

@protected_lesson_router.put(
    "/videos/{video_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a video",
    description="Update a video's metadata.",
    # responses={
    #     200: {
    #         "description": "Video updated successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Video updated successfully"
    #                 }
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Video not found"}
    #             }
    #         }
    #     }
    # }
)
async def update_video(
    video_id: str,
    video_input: VideoInput,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Update a video's metadata.

    This endpoint updates a video's metadata such as video_id, library_id, and secret_key.

    - **video_id**: UUID of the video to update
    - **video_input**: New video metadata
    """
    return lesson_service.edit_video(video_id, video_input)

@protected_lesson_router.get(
    "/videos/{video_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a video",
    description="Get a video by its ID.",
    # responses={
    #     200: {
    #         "description": "Video fetched successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Video fetched successfully",
    #                     "data": {
    #                         "id": "123e4567-e89b-12d3-a456-426614174000",
    #                         "video_id": "abc123",
    #                         "library_id": "lib123",
    #                         "secret_key": "encrypted-secret-key",
    #                         "video_url": "https://iframe.mediadelivery.net/embed/lib123/abc123?token=..."
    #                     }
    #                 }
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Video not found"}
    #             }
    #         }
    #     }
    # }
)
async def get_video(
    video_id: str,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Get a video by its ID.

    This endpoint retrieves a video by its ID, including its metadata and a generated secure URL.

    - **video_id**: UUID of the video to retrieve
    """
    return lesson_service.get_video_by_id(video_id)



@protected_lesson_router.post(
    "/{course_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add multiple lessons to a course",
    description="Create multiple lessons for a course, optionally with video information.",
    # responses={
    #     201: {
    #         "description": "Lessons created successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Lessons added successfully",
    #                     "data": [
    #                         {
    #                             "id": "8d854347-ba90-422d-901e-2752ba47a6f1",
    #                             "title": "Introduction to Python",
    #                             "description": "Learn the basics of Python programming",
    #                             "duration": 30,
    #                             "video_url": None,
    #                             "order": 1,
    #                             "created_at": "2025-05-04T10:57:36.144121+03:00",
    #                             "updated_at": None
    #                         },
    #                         {
    #                             "id": "9e965458-cb91-533e-b12f-3863ba58b7g2",
    #                             "title": "Python Data Types",
    #                             "description": "Learn about Python data types and structures",
    #                             "duration": 45,
    #                             "video_url": None,
    #                             "order": 2,
    #                             "created_at": "2025-05-04T11:30:22.144121+03:00",
    #                             "updated_at": None
    #                         }
    #                     ]
    #                 }
    #             }
    #         }
    #     },
    #     400: {
    #         "description": "Bad request",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Failed to add lesson, invalid data"}
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Course not found"}
    #             }
    #         }
    #     }
    # }
)
async def add_multiple_lessons(
    course_id: str,
    lessons_input: MultipleLessonInput,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Add multiple lessons to a course at once.

    This endpoint allows creating multiple lessons for a course in a single request.
    Each lesson can optionally include video information, which will be stored in the
    video table and linked to the lesson. The video URL is not stored directly but
    will be generated when the lesson is retrieved.

    - **course_id**: UUID of the course to add lessons to
    - **lessons_input**: Object containing an array of lesson objects:
      - **title**: The lesson title
      - **description**: The lesson description
      - **duration**: The lesson duration in minutes
      - **order**: The lesson order in the course (optional)
      - **video**: Optional video metadata object:
        - **video_id**: The video ID from the video hosting service
        - **library_id**: The library ID from the video hosting service
        - **secret_key**: The secret key for generating secure URLs

    If video information is provided, the secret key will be encrypted before storage.
    """
    return lesson_service.add_multiple_lessons(course_id, lessons_input)

@protected_lesson_router.post(
    "/{course_id}/{lesson_id}/video",
    # response_model=BaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add video to lesson",
    description="Add video information to a lesson for generating secure video URLs.",
    # responses={
    #     201: {
    #         "description": "Video added successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Video added successfully",
    #                     "data": {
    #                         "id": "123e4567-e89b-12d3-a456-426614174000",
    #                         "video_id": "abc123",
    #                         "library_id": "lib123",
    #                         "secret_key": "encrypted-secret-key",
    #                         "created_at": "2023-01-01T12:00:00Z",
    #                         "updated_at": "2023-01-01T12:00:00Z"
    #                     }
    #                 }
    #             }
    #         }
    #     },
    #     400: {
    #         "description": "Bad request",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Failed to add video, video already exists"}
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Lesson not found"}
    #             }
    #         }
    #     }
    # }
)
async def add_video_to_lesson(
    course_id: str,
    lesson_id: str,
    video_input: VideoInput,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Add video information to a lesson for generating secure video URLs.

    This endpoint stores the video metadata (video_id, library_id, secret_key) that will be used
    to generate secure video URLs when the lesson is retrieved. The actual video URL is not stored
    but generated dynamically when the lesson is accessed.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson to add the video to
    - **video_input**: Object containing video metadata:
      - **video_id**: The video ID from the video hosting service
      - **library_id**: The library ID from the video hosting service
      - **secret_key**: The secret key for generating secure URLs

    The secret key will be encrypted before storage for security.
    """
    return lesson_service.add_video_to_lesson(course_id, lesson_id, video_input)

@protected_lesson_router.get(
    "/{course_id}/{lesson_id}/video",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get video metadata for a lesson",
    description="Retrieve the video metadata associated with a lesson (not the generated URL).",
    # responses={
    #     200: {
    #         "description": "Video metadata retrieved successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Video fetched successfully",
    #                     "data": {
    #                         "id": "0b98bfd7-2460-4e08-a37c-725e14c497bb",
    #                         "video_id": "3e52de58-dc2b-4269-a0f5-f181f004964a",
    #                         "library_id": "393657",
    #                         "secret_key": "gAAAAABoFx3wyLT5UwPjdYwbe_HJY4T0MmPzyq-BDPvkdoH-rZi1JlYvuN3fQH2sRFhH06tJaeyZUplI1hefW-VWmrcobjBUouW8B6njxpiN7WP4_2P5Q90BLeI5_mYt3OnF6WnPATO2",
    #                         "created_at": "2025-05-04T10:57:36.152502+03:00",
    #                         "updated_at": "2025-05-04T10:57:36.152502+03:00"
    #                     }
    #                 }
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "No video found for this lesson"}
    #             }
    #         }
    #     }
    # }
)
async def get_lesson_video(
    course_id: str,
    lesson_id: str,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Retrieve the video metadata associated with a lesson.

    This endpoint returns the raw video metadata stored in the database, not the generated
    video URL. The metadata includes the video_id, library_id, and encrypted secret_key
    that are used to generate the secure video URL when a lesson is accessed.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson whose video metadata to retrieve

    Note: This endpoint is for administrative purposes. To get a lesson with its
    generated video URL, use the regular lesson retrieval endpoint.
    """
    return lesson_service.get_lesson_video(lesson_id)

@protected_lesson_router.put(
    "/{course_id}/{lesson_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a lesson",
    description="Update a lesson's information (does not affect video metadata).",
    # responses={
    #     200: {
    #         "description": "Lesson updated successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Lesson updated successfully",
    #                     "data": {
    #                         "id": "8d854347-ba90-422d-901e-2752ba47a6f1",
    #                         "title": "Updated Python Introduction",
    #                         "description": "Updated description for Python basics",
    #                         "duration": 35,
    #                         "order": 1,
    #                         "created_at": "2025-05-04T10:57:36.144121+03:00",
    #                         "updated_at": "2025-05-05T09:12:45.123456+03:00"
    #                     }
    #                 }
    #             }
    #         }
    #     },
    #     400: {
    #         "description": "Bad request",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Invalid lesson data"}
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Lesson not found"}
    #             }
    #         }
    #     }
    # }
)
async def edit_lesson(
    course_id: str,
    lesson_id: str,
    lesson_data: dict,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Update a lesson's information.

    This endpoint allows updating a lesson's basic information such as title, description,
    duration, and order. It does not modify the associated video metadata - use the
    dedicated video endpoints for that purpose.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson to update
    - **lesson_data**: Object containing the fields to update:
      - **title**: The lesson title (optional)
      - **description**: The lesson description (optional)
      - **duration**: The lesson duration in minutes (optional)
      - **order**: The lesson order in the course (optional)

    Only the fields included in the request will be updated.
    """
    return lesson_service.edit_lesson(course_id, lesson_id, lesson_data)

@protected_lesson_router.delete(
    "/{course_id}/{lesson_id}",
    # response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a lesson",
    description="Delete a lesson and its associated video metadata.",
    # responses={
    #     200: {
    #         "description": "Lesson deleted successfully",
    #         "content": {
    #             "application/json": {
    #                 "example": {
    #                     "detail": "Lesson deleted successfully"
    #                 }
    #             }
    #         }
    #     },
    #     404: {
    #         "description": "Not found",
    #         "content": {
    #             "application/json": {
    #                 "example": {"detail": "Lesson not found"}
    #             }
    #         }
    #     }
    # }
)
async def delete_lesson(
    course_id: str,
    lesson_id: str,
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Delete a lesson and its associated video metadata.

    This endpoint permanently removes a lesson from a course, including any
    associated video metadata. This operation cannot be undone.

    - **course_id**: UUID of the course containing the lesson
    - **lesson_id**: UUID of the lesson to delete

    Note: This will also delete any video metadata associated with the lesson.
    """
    return lesson_service.delete_lesson(course_id, lesson_id)

