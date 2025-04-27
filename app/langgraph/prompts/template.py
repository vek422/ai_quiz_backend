from langchain_core.prompts import ChatPromptTemplate
lvl1_prompt_template = ChatPromptTemplate.from_template("""
You are an expert technical evaluator in {skill}. Your task is to assess a candidate’s {skill} knowledge at the beginner level.

Generate {num} multiple choice questions (MCQs) that comprehensively evaluate their understanding of {skill}.

Strictly follow the JSON format provided below for each question. Do not include any explanations, extra text, or surrounding Markdown such as json```. Your response must start with `[` and end with `]` representing a array and be valid JSON.

JSON format for MCQ:
  "question": "Your question text here",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "answer": "The correct option",
  "max_time_required": "Time in seconds"
""")