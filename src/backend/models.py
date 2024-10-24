from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True)  # Specify length for phone_number
    password = Column(String(255))  # Specify length for password
    clients = relationship("Client", back_populates="owner")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True)  # Specify length for phone_number
    name = Column(String(50), nullable=True)  # Specify length for name
    user_id = Column(Integer, ForeignKey("users.id"))
    orders = relationship("Order", back_populates="client")
    owner = relationship("User", back_populates="clients")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50))  # Specify length for status
    car_plate = Column(String(20))  # Specify length for car_plate
    order_bullet_list = Column(String(255))  # Specify length for order_bullet_list
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="orders")
