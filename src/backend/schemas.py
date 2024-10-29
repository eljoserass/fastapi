from pydantic import BaseModel

class UserCreate(BaseModel):
    phone_number: str
    password: str

class UserLogin(BaseModel):
    phone_number: str
    password: str

class UserResponse(BaseModel):
    id: int
    phone_number: str

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    phone_number: str
    name: str = None

class ClientResponse(BaseModel):
    id: int
    phone_number: str
    name: str | None
    orders: list['OrderResponse'] = []  # This will reference the OrderResponse schema

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    status: str
    car_plate: str
    order_bullet_list: str
    client_id: int

class OrderResponse(BaseModel):
    id: int
    status: str
    car_plate: str
    order_bullet_list: str

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    status: str
    car_plate: str
    order_bullet_list: str
    client_id: int



