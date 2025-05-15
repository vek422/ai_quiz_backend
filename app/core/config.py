from langchain_openai import ChatOpenAI
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)
conn = sqlite3.connect('checkpoints.sqlite3', check_same_thread=False)
memory = SqliteSaver(conn)
