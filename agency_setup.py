"""
Agency Swarm Setup for Lead Generation System
"""
import os
from agency_swarm import Agent, Agency, set_openai_key
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
set_openai_key(os.getenv("OPENAI_API_KEY"))

# ==================== TOOLS ====================

class SearchLeadsTool(BaseTool):
    """
    Searches for leads based on specified criteria using multiple data sources.
    """
    query: str = Field(..., description="Search query for finding leads")
    location: str = Field(None, description="Location to search for leads")
    industry: str = Field(None, description="Industry to filter leads")
    
    def run(self):
        # This will integrate with your existing providers
        return f"Searching for leads with query: {self.query}, location: {self.location}, industry: {self.industry}"

class EnrichLeadTool(BaseTool):
    """
    Enriches lead data with additional information like email, phone, social profiles.
    """
    company_name: str = Field(..., description="Company name to enrich")
    website: str = Field(None, description="Company website URL")
    
    def run(self):
        # This will integrate with your enrichment logic
        return f"Enriching data for {self.company_name}"

class VerifyEmailTool(BaseTool):
    """
    Verifies if an email address is valid and deliverable.
    """
    email: str = Field(..., description="Email address to verify")
    
    def run(self):
        # This will integrate with your email verification
        return f"Verifying email: {self.email}"

class GenerateEmailTool(BaseTool):
    """
    Generates personalized email content for outreach.
    """
    lead_data: dict = Field(..., description="Lead data for personalization")
    template_type: str = Field("default", description="Type of email template to use")
    
    def run(self):
        # This will integrate with your email generation
        return f"Generating email for lead using template: {self.template_type}"

class ScheduleTaskTool(BaseTool):
    """
    Schedules automated tasks for lead processing.
    """
    task_type: str = Field(..., description="Type of task to schedule")
    frequency: str = Field(..., description="Frequency of the task (daily, weekly, etc.)")
    parameters: dict = Field(default_factory=dict, description="Task parameters")
    
    def run(self):
        # This will integrate with your scheduler
        return f"Scheduling {self.task_type} task with frequency: {self.frequency}"

# ==================== AGENTS ====================

# CEO Agent - Manages the overall lead generation strategy
ceo = Agent(
    name="CEO",
    description="Manages lead generation strategy and coordinates between agents",
    instructions="""You are the CEO of a lead generation agency. Your responsibilities include:
    1. Understanding client requirements for lead generation
    2. Coordinating with other agents to execute lead generation campaigns
    3. Ensuring quality of leads generated
    4. Managing the overall workflow
    5. Providing status updates and reports
    
    Always start by understanding what the user needs, then delegate tasks appropriately.""",
    temperature=0.7,
    max_prompt_tokens=25000,
)

# Lead Researcher Agent
lead_researcher = Agent(
    name="LeadResearcher",
    description="Specializes in finding and researching potential leads",
    instructions="""You are a Lead Research Specialist. Your responsibilities include:
    1. Searching for leads based on specified criteria
    2. Using multiple data sources to find comprehensive lead information
    3. Filtering leads based on quality and relevance
    4. Organizing lead data in a structured format
    
    Focus on finding high-quality, relevant leads that match the specified criteria.""",
    tools=[SearchLeadsTool],
    temperature=0.3,
)

# Data Enrichment Agent
data_enricher = Agent(
    name="DataEnricher",
    description="Enriches lead data with additional information",
    instructions="""You are a Data Enrichment Specialist. Your responsibilities include:
    1. Taking basic lead information and enriching it with additional data
    2. Finding contact information (emails, phone numbers)
    3. Gathering social media profiles
    4. Verifying the accuracy of information
    
    Ensure all enriched data is accurate and up-to-date.""",
    tools=[EnrichLeadTool, VerifyEmailTool],
    temperature=0.3,
)

# Email Campaign Agent
email_campaign = Agent(
    name="EmailCampaign",
    description="Manages email outreach campaigns",
    instructions="""You are an Email Campaign Specialist. Your responsibilities include:
    1. Creating personalized email content for leads
    2. Managing email campaigns
    3. Tracking email performance
    4. Optimizing email templates for better engagement
    
    Focus on creating compelling, personalized messages that resonate with leads.""",
    tools=[GenerateEmailTool],
    temperature=0.5,
)

# Automation Agent
automation = Agent(
    name="AutomationSpecialist",
    description="Handles task scheduling and automation",
    instructions="""You are an Automation Specialist. Your responsibilities include:
    1. Setting up automated workflows for lead generation
    2. Scheduling recurring tasks
    3. Managing data processing pipelines
    4. Monitoring and optimizing automated processes
    
    Ensure all automated processes run efficiently and reliably.""",
    tools=[ScheduleTaskTool],
    temperature=0.3,
)

# ==================== AGENCY ====================

# Create the agency with communication flows
agency = Agency(
    [
        ceo,  # CEO is the entry point
        [ceo, lead_researcher],  # CEO can communicate with Lead Researcher
        [ceo, data_enricher],    # CEO can communicate with Data Enricher
        [ceo, email_campaign],   # CEO can communicate with Email Campaign
        [ceo, automation],       # CEO can communicate with Automation
        [lead_researcher, data_enricher],  # Researcher can pass leads to Enricher
        [data_enricher, email_campaign],   # Enricher can pass data to Email Campaign
        [automation, lead_researcher],      # Automation can trigger research tasks
        [automation, email_campaign],       # Automation can trigger email campaigns
    ],
    shared_instructions="""This is a lead generation agency. All agents should:
    1. Focus on generating high-quality, relevant leads
    2. Ensure data accuracy and compliance
    3. Work efficiently and collaboratively
    4. Provide clear status updates
    5. Maintain data privacy and security standards
    """,
    temperature=0.5,
    max_prompt_tokens=25000
)

if __name__ == "__main__":
    # Run the demo interface
    print("Starting Lead Generation Agency...")
    print("\nYou can interact with the agency through the CEO agent.")
    print("Example commands:")
    print("- 'Find 10 software companies in New York'")
    print("- 'Enrich these leads with contact information'")
    print("- 'Create an email campaign for these leads'")
    print("- 'Schedule daily lead searches for tech startups'")
    print("\nStarting agency demo...\n")
    
    # Run the terminal demo
    agency.run_demo()