# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Create a SQLite engine
engine = create_engine("sqlite:///faceDetection.db", echo=True)

# Create all tables
Base.metadata.create_all(engine)

# Create a configured "Session" class and instance
SessionLocal = sessionmaker(bind=engine)

# Dependency for accessing DB in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# # main.py

# from database import engine
# from models import Base

# # Create tables only if they don't exist
# Base.metadata.create_all(bind=engine)

# # Your main logic starts below
# print("Database and tables are ready.")







# pip install werkzeug


# from werkzeug.security import generate_password_hash, check_password_hash

# hashed = generate_password_hash("plain_password")
# # Store `hashed` in password_hash column

# check_password_hash(stored_password_hash, "attempted_password")


