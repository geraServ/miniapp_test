import hashlib
import hmac
import os
from urllib.parse import parse_qsl
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def validate_init_data(init_data: str) -> bool:
    """
    Validate Telegram WebApp initData
    Based on: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        hash_str = parsed_data.pop('hash')
        
        data_check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(parsed_data.items()))
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == hash_str
    except:
        return False

def extract_user_data(init_data: str) -> dict:
    """Extract user data from initData"""
    parsed_data = dict(parse_qsl(init_data))
    user_data = {
        'telegram_id': int(parsed_data.get('user[id]')),
        'first_name': parsed_data.get('user[first_name]', ''),
        'last_name': parsed_data.get('user[last_name]', ''),
        'username': parsed_data.get('user[username]', ''),
    }
    return user_data