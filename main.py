import os
import random
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client

app = FastAPI(title="KrishiSense Backend Engine")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated databases
# NOTE: In a serverless environment, these variables are volatile!
# They will reset whenever the serverless function "cold starts."
USER_DATABASE = {
    "admin": { "password": "admin", "name": "System Administrator" },
    "9876543210": { "password": "mumbai2026", "name": "Rajesh Kumar" }
}
OTP_REGISTRY = {}

class HandshakeRequest(BaseModel):
    username: str
    password: str
    fullName: str | None = None
    mode: str | None = None

class VerifyOTPRequest(BaseModel):
    username: str
    otp: str

@app.post("/api/auth/request-otp")
async def request_otp(data: HandshakeRequest):
    # Verify user existence
    if data.username not in USER_DATABASE or USER_DATABASE[data.username]["password"] != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    OTP_REGISTRY[data.username] = otp_code
    
    # Twilio Integration
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if account_sid and auth_token and twilio_number:
        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"Your KrishiSense Verification Code is: {otp_code}",
                from_=twilio_number,
                to=data.username if data.username.startswith("+") else f"+91{data.username}"
            )
            return {"status": "success", "message": "OTP sent via Twilio SMS."}
        except Exception:
            return {"status": "sandbox", "message": "Twilio failed. Sandbox bypass active.", "otp": otp_code}
    
    return {"status": "sandbox", "message": "Running in Sandbox Mode.", "otp": otp_code}

@app.post("/api/auth/verify-otp")
async def verify_otp(data: VerifyOTPRequest):
    # Validate OTP
    if data.username in OTP_REGISTRY and OTP_REGISTRY[data.username] == data.otp:
        del OTP_REGISTRY[data.username] 
        return {
            "status": "success", 
            "message": "2FA Authentication Verified.", 
            "user": USER_DATABASE[data.username]
        }
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP code."
    )
