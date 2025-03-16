import sys
#from utils.chat_loader import ChatWhatsapp, Message
from src.backend.models import Message
from openai import OpenAI
from pydantic import BaseModel


SYSTEM = """Eres un asistente de recambista en España. Tu labor sera leer las conversaciones con clientes en Whatsapp y simplificar su entendimiento al recambista
Para hacer esto, leeras la conversacion entre Toni (el mecanico pidiendo recambios) y Guillem (el recambista). El usuario te enviara la conversacion.
De esta conversacion tienes que:
- identificar las distintas ordenes de Toni
- una vez identificada extraer la informacion que Toni quiere saber sobre ese pedido
- la informacion se puede contener en forma de imagenes.
- por cada pedido indetifica modelo, marca, placa del vehiculo y lo que toni esta pidiendo sobre este."""

SYSTEM_PRO = """You will receive messages in spanish. This messages are from a mechanic, making an order.
Parse the message into the order. In some cases you will receive messages that all refer to the same order, and in others, it can be multiple orders.
An order can be only about one car, so each order can only have one car plate.
The messages might contain images that are used to give information about the car plate or about the car part that is being order. Reference the image used for your answer.
Answer always in spanish.
You will receive multiple messages, so remember that you might need to parse the messages into multiple orders
"""

SYSTEM_DEFAULT = "You are an expert at structured data extraction. You will be given unstructured text from a chat with a mechanic asking for quotas on car parts and should convert it into the given structure."

def encode_image(image_path):
  import base64
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

OpenAIclient = OpenAI()



async def message_to_orders(messages: list[Message]):

    # TODO get rid of this in here
    class Order(BaseModel):
        car_plate: str
        car_brand: str
        car_model: str
        order_requirements: list[str]
        reference_media_files: list[str]

    class Orders(BaseModel):
        orders: list[Order]

    gpt_messages = [{"role": "system", "content": SYSTEM_DEFAULT}]

    user_message = {"role": "user", "content": []}
    for message in messages:
        print (str(message))
        if message.media_urls == None:
            user_message["content"].append({"type": "text", "text": f"Mensaje del mecánico: {message.content}"})
        else:
           image = encode_image(message.media_urls)
           user_message["content"].extend([
              {"type":  "text", "text": f"Mensaje del mecánico: {message.content} {message.media_urls} (archivo adjunto)"},
              {"type": "image_url",  "image_url": { "url":  f"data:image/jpeg;base64,{image}", "detail": "high"}}
           ]
           )
    # TODO maybe change to put the image url instead of passing the base64?
    gpt_messages.append(user_message)
    print ("GPT MESSAGES")
    print (gpt_messages)
    completion = OpenAIclient.beta.chat.completions.parse(model="gpt-4o", messages=gpt_messages, response_format=Orders)
    return completion


async def call_llm(messages: list[Message]): # -> list[Order] 

    completion = await message_to_orders(messages)
    if hasattr(completion, 'choices') and len(completion.choices) > 0:
        # Check the structure of the first choice
        first_choice = completion.choices[0]
        # Access the orders from the parsed attribute of the message
        if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'parsed'):
            orders = first_choice.message.parsed.orders
            print (orders)
            return orders
        else:
            print("No orders found in the first choice's message.")
    else:
        print("No choices found in the completion response.")
    return None
