
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    debit_initial = Column(Float, nullable=False)
    concentration_initiale = Column(Float, nullable=False)
    residus = Column(Float, nullable=False)
    debit_filtre = Column(Float, nullable=False)
    concentration_finale = Column(Float, nullable=False)
    bilan = Column(Float, nullable=False)

    created_at = Column(DateTime, server_default=func.current_timestamp())
