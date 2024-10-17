# app/config.py
import os
from dotenv import load_dotenv

# Load the .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SQLALCHEMY_DATABASE_URI = ( os.environ.get("DATABASE_URL").replace("postgres://", "postgresql://")  or "sqlite:///" + os.path.join(basedir, "app.db") )
