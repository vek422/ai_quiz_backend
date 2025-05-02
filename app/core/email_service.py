from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException
from .config import SENDGRID_API_KEY,SENDGRID_FROM_EMAIL
def send_email(to_email: str, subject: str, content: str):
    api_key = SENDGRID_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="SendGrid API key not configured")
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def send_candidate_onboarding_email(name: str, email: str, password: str, test_title: str, resume_link: str, test_link: str):
    subject = f"Your Assessment Invitation for {test_title}"
    content = f"""
    <p>Dear {name},</p>
    <p>You have been invited to take the assessment: <b>{test_title}</b>.</p>
    <p>Your login credentials are:</p>
    <ul>
        <li>Email: {email}</li>
        <li>Password: {password}</li>
    </ul>
    <p>Resume Link: <a href='{resume_link}'>{resume_link}</a></p>
    <p>Test Link: <a href='{test_link}'>{test_link}</a></p>
    <p>Best of luck!</p>
    """
    return send_email(email, subject, content)
