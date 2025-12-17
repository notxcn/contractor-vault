"""
Email Scanner Service - Shadow IT Detection
Scans Gmail for signup verification emails using OAuth.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("contractor_vault.email_scanner")


# Common patterns for signup/verification emails
SIGNUP_PATTERNS = [
    # Subject line patterns
    r"verify your email",
    r"confirm your email",
    r"confirm your account",
    r"welcome to (.+)",
    r"activate your account",
    r"complete your registration",
    r"verify your (.+) account",
    r"your (.+) account is ready",
    r"thanks for signing up",
    r"thank you for registering",
    r"you're almost there",
    r"just one more step",
]

# Service name extraction patterns - maps sender domains to service names
SERVICE_MAPPINGS = {
    "canva.com": "Canva",
    "trello.com": "Trello",
    "notion.so": "Notion",
    "slack.com": "Slack",
    "asana.com": "Asana",
    "monday.com": "Monday.com",
    "figma.com": "Figma",
    "openai.com": "OpenAI",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "atlassian.com": "Atlassian",
    "jira.com": "Jira",
    "dropbox.com": "Dropbox",
    "zoom.us": "Zoom",
    "airtable.com": "Airtable",
    "miro.com": "Miro",
    "linear.app": "Linear",
    "vercel.com": "Vercel",
    "netlify.com": "Netlify",
    "heroku.com": "Heroku",
    "aws.amazon.com": "AWS",
    "cloud.google.com": "Google Cloud",
    "azure.microsoft.com": "Azure",
}


@dataclass
class DetectedEmail:
    """Represents a detected signup email."""
    subject: str
    sender: str
    sender_domain: str
    service_name: str
    date: datetime
    message_id: str


class EmailScannerService:
    """
    Scans emails for signup verification patterns.
    
    Uses Gmail API via OAuth to access contractor emails and
    detect when they sign up for external services.
    """
    
    def __init__(self, credentials=None):
        """
        Initialize scanner with OAuth credentials.
        
        Args:
            credentials: Google OAuth credentials object
        """
        self.credentials = credentials
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in SIGNUP_PATTERNS
        ]
    
    def is_signup_email(self, subject: str) -> tuple[bool, Optional[str]]:
        """
        Check if an email subject matches signup patterns.
        
        Returns:
            Tuple of (is_match, extracted_service_name)
        """
        for pattern in self._compiled_patterns:
            match = pattern.search(subject)
            if match:
                # Try to extract service name from capture group
                service = match.groups()[0] if match.groups() else None
                return True, service
        return False, None
    
    def extract_service_from_sender(self, sender_email: str) -> tuple[str, str]:
        """
        Extract service name and domain from sender email.
        
        Returns:
            Tuple of (service_name, domain)
        """
        # Extract domain from email
        match = re.search(r"@(.+?)(?:>|$)", sender_email)
        if not match:
            return "Unknown", "unknown"
        
        domain = match.group(1).lower()
        
        # Check known mappings
        for service_domain, service_name in SERVICE_MAPPINGS.items():
            if service_domain in domain:
                return service_name, domain
        
        # Fallback: use domain name as service
        domain_name = domain.split('.')[0].title()
        return domain_name, domain
    
    async def scan_gmail(
        self,
        email_address: str,
        max_results: int = 100,
        days_back: int = 30,
    ) -> list[DetectedEmail]:
        """
        Scan Gmail inbox for signup emails.
        
        Args:
            email_address: The email to scan
            max_results: Maximum emails to check
            days_back: How far back to scan
            
        Returns:
            List of detected signup emails
        """
        if not self.credentials:
            raise ValueError("Gmail API credentials not configured")
        
        # TODO: Implement actual Gmail API calls
        # This would use google-auth and google-api-python-client
        # 
        # from googleapiclient.discovery import build
        # service = build('gmail', 'v1', credentials=self.credentials)
        # results = service.users().messages().list(
        #     userId='me',
        #     q='newer_than:30d (subject:"verify" OR subject:"welcome" OR subject:"confirm")',
        #     maxResults=max_results
        # ).execute()
        
        logger.warning("Gmail scanning not yet implemented - returning demo data")
        
        # Return empty for now - actual implementation requires OAuth setup
        return []
    
    def analyze_email(
        self,
        subject: str,
        sender: str,
        date: datetime,
        message_id: str = "",
    ) -> Optional[DetectedEmail]:
        """
        Analyze a single email for signup patterns.
        
        Args:
            subject: Email subject line
            sender: Sender email address
            date: Email date
            message_id: Unique message identifier
            
        Returns:
            DetectedEmail if matches, None otherwise
        """
        is_signup, extracted_name = self.is_signup_email(subject)
        
        if not is_signup:
            return None
        
        service_name, domain = self.extract_service_from_sender(sender)
        
        # Prefer extracted name from subject if available
        if extracted_name and len(extracted_name) < 50:
            service_name = extracted_name.strip().title()
        
        return DetectedEmail(
            subject=subject,
            sender=sender,
            sender_domain=domain,
            service_name=service_name,
            date=date,
            message_id=message_id,
        )


# Singleton instance
_scanner: Optional[EmailScannerService] = None


def get_email_scanner() -> EmailScannerService:
    """Get the email scanner service singleton."""
    global _scanner
    if _scanner is None:
        _scanner = EmailScannerService()
    return _scanner
