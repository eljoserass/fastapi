import os
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # Add this import at the top of your file
from src.backend.database import SessionLocal, engine, Base
from src.backend.schemas import UserCreate, UserLogin, ClientCreate, OrderCreate
from src.backend.models import User, Client, Order, Message
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, Field
#from twilio.rest import Client as TwilioClient
import requests
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from twilio.twiml.messaging_response import MessagingResponse
from language import call_llm


# TODO do this correctly
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
#twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create the database tables

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create JWT token
def create_access_token(data: dict, expires_delta=None):
    from datetime import datetime, timedelta

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoint to register a user
@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    new_user = User(phone_number=user.phone_number, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

# Endpoint to login and get JWT token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint to get clients of the logged-in user
@app.get("/clients")
async def get_clients(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise credentials_exception
    return user.clients

# Endpoint to get orders of a specific client
@app.get("/clients/{client_id}/orders")
async def get_orders(client_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise credentials_exception
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.orders


class WhatsAppMessage(BaseModel):
    From: str = Field(..., description="The sender's phone number")
    Body: str = Field("", description="The message body")  # Optional for media-only messages
    NumMedia: int = Field(0, description="Number of media files attached")

# Dependency to parse form data into the Pydantic model
async def whatsapp_message(
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0)
) -> WhatsAppMessage:
    return WhatsAppMessage(From=From, Body=Body, NumMedia=NumMedia)

@app.post("/whatsapp/{user_id}")
async def whatsapp_webhook(user_id: int, request: Request, message: WhatsAppMessage = Depends(whatsapp_message), db: Session = Depends(get_db)):
    """
    Webhook endpoint to handle incoming WhatsApp messages, including media.
    """
    # Gather media URLs if available
    form_data = await request.form()

    # Gather media URLs if available and download them
    media_urls = []
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    phone_number = message.From.replace("whatsapp:", "")
    
    # TODO IMPORTANT THIS ONLY WORKS WITH ONE USER
    client = db.query(Client).filter(Client.phone_number == phone_number, Client.user_id == user_id).first()
    if not client:
        client = Client(phone_number=phone_number, user_id=user_id)
        db.add(client)
        try:
            db.commit()  # Attempt to commit the new client
            db.refresh(client)
        except IntegrityError:
            db.rollback()  # Rollback if there's an integrity error
            client = db.query(Client).filter(Client.phone_number == phone_number, Client.user_id == user_id).first()  # Fetch the existing client
        else:
            db.refresh(client)  # Refresh the client if successfully added

    # Store the message
    sanitized_content = message.Body.replace('\xa0', ' ')  # Replace non-breaking spaces with regular spaces

    for i in range(message.NumMedia):
        media_url = form_data.get(f"MediaUrl{i}")
        if media_url:
            media_response = requests.get(media_url, auth=(TWILIO_SID, TWILIO_AUTH))
            if media_response.status_code == 200:
                # Determine the file extension based on media type
                content_type = media_response.headers.get("Content-Type")
                extension = content_type.split('/')[-1] if content_type else 'bin'  # Default to binary if type is unknown

                filename = f"media/{user_id}/{client.id}/FILE-{current_time}.{extension}"
                
                directory = os.path.dirname(filename)

                # Check if the directory exists, create if it doesn't
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    print(f'Created directory: {directory}')

                with open(filename, "wb") as f:
                    f.write(media_response.content)
                print(f"Media downloaded and saved as {filename}")

            media_urls.append(filename)


    # Convert media URLs list to a comma-separated string for storage
    media_urls_str = ",".join(media_urls) if media_urls else None

    new_message = Message(content=sanitized_content, media_urls=media_urls_str, client_id=client.id)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    all_messages = db.query(Message).filter(Message.client_id == client.id).order_by(Message.id.asc()).all()

    orders = await call_llm(all_messages)
    
    # TODO change that if the order exists, but the list of requirements is different (the stuff changed, or is longer or smth) update it
    for order_data in orders:  # Assuming llm_response returns a list of orders
        existing_order = db.query(Order).filter(Order.car_plate == order_data.car_plate, Order.client_id == client.id).first()
        if existing_order:
                # Update the existing order with new information
            print (f"this order exists {order_data}")
            existing_order.status = "Esperando precio"  # Update status or any other fields as needed
            existing_order.car_brand = order_data.car_brand
            existing_order.car_model = order_data.car_model
            existing_order.order_requirements = order_data.order_requirements  # Assuming order_details is a dict
            existing_order.reference_media_files = order_data.reference_media_files  # Update media files if necessary
        else:
            # Create a new order if it doesn't exist
            print(f"this order is new {order_data}")
            new_order = Order(
                status="Esperando precio",
                car_plate=order_data.car_plate,
                car_brand=order_data.car_brand,
                car_model=order_data.car_model,
                order_requirements=order_data.order_requirements,  # Assuming order_details is a dict
                reference_media_files=order_data.reference_media_files,
                client_id=client.id
            )
            db.add(new_order)

    # Commit the changes to the database
    db.commit()
    # Create a response message
    response = MessagingResponse()
    response.message("Message and any media received!")

    # Return the XML response required by Twilio
    return str(response)

@app.get("/media/{user_id}/{client_id}/{file_name}")
async def get_media(user_id: str, client_id: str, file_name: str):
    file_path = f"./media/{user_id}/{client_id}/{file_name}"
    
    if os.path.exists(file_path):
        
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/media")
async def delete_media():
    media_directory = "./media"

    if os.path.exists(media_directory):
        for root, dirs, files in os.walk(media_directory, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        return {"detail": "All media files have been deleted."}
    else:
        raise HTTPException(status_code=404, detail="Media directory not found")


@app.delete("/messages")
async def delete_all_messages(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise credentials_exception

    # Delete all messages for the current user
    db.query(Message).filter(Message.client.has(user_id=user.id)).delete(synchronize_session=False)
    db.commit()

    return {"detail": "All messages have been deleted for the current user."}


@app.delete("/orders")
async def delete_all_orders(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise credentials_exception

    # Delete all orders for the current user's clients
    db.query(Order).filter(Order.client.has(user_id=user.id)).delete(synchronize_session=False)
    db.commit()

    return {"detail": "All orders have been deleted for the current user."}


@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}