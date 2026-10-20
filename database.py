from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Base de datos local, no requiere servidor
SQLALCHEMY_DATABASE_URL = "sqlite:///./negocio_data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)