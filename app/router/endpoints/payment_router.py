from re import S
from fastapi import APIRouter, Depends, HTTPException, Request
from app.domain.schema.courseSchema import (
    SearchParams,
    CallbackPayload,
    DateFilterParams
)
from app.service.payment_service import PaymentService, get_payment_service
from app.utils.middleware.dependancies import is_admin, is_logged_in
from uuid import UUID
import hmac
import hashlib
import json
from app.core.config.env import get_settings
from app.domain.schema.courseSchema import ChapaWebhookPayload


SETTINGS = get_settings()
# Public payment router
payment_router = APIRouter(
    prefix="/payment",
    tags=["payment"]
)

# Protected payment router (admin only)
protected_payment_router = APIRouter(
    prefix="/protected/payment",
    tags=["payment"],
    dependencies=[Depends(is_admin)]
)

@payment_router.post("/{course_id}/initiate")
async def initiate_payment(
    course_id: str,
    decoded_token: dict = Depends(is_logged_in),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Initiate a payment for a course.
    
    Args:
        course_id (str): The course ID.
        decoded_token (dict): The decoded JWT token.
        payment_service (PaymentService): The payment service.
        
    Returns:
        dict: The payment response.
    """
    user_id = decoded_token.get("id")
    user_id = UUID(user_id)
    course_id = UUID(course_id)
    
    return payment_service.initiate_payment(user_id, course_id)

@payment_router.post("/callback")
async def payment_callback(
    request: Request,    
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Process a payment callback.
    
    Args:
        callback (str): The callback reference.
        trx_ref (str): The transaction reference.
        status (str): The payment status.
        payment_service (PaymentService): The payment service.
        
    Returns:
        dict: The enrollment response.
    """
    try:
        # 1. Get the raw request body
        body = await request.body()
        
        # 2. Get the Chapa signature from the header
        signature = request.headers.get("Chapa-Signature") or request.headers.get("x-chapa-signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Chapa-Signature header missing")

        # 3. Verify the signature
        CHAPA_SECRET_KEY = SETTINGS.CHAPA_WEBHOOK_SECRET
        hasher = hmac.new(
            CHAPA_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha256
        )
        if hasher.hexdigest() != signature:
            raise HTTPException(status_code=403, detail="Invalid Chapa-Signature")

        # 4. Parse the JSON payload
        payload_data = json.loads(body)
        payload = ChapaWebhookPayload(**payload_data)

        # 5. Process the payment
        response = payment_service.process_payment_callback(payload)
        return response
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing payment callback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@protected_payment_router.get("/user/{user_id}")
async def get_user_payments(
    user_id: str,
    search_params: DateFilterParams = Depends(),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get all payments for a user.
    
    Args:
        user_id (str): The user ID.
        search_params (DateFilterParams): The search parameters.
        payment_service (PaymentService): The payment service.
        
    Returns:
        dict: The payments response.
    """
    return payment_service.get_user_payments(
        user_id, 
        search_params.page, 
        search_params.page_size, 
        search_params.filter,
        search_params.year,
        search_params.month,
        search_params.week,
        search_params.day
    )


