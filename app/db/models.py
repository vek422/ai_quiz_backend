from sqlalchemy import Column,String,ForeignKey
from app.db.database import Base

class Candidate(Base):
    __tablename__ = 'candidate'
    uid = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)

class LoginDetail(Base):
    __tablename__ = 'login_detail'
    uid = Column(String,ForeignKey('candidate.uid'),primary_key=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True)