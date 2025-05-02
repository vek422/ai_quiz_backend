from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = 'user'
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'candidate' or 'recruiter'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship('Candidate', back_populates='user', uselist=False)
    recruiter = relationship('Recruiter', back_populates='user', uselist=False)

class Candidate(Base):
    __tablename__ = 'candidate'
    uid = Column(String, ForeignKey('user.uid'), primary_key=True)
    name = Column(String)
    phone = Column(String)
    resume_link = Column(String,nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='candidate')
    assessments = relationship('CandidateAssessment', back_populates='candidate')

class Recruiter(Base):
    __tablename__ = 'recruiter'
    uid = Column(String, ForeignKey('user.uid'), primary_key=True)
    name = Column(String)
    company = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='recruiter')
    tests = relationship('Test', back_populates='recruiter')

class Test(Base):
    __tablename__ = 'test'
    test_id = Column(String, primary_key=True, index=True)
    recruiter_uid = Column(String, ForeignKey('recruiter.uid'))
    title = Column(String)
    jd_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scheduled_end = Column(DateTime, nullable=True)
    scheduled_start = Column(DateTime, nullable=True)

    recruiter = relationship('Recruiter', back_populates='tests')
    assessments = relationship('CandidateAssessment', back_populates='test')

class CandidateAssessment(Base):
    __tablename__ = 'candidate_assessment'
    assessment_id = Column(String, primary_key=True, index=True)
    candidate_uid = Column(String, ForeignKey('candidate.uid'))
    test_id = Column(String, ForeignKey('test.test_id'))
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship('Candidate', back_populates='assessments')
    test = relationship('Test', back_populates='assessments')