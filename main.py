import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from src.backend.database import SessionLocal, engine, Base
from src.backend.schemas import UserCreate, UserLogin
from passlib.context import CryptContext

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv("MYSQL_URL")

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    from src.backend.models import User
    # Check if the user already exists
    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Create a new user
    new_user = User(phone_number=user.phone_number, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    from src.backend.models import User
    # Retrieve the user by phone number
    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid phone number or password")

    # Verify the password
    if not pwd_context.verify(user.password, existing_user.password):
        raise HTTPException(status_code=400, detail="Invalid phone number or password")

    return {"message": "Login successful", "user_id": existing_user.id}

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
