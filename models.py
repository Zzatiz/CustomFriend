from sqlalchemy import Column, Integer, String, DateTime, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    billing_period = Column(String, default='daily')
    subscription_status = Column(String, default='inactive')
    subscribed_until = Column(DateTime, default=func.now())

username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

engine = create_engine(f'postgresql://{username}:{password}@localhost/CustomFriend')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
