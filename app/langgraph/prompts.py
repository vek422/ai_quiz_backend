from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import ChatPromptTemplate

resume_parsing_prompt = ChatPromptTemplate.from_template("""
You are an expert resume extractor. Your task is to extract structured information from a given resume. Use your expertise to carefully organize the extracted information into clean, usable fields.

Resume:
{resume_text}

Task: Extract the following fields and organize them into structured JSON format:
- education: (list) A list of educational qualifications mentioned in the resume, including degrees, certifications, or any relevant academic credentials.
- experience: (list) A list of work experiences, including job titles, companies, and duration (e.g., "Software Developer at TechCorp for 2 years").
- skills: (list) A list of skills mentioned, including programming languages, tools, frameworks, or soft skills.
- projects: (list) A list of any projects mentioned, particularly if they showcase relevant work or technical expertise. Optional.
- certifications: (list) A list of certifications or additional qualifications. Optional.
- summary: (string) A short 3-4 line summary of the candidate's professional background or profile. Optional.

Instructions:
1. Output strictly in valid JSON format.
2. Do not add any extra text, explanations, or Markdown formatting such as ```json.
3. The JSON response must start directly with `{{` and end with `}}`.

JSON Format:

{{
  "education": ["Degree 1", "Degree 2"],
  "experience": ["Experience 1", "Experience 2"],
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "projects": ["Project 1", "Project 2"],
  "certifications": ["Certification 1", "Certification 2"],
  "summary": "A short summary of the candidate's background."
}}
""")


jd_parsing_prompt = ChatPromptTemplate.from_template("""
You are an expert data extractor. Your task is to extract structured information from a given job description. Use your understanding to carefully organize the extracted information into clean, usable fields.

Job Description:
{jd_text}

Task: Extract the following fields and organize them into structured JSON format:
- title: (string) The job title.
- company: (string) The company's name.
- required_skills: (list of important skills mentioned in the job description, minimum 5 if available skills should be important keywords like programming language, framework or tool and sorted by highest importance first).
- responsibilities: (list of major job duties or responsibilities mentioned).
- qualifications: (list of qualifications or eligibility requirements).
- description: (a short 3-4 line summary of the job).

Instructions:
1. Output strictly in valid JSON format.
2. Do not add any extra text, explanations, or Markdown formatting such as ```json.
3. The JSON response must start directly with `{{` and end with `}}`.

JSON Format:

{{
  "title": "Job title",
  "company": "Company name",
  "required_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "responsibilities": ["Responsibility 1", "Responsibility 2", "Responsibility 3"],
  "qualifications": ["Qualification 1", "Qualification 2"],
  "description": "A short summary of the job."
}}
""")


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


lvl2_prompt_template = ChatPromptTemplate.from_template("""
Description: You are an expert technical evaluator in {skill}. Your job is to evaluate the candiadte's {skill} knowledge at the intermidiate level through the multiple select question. The candidate have done following projects {projects} and have following experience {experience}.

Task: Generate {num} multiple select question, where multiple options may correct or only one option is correct.

Instructions: Strictly follow the JSON format provided below for each question. Do not include any explanations, extra text, or surrounding Markdown such as json```. Your response must start with `[` and end with `]` representing an array and must be valid JSON.

JSON format for MSQ:
  "question": "Your question text here",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "answers": ["Correct Option 1", "Correct Option 2"],  // List of correct answers
  "max_time_required": "Time in seconds"
""")


lvl3_prompt_template = ChatPromptTemplate.from_template("""
You are an expert evaluator. Your task is to test whether a candidate is capable of performing a given job role based on its description. Use the job title, company, responsibilities, and qualifications to craft realistic, scenario-based questions.

Job Description:
Title: {title}
Company: {company}
Responsibilities: {responsibilities}
Qualifications: {qualifications}

Task: Generate {num} scenario-based questions. Each question must be derived directly from the job responsibilities and required qualifications. These scenarios should reflect real-world situations the candidate might face in this job and should test their practical thinking, problem-solving, and decision-making abilities.

Instructions:
1. For each question, randomly decide whether it should be a multiple choice question (MCQ) or a multiple select question (MSQ).
2. Strictly follow the corresponding JSON format based on the type you choose.
3. Do not mention whether it is MCQ or MSQ in the output.
4. Do not include any explanations, extra text, or surrounding Markdown such as ```json. Your response must start with `[` and end with `]`, representing a valid JSON array.
5. Base each scenario on actual job responsibilities or qualifications.


JSON Formats:

For MCQ (Only one option is correct):
  "Scenario" : "A real-world situation related to the job description where the candidate must apply relevant knowledge and skills.",
  "question": "A question testing the candidate's ability to act or decide in that scenario.",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
  "answer": "The correct option",
  "max_time_required": "Time in seconds"

For MSQ (Multiple options are correct):
  "Scenario" : "A real-world situation related to the job description where the candidate must apply relevant knowledge and skills.",
  "question": "A question testing the candidate's ability to act or decide in that scenario.",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
  "answers": ["Correct Option 1", "Correct Option 2"],
  "max_time_required": "Time in seconds"

""")
