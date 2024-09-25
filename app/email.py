import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, SecretStr
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# Load configuration from environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS"))

if not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM, SECRET_KEY]):
    raise ValueError("Missing required environment variables")

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USERNAME,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_FROM,
    MAIL_PORT=EMAIL_PORT,
    MAIL_SERVER=EMAIL_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

print(f"Email configuration: FROM={EMAIL_FROM}, HOST={EMAIL_HOST}, PORT={EMAIL_PORT}, USERNAME={EMAIL_USERNAME}")

def create_email_verification_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": email}
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError:
        raise HTTPException(status_code=500, detail="Could not create verification token")

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
    try:
        print(f"Attempting to send email to {email} from {EMAIL_FROM}")
        await fm.send_message(message)
        print(f"Email sent successfully to {email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def verify_email_token(token: str) -> Dict[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise ValueError("Invalid token")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
