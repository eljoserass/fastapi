import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey  # Import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship  # Import relationship

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv("MYSQL_URL")
print (DATABASE_URL)
# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Define your models here

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
