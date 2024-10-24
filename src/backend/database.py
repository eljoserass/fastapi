import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

MYSQL_USER = os.getenv("MYSQLUSER")
MYSQL_HOST = os.getenv("MYSQLHOST")
MYSQL_DB = os.getenv("MYSQLDATABASE")
MYSQL_PORT = os.getenv("MYSQLPORT")
MYSQL_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_CONNECTOR = "mysql+mysqlconnector"
DATABASE_URL = f"{MYSQL_CONNECTOR}://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()
