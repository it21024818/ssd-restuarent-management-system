import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import databases

# Load environment variables from .env file
with open('.env', 'r') as f:
    for line in f:
        key, value = line.strip().split('=')
        os.environ[key] = value

DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL)


metadata = sqlalchemy.MetaData()

engine = create_engine(
    DATABASE_URL
)