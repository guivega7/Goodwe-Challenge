from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'aghwao2gj-1sa3ffa')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///solarmind.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False