"""
Agency Swarm Integration with Existing Lead Generation System
This integrates agency-swarm with your current providers and infrastructure
"""
import os
import sys
import json
from agency_swarm import Agent, Agency, set_openai_key
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import your existing modules
from providers.multi_provider import MultiProvider
from providers.hybrid_scraper import HybridScraper
from providers.pure_scraper import PureScraper
from providers.free_scraper import FreeScraper
from email_generator import EmailGenerator
from instantly_integration import InstantlyIntegration
import sqlite3

# Load environment variables
load_dotenv()

# Set OpenAI API key
set_openai_key(os.getenv("OPENAI_API_KEY"))

# ==================== INTEGRATED TOOLS ====================

class SearchLeadsWithProviderTool(BaseTool):
    """
    Searches for leads using the existing multi-provider system.
    """
    query: str = Field(..., description="Search query for finding leads")
    location: str = Field(None, description="Location to search for leads")
    provider_type: str = Field("hybrid", description="Provider type: hybrid, pure, free, or multi")
    max_results: int = Field(10, description="Maximum number of results to return")
    
    def run(self):
        try:
            # Select provider based on type
            if self.provider_type == "hybrid":
                provider = HybridScraper()
            elif self.provider_type == "pure":
                provider = PureScraper()
            elif self.provider_type == "free":
                provider = FreeScraper()
            else:
                provider = MultiProvider()
            
            # Search for leads
            results = provider.search(self.query, self.location, max_results=self.max_results)
            
            return {
                "status": "success",
                "count": len(results),
                "leads": results
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class EnrichLeadFromDatabaseTool(BaseTool):
    """
    Enriches lead data using existing database and providers.
    """
    company_name: str = Field(..., description="Company name to enrich")
    website: str = Field(None, description="Company website URL")
    use_hunter: bool = Field(True, description="Use Hunter.io for email finding")
    
    def run(self):
        try:
            enriched_data = {
                "company": self.company_name,
                "website": self.website
            }
            
            # Use hybrid scraper for enrichment
            provider = HybridScraper()
            
            if self.website:
                # Get additional data from website
                company_data = provider.get_company_details(self.website)
                enriched_data.update(company_data)
            
            # Find emails if Hunter is enabled
            if self.use_hunter and os.getenv("HUNTER_API_KEY"):
                from src.providers.base import BaseProvider
                base = BaseProvider()
                emails = base.find_emails_hunter(self.company_name, self.website)
                enriched_data["emails"] = emails
            
            return {
                "status": "success",
                "data": enriched_data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class GeneratePersonalizedEmailTool(BaseTool):
    """
    Generates personalized emails using the existing email generator.
    """
    lead_data: dict = Field(..., description="Lead data for personalization")
    template_name: str = Field("default", description="Email template to use")
    tone: str = Field("professional", description="Tone of the email: professional, casual, formal")
    
    def run(self):
        try:
            generator = EmailGenerator()
            
            # Generate email content
            email_content = generator.generate_email(
                company_name=self.lead_data.get("company", ""),
                contact_name=self.lead_data.get("contact_name", ""),
                industry=self.lead_data.get("industry", ""),
                template=self.template_name,
                tone=self.tone
            )
            
            return {
                "status": "success",
                "email": email_content
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class SaveLeadsToDatabaseTool(BaseTool):
    """
    Saves leads to the SQLite database.
    """
    leads: List[dict] = Field(..., description="List of leads to save")
    campaign_id: str = Field(None, description="Campaign ID to associate with leads")
    
    def run(self):
        try:
            db_path = "data/scheduler.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create leads table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    website TEXT,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    industry TEXT,
                    campaign_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert leads
            saved_count = 0
            for lead in self.leads:
                cursor.execute('''
                    INSERT INTO leads (company_name, website, email, phone, address, industry, campaign_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead.get("company_name", ""),
                    lead.get("website", ""),
                    lead.get("email", ""),
                    lead.get("phone", ""),
                    lead.get("address", ""),
                    lead.get("industry", ""),
                    self.campaign_id
                ))
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "saved_count": saved_count
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class SendEmailCampaignTool(BaseTool):
    """
    Sends email campaigns using Instantly integration.
    """
    campaign_name: str = Field(..., description="Name of the campaign")
    leads: List[dict] = Field(..., description="List of leads with email addresses")
    email_content: str = Field(..., description="Email content to send")
    
    def run(self):
        try:
            instantly = InstantlyIntegration()
            
            # Create campaign
            campaign_result = instantly.create_campaign(
                name=self.campaign_name,
                leads=self.leads,
                email_content=self.email_content
            )
            
            return {
                "status": "success",
                "campaign": campaign_result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class ScheduleAutomationTool(BaseTool):
    """
    Schedules automated tasks using the existing scheduler.
    """
    task_type: str = Field(..., description="Type of task: search_leads, enrich_data, send_emails")
    schedule: str = Field(..., description="Schedule: daily, weekly, monthly")
    parameters: dict = Field(default_factory=dict, description="Task parameters")
    
    def run(self):
        try:
            db_path = "data/scheduler.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create scheduled_tasks table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT,
                    schedule TEXT,
                    parameters TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert scheduled task
            cursor.execute('''
                INSERT INTO scheduled_tasks (task_type, schedule, parameters)
                VALUES (?, ?, ?)
            ''', (
                self.task_type,
                self.schedule,
                json.dumps(self.parameters)
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "task_id": task_id,
                "message": f"Task scheduled successfully with ID: {task_id}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# ==================== SPECIALIZED AGENTS ====================

# CEO Agent - Strategic coordinator
ceo = Agent(
    name="CEO",
    description="Strategic coordinator for lead generation operations",
    instructions="""You are the CEO of an advanced lead generation system. Your role is to:
    1. Understand client requirements and translate them into actionable tasks
    2. Coordinate with specialized agents to execute lead generation campaigns
    3. Ensure quality and compliance in all operations
    4. Provide comprehensive reports and insights
    5. Optimize the overall lead generation strategy
    
    Always start by clarifying the user's needs, then create a strategic plan and delegate appropriately.
    Maintain high standards for data quality and compliance.""",
    temperature=0.7,
    max_prompt_tokens=25000,
)

# Lead Hunter Agent
lead_hunter = Agent(
    name="LeadHunter",
    description="Specialized in finding and identifying potential leads",
    instructions="""You are a Lead Hunter specialist. Your expertise includes:
    1. Using multiple data providers (hybrid, pure, free) to find leads
    2. Optimizing search queries for better results
    3. Filtering and qualifying leads based on criteria
    4. Identifying high-value prospects
    
    Use the SearchLeadsWithProviderTool strategically:
    - Use 'hybrid' for balanced cost/quality
    - Use 'pure' for high-quality verified data
    - Use 'free' for budget-conscious searches
    - Use 'multi' for comprehensive coverage""",
    tools=[SearchLeadsWithProviderTool, SaveLeadsToDatabaseTool],
    temperature=0.3,
)

# Data Specialist Agent
data_specialist = Agent(
    name="DataSpecialist",
    description="Expert in data enrichment and verification",
    instructions="""You are a Data Enrichment Specialist. Your responsibilities:
    1. Enrich basic lead information with comprehensive data
    2. Verify email addresses and contact information
    3. Ensure data accuracy and completeness
    4. Maintain data quality standards
    
    Focus on providing accurate, actionable data that sales teams can use immediately.""",
    tools=[EnrichLeadFromDatabaseTool],
    temperature=0.3,
)

# Campaign Manager Agent
campaign_manager = Agent(
    name="CampaignManager",
    description="Manages email outreach and marketing campaigns",
    instructions="""You are a Campaign Manager specializing in email outreach. Your role includes:
    1. Creating personalized email campaigns
    2. Managing campaign execution through Instantly
    3. Optimizing email content for engagement
    4. Tracking and reporting campaign performance
    
    Focus on creating compelling, personalized messages that convert.""",
    tools=[GeneratePersonalizedEmailTool, SendEmailCampaignTool],
    temperature=0.5,
)

# Automation Engineer Agent
automation_engineer = Agent(
    name="AutomationEngineer",
    description="Designs and implements automated workflows",
    instructions="""You are an Automation Engineer. Your expertise includes:
    1. Setting up automated lead generation workflows
    2. Scheduling recurring tasks for continuous lead flow
    3. Optimizing processes for efficiency
    4. Monitoring and maintaining automated systems
    
    Design robust, scalable automation that runs reliably without manual intervention.""",
    tools=[ScheduleAutomationTool],
    temperature=0.3,
)

# ==================== AGENCY CONFIGURATION ====================

# Create the agency with optimized communication flows
lead_gen_agency = Agency(
    [
        ceo,  # CEO as the main entry point
        [ceo, lead_hunter],           # CEO directs lead hunting
        [ceo, data_specialist],        # CEO requests data enrichment
        [ceo, campaign_manager],       # CEO initiates campaigns
        [ceo, automation_engineer],    # CEO requests automation
        [lead_hunter, data_specialist],      # Hunter passes leads for enrichment
        [data_specialist, campaign_manager],  # Specialist provides enriched data for campaigns
        [automation_engineer, lead_hunter],    # Automation triggers lead searches
        [automation_engineer, campaign_manager], # Automation triggers campaigns
    ],
    shared_instructions="""This is an advanced lead generation agency integrated with existing infrastructure.
    
    Key Principles:
    1. Quality over quantity - focus on high-value, relevant leads
    2. Data accuracy is paramount - verify before using
    3. Compliance first - respect privacy laws and regulations
    4. Efficiency through automation - minimize manual work
    5. Continuous improvement - learn from results and optimize
    
    Available Resources:
    - Multiple data providers (Hybrid, Pure, Free scrapers)
    - Email verification and enrichment tools
    - Instantly for email campaigns
    - SQLite database for data persistence
    - Automated scheduling system
    
    Always maintain professional standards and protect client data.""",
    temperature=0.5,
    max_prompt_tokens=25000
)

def run_agency():
    """Run the lead generation agency"""
    print("=" * 60)
    print("LEAD GENERATION AGENCY - AGENCY SWARM")
    print("=" * 60)
    print("\nIntegrated with your existing lead generation infrastructure:")
    print("✓ Multi-provider search system")
    print("✓ Data enrichment and verification")
    print("✓ Email campaign management")
    print("✓ Automated scheduling")
    print("✓ Database persistence")
    print("\n" + "=" * 60)
    print("\nExample Commands:")
    print("• 'Find 20 software companies in San Francisco'")
    print("• 'Enrich these leads with contact information'")
    print("• 'Create a personalized email campaign for SaaS companies'")
    print("• 'Schedule daily searches for tech startups in New York'")
    print("• 'Generate a report of all leads collected this week'")
    print("\n" + "=" * 60)
    print("\nStarting agency interface...\n")
    
    # Run the terminal demo
    lead_gen_agency.run_demo()

if __name__ == "__main__":
    run_agency()