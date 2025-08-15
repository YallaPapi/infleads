# R27 Infinite AI Leads Agent

A powerful automated lead generation system with AI-powered scoring and personalized email outreach.

## Features

- 🔍 **Google Maps Scraping** - Extract business data via Apify
- 🤖 **AI Lead Scoring** - Score leads 0-10 based on digital presence weaknesses
- ✉️ **Personalized Emails** - Generate custom outreach emails for each lead
- 📊 **CSV Export** - Download results in standard format
- ☁️ **Google Drive Integration** - Auto-upload results to Drive
- 🖥️ **Web Interface** - Beautiful GUI for client demos

## Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file with your API keys:

```env
# Required
APIFY_API_KEY=your_apify_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional (for Drive upload)
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
```

### 3. Run the Application

#### Web Interface (Recommended for Demos)
```bash
python app.py
# Or on Windows: start_gui.bat
```
Then open http://localhost:5000 in your browser

#### Command Line
```bash
python main.py "coffee shops in Austin" --limit 25
```

## Web Interface Guide

1. **Enter Search Query**: Type business type and location (e.g., "dentists in Miami")
2. **Select Number of Leads**: Choose how many businesses to analyze (5-100)
3. **Click Generate**: Watch real-time progress as the system:
   - Fetches business data from Google Maps
   - Scores each lead with AI
   - Generates personalized emails
   - Creates downloadable CSV
4. **Download Results**: Get your CSV with all lead data and emails

## Lead Scoring Rules (R27)

The AI scores leads from 0-10 based on:
- **+3 points**: No website or broken website
- **+2 points**: Low review rating (<3.5 stars)
- **+2 points**: Less than 3 images
- **+2 points**: No social media presence
- **+1 point**: Unclaimed Google Business listing

Higher scores = Better leads (more need for digital marketing services)

## CSV Output Format

| Column | Description |
|--------|-------------|
| Name | Business name |
| Address | Full address |
| Phone | Phone number |
| Website | Website URL (or NA) |
| SocialMediaLinks | Social profiles |
| Reviews | Rating and count |
| Images | Number of images |
| LeadScore | AI score (0-10) |
| LeadScoreReasoning | Why this score |
| DraftEmail | Personalized outreach |

## Google Drive Setup (Optional)

For automatic uploads without popups:

1. Create a service account in Google Cloud Console
2. Download the JSON key as `service_account.json`
3. Share your Drive folder with the service account email
4. Set `GOOGLE_DRIVE_FOLDER_ID` in `.env`

## API Costs

Approximate costs per run:
- Apify: ~$0.01-0.03 per 25 leads
- OpenAI: ~$0.05-0.10 per 25 leads (scoring + emails)
- Total: ~$0.06-0.13 per 25 leads

## Troubleshooting

### "No leads found"
- Check your Apify API key is valid
- Try a different search query
- Ensure query includes location

### "Drive upload failed"
- Check credentials.json or service_account.json exists
- Verify Drive folder permissions

### "Scoring failed"
- Check OpenAI API key is valid
- Ensure you have API credits

## System Requirements

- Python 3.10+
- 4GB RAM minimum
- Internet connection
- Chrome/Firefox/Edge browser (for web interface)

## Support

For issues or questions, check the logs in `logs/r27_agent.log`