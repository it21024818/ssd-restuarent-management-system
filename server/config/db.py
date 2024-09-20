import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import databases

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL)


metadata = sqlalchemy.MetaData()

engine = create_engine(
    DATABASE_URL
)