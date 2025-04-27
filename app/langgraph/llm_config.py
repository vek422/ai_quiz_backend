from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
conn = sqlite3.connect('checkpoints.sqlite3',check_same_thread=False)


memory = SqliteSaver(conn)   
llm = ChatOpenAI(model="gpt-4o",api_key=OPENAI_API_KEY)
