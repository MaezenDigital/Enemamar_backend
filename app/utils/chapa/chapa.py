import requests
from chapa import Chapa
from app.core.config.env import get_settings
import random
import string
settings = get_settings()
# Replace 'your_secret_key' with your actual Chapa secret key

def generete_tx_ref(length):
    #Generate a transaction reference
    tx_ref = string.ascii_lowercase
    return ''.join(random.choice(tx_ref) for i in range(length))

def pay_course(payment_data):
    print(payment_data.title)
    data = {
        # Required fields
        'phone_number': payment_data.phone_number,  # Use attribute-style access
        'amount': payment_data.amount,  # Use attribute-style access
        'first_name': payment_data.first_name,  # Use attribute-style access
        'last_name': payment_data.last_name,  # Use attribute-style access
        'tx_ref': payment_data.tx_ref,  # Use attribute-style access
        'email': settings.BASE_EMAIL,  # Use attribute-style access
        # Optional fields
        'callback_url': payment_data.callback_url,  # Use attribute-style access
        'return_url': payment_data.return_url,  # Use attribute-style access
        'customization': {
            'title': "Course Payment",  # Use attribute-style access
            'description': f'Payment for your course ',  # Use attribute-style access
        }
    }



    headers = {
        'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        'https://api.chapa.co/v1/transaction/initialize',
        json=data,
        headers=headers
    )
    
    return response.json()

def verify_payment(transaction_id):
    
	url = f"https://api.chapa.co/v1/transaction/verify/{transaction_id}"
	payload = ''
	headers = {
		'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
	}
	response = requests.get(url, headers=headers, data=payload)
	print("verification response",response)
	data = response.json()
	return data