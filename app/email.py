from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from jose import jwt
from datetime import datetime, timedelta
from typing import Dict

# You should store these in environment variables
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USERNAME = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_FROM = "your-email@gmail.com"

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USERNAME,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_FROM,
    MAIL_PORT=EMAIL_PORT,
    MAIL_SERVER=EMAIL_HOST,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
)

SECRET_KEY = "your-secret-key"  # You should store this in an environment variable
ALGORITHM = "HS256"

def create_email_verification_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def send_email_verification(email: EmailStr, token: str):
    verification_url = f"http://localhost:8000/verify-email?token={token}"
    
    html = f"""
    <p>Please click the link below to verify your email address:</p>
    <p><a href="{verification_url}">{verification_url}</a></p>
    """

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=html,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

def verify_email_token(token: str) -> Dict[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise ValueError("Invalid token")
        return {"email": email}
    except jwt.JWTError:
        raise ValueError("Invalid token")
