from app.db.database import get_db
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CandidateAssessment, Test
from sqlalchemy import select
from app.langgraph.models import UserState
from typing import Dict
import logging
from app.langgraph.models import userstate_initializer
logger = logging.getLogger(__name__)


def initialize_assessment(userState: UserState) -> UserState:

    # if not parsed_jd or not parsed_resume:
    #     logger.error(
    #         f"Initialization failed: parsed_jd={parsed_jd}, parsed_resume={parsed_resume}")
    #     raise HTTPException(status_code=400, detail="JD not found in context")

    # userState.job_description = parsed_jd
    # userState.resume = parsed_resume

    logger.info(f"User {userState.user_id} initialized with JD and Resume.")
    return userState
