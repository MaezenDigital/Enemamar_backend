import requests  
from app.core.config.env import get_settings


setting = get_settings()
def send_otp_sms(phone_number: str):
    # Send OTP SMS
    # we use requests library for the samples
    # session object
    session = requests.Session()
    # base url
    base_url = 'https://api.afromessage.com/api/challenge'
    # api token
    token = setting.SMS_TOKEN
    # header
    headers = {'Authorization': 'Bearer ' + token}
    # request parameters
    callback = ""
    form_id = setting.SMS_ID
    sender = setting.SMS_SENDER_NAME
    to = phone_number
    pre = " Hello, your OTP is: " 
    post = " Thank you for using our service."
    sb = 1
    sa = 1
    ttl = setting.SMS_EXPIRATION_SECONDS  # expiration time in seconds
    len = 6
    t = 0
    # final url
    url = '%s?from=%s&sender=%s&to=%s&pr=%s&ps=%s&callback=%s&sb=%d&sa=%d&ttl=%d&len=%d&t=%d' % (base_url, form_id, sender, to, pre, post, callback, sb, sa, ttl, len, t)
    # make request
    try:
        result = session.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        # Handle the exception (e.g., log it, raise a custom error, etc.)
        print(f"Request failed: {e}")
        return (500, str(e))
    # check result
    status_code = 200
    if result.status_code == 200:
        # request is success. inspect the json object for the value of `acknowledge`
        json = result.json()
        if json['acknowledge'] != 'success':
            status_code = 400
    else:
        # anything other than 200 goes here.
        return (result.status_code, result.content)
    
    return (status_code, result.content)

def verify_otp_sms(phone_number: str, code: str):
    # session configuration
    session = requests.Session()
    # base url
    base_url = 'https://api.afromessage.com/api/verify'
    # api token
    token = setting.SMS_TOKEN
    # header
    headers = {'Authorization': 'Bearer ' + token}
    # request parameters
    # Note: You can also use the verification id sent in the challenge request. 
    # Use the `vc` query parameter to verify via verification id.
    to = phone_number
    code = code
    # final url
    url = '%s?to=%s&code=%s' % (base_url, to, code)
    # make request
    try:
        result = session.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        # Handle the exception (e.g., log it, raise a custom error, etc.)
        print(f"Request failed: {e}")
        return (500, str(e))
    # check result
    status_code = 200
    if result.status_code == 200:
        # request is success. inspect the json object for the value of `acknowledge`
        json = result.json()
        if json['acknowledge'] != 'success':
            status_code = 400
    else:
        # anything other than 200 goes here.
        return (result.status_code, result.content)
    
    return (status_code, result.content)
                                
def send_sms(phone_number: str, message: str):
    # session configuration
    session = requests.Session()
    # base url
    base_url = 'https://api.afromessage.com/api/send'
    # api token
    token = setting.SMS_TOKEN
    # header
    headers = {'Authorization': 'Bearer ' + token}
    # request parameters
    to = phone_number
    text = message
    from_id = setting.SMS_ID  # sender ID, can be empty
    sender = setting.SMS_SENDER_NAME  # sender name, can be empty
    # final url
    url = f"{base_url}?from={from_id}&send={sender}&to={to}&message={text}"
    # make request
    try:
        result = session.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        # Handle the exception (e.g., log it, raise a custom error, etc.)
        print(f"Request failed: {e}")
        return (500, str(e))
    
    return (result.status_code, result.content)

