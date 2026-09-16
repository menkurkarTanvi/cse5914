from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

#THIS FILE IS JUST A TEMPLATE 

# Update with your database credentials: postgresql://user:password@host:port/db_name
DATABASE_URL = "postgresql://postgres:password@localhost:5432/my_database"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()

# Dependency to get the DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()