from fastapi import APIRouter, Depends, Request,HTTPException, status
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

# Load settings
settings = get_settings()
CHAPA_WEBHOOK_SECRET = settings.CHAPA_WEBHOOK_SECRET

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


@payment_router.get("/callback")
async def payment_callback(
    # callback: str,
    ref_id: str,
    trx_ref: str,
    status: str,
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
    # print(f"Callback: {callback}")
    payload = CallbackPayload(trx_ref=trx_ref, status=status, reference=ref_id) 
    return payment_service.process_payment_callback(payload)



@payment_router.post("/webhook")
async def payment_callback(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Process and verify a Chapa payment callback.
    """
    # 1. Get the signature from the headers. Prioritize 'x-chapa-signature'.
    chapa_signature = request.headers.get("x-chapa-signature")
    if not chapa_signature:
        chapa_signature = request.headers.get("Chapa-Signature")

    if not chapa_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook signature header not found."
        )

    # 2. Get the raw body and parse it into a dictionary
    raw_body = await request.body()
    try:
        payload_dict = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body."
        )

    # 3. --- THIS IS THE CRITICAL FIX ---
    # Re-serialize the parsed dictionary to a compact JSON string.
    # The `separators` argument removes whitespace, creating a deterministic string.
    # Then, encode it to bytes for HMAC.
    payload_to_hash = json.dumps(payload_dict, separators=(",", ":")).encode('utf-8')

    # 4. Generate the local signature using the re-serialized payload
    local_signature = hmac.new(
        CHAPA_WEBHOOK_SECRET.encode('utf-8'),
        payload_to_hash, # Use the new, correct payload
        hashlib.sha256
    ).hexdigest()

    # 5. Securely compare the signatures
    if not hmac.compare_digest(local_signature, chapa_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature."
        )

    # --- Signature is valid, proceed with your business logic ---
    
    trx_ref = payload_dict.get("trx_ref")
    payment_status = payload_dict.get("status") # Renamed to avoid conflict with `status` module
    reference = payload_dict.get("reference")

    payload = CallbackPayload(trx_ref=trx_ref, status=payment_status, reference=reference) 
    
    return payment_service.process_payment_callback(payload)

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


