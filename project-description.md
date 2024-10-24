
The project will be a fastapi server connected to a mysql database. connected in railway. it will help customer facing employees handle orders 

It will be a server that users can register and login, then they will give acccess to their whattsapp and connect our webhook to receive their messages, an llm will read the messages and identify which messages are from orders, when an order is identify it will create a client, this client can have many orders. the information about the order is identifying the plate and what the user is asking about that car, and a status to konw if the user has been given the quota or not.

a scketch of the database will be

User
- phone number
- password
- clients

Client
- phone number
- amount of orders
- name (optional)
- orders

Order
- satus
- car plate
- order bullet list


Users can have one phone number, one password, many clients

Clients  can have one phone number, whole number of orders, name optional, many orders

Orders can have one status, one car plate, one bullet point list (this is just a string)

Users can create, login, update and delete their info. Clients can be created and updated. Orders can be created and deleted.
