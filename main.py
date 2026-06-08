import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize the FastAPI app
app = FastAPI()

# Enable CORS so your frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data structure for the login request
class LoginRequest(BaseModel):
    username: str
    password: str

# Login Endpoint
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Verify credentials
    # In a real app, replace this with a database check
    if request.username == "9876543210" and request.password == "mumbai2026":
        return {"status": "success", "message": "Authenticated"}
    
    # Return 401 if credentials don't match
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Root path check
@app.get("/")
def read_root():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
