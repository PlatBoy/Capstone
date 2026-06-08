import os
import random
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client

app = FastAPI(title="KrishiSense Backend Engine")

# Enable CORS so your frontend can communicate with this API seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated databases (Resets when server restarts or scales down)
USER_DATABASE = { 
    "admin": { "password": "admin", "name": "System Administrator" },
    "9876543210": { "password": "mumbai2026", "name": "Rajesh Kumar" }
}
OTP_REGISTRY = {}

class HandshakeRequest(BaseModel):
    username: str
    password: str
    fullName: str = None
    mode: str  # 'login' or 'register'

class VerificationRequest(BaseModel):
    username: str
    otp: str

@app.get("/")
def read_root():
    return {"status": "KrishiSense API is live and running!"}

@app.post("/api/auth/request-otp")
async def request_otp(payload: HandshakeRequest):
    username = payload.username.strip()
    password = payload.password
    
    if payload.mode == "login":
        if username not in USER_DATABASE or USER_DATABASE[username]["password"] != password:
            raise HTTPException(status_code=401, detail="Invalid identity credentials.")
    else:
        if username in USER_DATABASE:
            raise HTTPException(status_code=400, detail="Mobile account profile already exists.")
        USER_DATABASE[username] = { "password": password, "name": payload.fullName or "Farmer Plot" }

    # Generate a secure random 6-digit verification code
    secure_otp = str(random.randint(100000, 999999))
    OTP_REGISTRY[username] = secure_otp

    # Automatically fetch keys from Vercel's Environment Variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    sender_number = os.environ.get("TWILIO_PHONE_NUMBER")

    if username != "admin" and username.isdigit():
        # Check if Twilio is configured on Vercel
        if account_sid and auth_token and sender_number:
            try:
                client = Client(account_sid, auth_token)
                # Adds country code prefix for India (+91) if not explicitly typed
                formatted_phone = f"+91{username}" if not username.startswith("+") else username
                
                client.messages.create(
                    body=f"[KrishiSense Security] Your 2FA Key is: {secure_otp}. Valid for single use.",
                    from_=sender_number,
                    to=formatted_phone
                )
                return {"status": "dispatched", "message": "Real text message routed to mobile device."}
            except Exception as err:
                raise HTTPException(status_code=500, detail=f"Twilio deployment gateway error: {str(err)}")
        else:
            # 💡 SANDBOX FALLBACK: If your Twilio keys aren't set up yet, this lets you keep testing!
            return {
                "status": "dispatched", 
                "message": f"[DEV SANDBOX] Twilio credentials missing. Your generated OTP code is: {secure_otp}"
            }

    return {"status": "dispatched", "message": "Root admin session token initialized."}

@app.post("/api/auth/verify-otp")
async def verify_otp(payload: VerificationRequest):
    username = payload.username.strip()
    submitted_otp = payload.otp.strip()

    if username in OTP_REGISTRY and OTP_REGISTRY[username] == submitted_otp:
        # Delete token instantly upon successful validation to prevent replay attacks
        del OTP_REGISTRY[username]
        return {
            "status": "authenticated",
            "profile": username,
            "name": USER_DATABASE[username]["name"]
        }
    
    raise HTTPException(status_code=400, detail="Security token mismatch or expired lifetime.")
