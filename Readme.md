# Getting Started

## 1. Install Dependencies

```
pip install -r requirements.txt
```

## 2. Configure Environment Variables

Create a `.env` file in the project root with the following content (replace with your actual keys):

```
OPENAI_API_KEY=your-openai-key
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_SENDER_EMAIL=your-email@example.com
```

## 3. Run the Application

```
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

# API Endpoints

## Authentication

### POST `/auth/login`

Authenticate a user and receive a JWT token.

- **Input:**
  - `email`: string
  - `password`: string
- **Response:**
  - `access_token`: string
  - `token_type`: string

---

## Recruiter Test Management

### POST `/test/recruiter/test`

Create a new test (job description) as a recruiter.

- **Input:**
  - `title`: string
  - `jd_text`: string
  - `scheduled_start`: datetime (optional)
  - `scheduled_end`: datetime (optional)
- **Response:**
  - `msg`: string
  - `test_id`: string

### GET `/test/recruiter/tests`

List all tests created by the recruiter.

- **Response:**
  - List of test objects (see model)

### PUT `/test/recruiter/test/{test_id}`

Update a test's details.

- **Input:**
  - Any of: `title`, `jd_text`, `scheduled_start`, `scheduled_end`
- **Response:**
  - `msg`: string

### DELETE `/test/recruiter/test/{test_id}`

Delete a test.

- **Response:**
  - `msg`: string

### POST `/test/recruiter/test/{test_id}/add_candidates`

Add candidates to a test.

- **Input:**
  - List of candidates:
    - `name`: string
    - `email`: string
    - `phone`: string
    - `resume_link`: string (Google Drive PDF link)
- **Response:**
  - List of candidate creation results

---

## Candidate Assessment

### GET `/test/candidate/tests`

List all available tests for the logged-in candidate.

- **Response:**
  - List of test objects

### POST `/test/candidate/assessment/start`

Start an assessment for a candidate.

- **Input:**
  - `candidate_uid`: string
  - `test_id`: string
- **Response:**
  - `assessment_id`: string
  - `current_level`: int
  - `resume_text`: string (parsed resume)
  - `jd_fields`: dict (parsed JD fields)

### POST `/test/candidate/assessment/{assessment_id}/level/{level}/submit`

Submit answers for a specific assessment level.

- **Input:**
  - `state`: dict (current workflow state)
  - `response`: dict (user's answers for this level)
- **Response:**
  - `assessment_id`: string
  - `level`: int
  - `result`: dict (next questions, pass/fail, or end)

### GET `/test/candidate/assessment/{assessment_id}/state`

Get the current state/progress of an assessment.

- **Response:**
  - `assessment_id`: string
  - `state`: dict (current workflow state)

### GET `/test/candidate/assessments`

List all assessments for a candidate.

- **Input:**
  - `candidate_uid`: string
- **Response:**
  - List of assessment objects

---

# Notes

- All endpoints require authentication unless otherwise specified.
- For assessment, resumes are parsed from Google Drive PDF links using LLM (no OCR dependency).
- Job Descriptions are parsed using LLM for structured extraction.
- All workflow state is checkpointed in SQLite for reliability.

# Example: Submitting Level Answers

```json
POST /test/candidate/assessment/{assessment_id}/level/1/submit
{
  "state": { ... },
  "response": {
    "skill1": { "q1_id": "answer", ... },
    ...
  }
}
```
