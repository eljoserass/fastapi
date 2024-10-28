from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(25), unique=True, index=True)  # Specify length for phone_number
    password = Column(String(255))  # Specify length for password
    clients = relationship("Client", back_populates="owner")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(25))  # Specify length for phone_number
    name = Column(String(50), nullable=True)  # Specify length for name
    user_id = Column(Integer, ForeignKey("users.id"))
    orders = relationship("Order", back_populates="client")
    owner = relationship("User", back_populates="clients")  # Relationship to User
    messages = relationship("Message", back_populates="client")  # Relationship to Message

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50))  # Specify length for status
    car_plate = Column(String(20))  # Specify length for car_plate
    order_bullet_list = Column(String(255))  # Specify length for order_bullet_list
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="orders")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)  # Unique identifier for each message
    content = Column(String(255))  # Store the message content (up to 255 characters)
    media_urls = Column(String(255), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"))  # Foreign key to link to the Client model
    client = relationship("Client", back_populates="messages")  # Relationship to Client
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp for when the message was created