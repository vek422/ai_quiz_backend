import asyncio
import aiohttp
from app.worker.resume_worker import process_resume
from app.langgraph.other.parse_jd import parse_jd
from app.langgraph.models import UserState
from app.langgraph.graph.level1 import level1_graph
from app.langgraph.models import userstate_initializer, JobDescription, Resume
from app.langgraph.graph.level2 import level2_graph
from app.langgraph.graph.level3 import level3_graph


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


async def run_resume_processing():
    """Async function to run the resume processing."""
    processed_resume = await process_resume(
        "1", "https://drive.google.com/file/d/1uayWAiaA8Y9I7eajmNqbdj7IJ7BhI_QR/view?usp=drive_link")
    print(processed_resume)


if __name__ == "__main__":
    # Initialize user state
    user_state = userstate_initializer()

    user_state.job_description = JobDescription(
        required_skills=["Python", "Machine Learning", "Data Analysis"],
        title="Data Scientist",
        company="TechCorp",
        responsibilities=["Analyze data", "Develop models"],
        qualifications=["Master's in Data Science"]
    )

    user_state.resume = Resume(
        skills=["Python", "R", "SQL"],
        education=["MSc in Data Science"],
        experience=["2 years as Data Analyst"],
        projects=["Customer churn prediction", "Recommendation engine"],
        certifications=["Certified Data Scientist"],
        summary="Data scientist with expertise in machine learning and analytics."
    )

    # # Now you can run the graph
    result = level1_graph.invoke(user_state)
    print(result)

    # Run the async function with asyncio
    # asyncio.run(run_resume_processing())
