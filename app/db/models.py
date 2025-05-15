from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, ARRAY, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__ = 'user'
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'candidate' or 'recruiter'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    name = Column(String)
    candidate = relationship('Candidate', back_populates='user', uselist=False)
    recruiter = relationship('Recruiter', back_populates='user', uselist=False)


class Candidate(Base):
    __tablename__ = 'candidate'
    uid = Column(String, ForeignKey('user.uid'), primary_key=True)
    resume_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='candidate')
    assessments = relationship(
        'CandidateAssessment', back_populates='candidate')


class Recruiter(Base):
    __tablename__ = 'recruiter'
    uid = Column(String, ForeignKey('user.uid'), primary_key=True)
    name = Column(String)
    company = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship('User', back_populates='recruiter')
    tests = relationship('Test', back_populates='recruiter')


class Test(Base):
    __tablename__ = 'test'
    test_id = Column(String, primary_key=True, index=True)
    recruiter_uid = Column(String, ForeignKey('recruiter.uid'))
    title = Column(String)
    jd_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    job_description_id = Column(Integer, ForeignKey(
        'job_descriptions.id'))  # Added FK

    job_description = relationship('JobDescription')
    recruiter = relationship('Recruiter', back_populates='tests')
    assessments = relationship('CandidateAssessment', back_populates='test')


class CandidateAssessment(Base):
    __tablename__ = 'candidate_assessment'
    assessment_id = Column(String, primary_key=True, index=True)
    candidate_uid = Column(String, ForeignKey('candidate.uid'))
    test_id = Column(String, ForeignKey('test.test_id'))
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    status = Column(String, default="not_started")
    score = Column(Integer, nullable=True)

    candidate = relationship('Candidate', back_populates='assessments')
    test = relationship('Test', back_populates='assessments')


class JobDescription(Base):
    __tablename__ = 'job_descriptions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    # Use ARRAY if Postgres; otherwise replace with JSON
    required_skills = Column(ARRAY(String))
    responsibilities = Column(ARRAY(String))
    qualifications = Column(ARRAY(String))
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
