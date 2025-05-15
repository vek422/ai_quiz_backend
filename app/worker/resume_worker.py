import aiohttp
import base64
import fitz  # PyMuPDF
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models import Candidate
from sqlalchemy import select
import openai
from app.core.config import OPENAI_API_KEY
from app.db.database import DATABASE_URL
from app.langgraph.other.parse_resume import parse_resume

# Create a dedicated engine and session factory for the worker
# This ensures we don't share connections across event loops
worker_engine = create_async_engine(DATABASE_URL)
WorkerSessionLocal = sessionmaker(
    bind=worker_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)


def get_gdrive_download_url(view_url: str) -> str:
    """
    Convert a Google Drive view URL to a direct download URL.
    """
    import re
    match = re.search(r"/d/([\w-]+)", view_url)
    if not match:
        raise ValueError("Invalid Google Drive link format")
    file_id = match.group(1)
    return f"https://drive.google.com/uc?export=download&id={file_id}"


async def download_resume_pdf(resume_link: str) -> bytes:
    print(f"Downloading resume from {resume_link}")
    async with aiohttp.ClientSession() as session:
        async with session.get(resume_link) as response:
            if response.status != 200:
                raise Exception("Failed to download resume")
            return await response.read()


async def convert_pdf_to_base64(pdf_bytes: bytes) -> str:
    print("Converting PDF to base64 image")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)  # first page
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    base64_img = base64.b64encode(img_bytes).decode('utf-8')
    return base64_img


async def parse_resume_with_openai(base64_img: str) -> str:
    print("Parsing resume with OpenAI")
    openai.api_key = OPENAI_API_KEY
    messages = [
        {
            "role": "system",
            "content": "Extract text from this resume image."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_img}"
                    }
                }
            ]
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    return response.choices[0].message.content


async def process_resume(candidate_uid: str, resume_link: str):
    try:
        # 1. Download the resume PDF
        pdf_bytes = await download_resume_pdf(get_gdrive_download_url(resume_link))

        # 2. Convert PDF to base64 image
        base64_img = await convert_pdf_to_base64(pdf_bytes)

        # 3. Parse with OpenAI
        parsed_text = await parse_resume_with_openai(base64_img)

        # 4. convert the parsed text into formated text using openai
        parsed_resume = parse_resume(resume_text=parsed_text)

        print(f"parsed resume {parsed_resume}")

        async with WorkerSessionLocal() as session:
            query = await session.execute(select(Candidate).where(Candidate.uid == candidate_uid))
            candidate = query.scalars().first()
            print(f"Candidate found: {candidate}")
            if candidate:
                print(
                    f"Updating candidate {candidate_uid} with parsed resume text")
                candidate.resume_text = parsed_resume
                await session.commit()
            else:
                print(
                    f"Warning: Candidate with ID {candidate_uid} not found in database")

    except Exception as e:
        print(f"Error in process_resume: {str(e)}")
        # Re-raise the exception so the queue can handle it
        raise
