# Vercel Deployment Guide

## Prerequisites

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

## Environment Variables

Set these environment variables in Vercel dashboard or via CLI:

### Required
- `GOOGLE_API_KEY` - Your Google Maps API key

### Optional
- `OPENAI_API_KEY` - For advanced features (not used in basic version)
- `ANTHROPIC_API_KEY` - For advanced features
- `MAILTESTER_API_KEY` - For email verification
- `INSTANTLY_API_KEY` - For Instantly integration

## Deployment Steps

1. **Deploy to Vercel:**
   ```bash
   vercel --prod
   ```

2. **Set Environment Variables:**
   ```bash
   vercel env add GOOGLE_API_KEY
   # Enter your Google API key when prompted
   ```

3. **Redeploy with Environment Variables:**
   ```bash
   vercel --prod
   ```

## Vercel-Specific Limitations

### What's Different in Serverless Mode:

1. **No Background Jobs**: All processing is synchronous
2. **Processing Time Limit**: Max 5 minutes per request (300 seconds)
3. **No File Persistence**: No local file storage between requests
4. **Memory Limits**: Functions restart frequently

### Features Disabled/Limited:

- **Email Generation**: Disabled (too slow for serverless)
- **Background Processing**: All processing is synchronous
- **Job Persistence**: Jobs don't persist between requests
- **Very Large Batches**: 1000+ leads may timeout (but 100-500 should work fine)

## Testing Locally

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**
   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   ```

3. **Run Locally:**
   ```bash
   cd api
   python index.py
   ```

## Folder Structure for Vercel

```
infleads/
├── api/
│   └── index.py          # Main Flask app for Vercel
├── templates/
│   └── index_simple.html # Simplified UI
├── src/                  # Your existing modules
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── .vercelignore        # Files to exclude
└── DEPLOYMENT.md        # This file
```

## Monitoring

- Check Vercel dashboard for function logs
- Monitor function duration (should be under 60s)
- Watch for cold start delays

## Scaling Considerations

For higher volume or more features, consider:

1. **Vercel Pro**: Higher limits and faster functions
2. **External Database**: Use PostgreSQL/MongoDB for persistence
3. **Queue System**: Use Redis/Bull for background jobs
4. **CDN**: For faster global access

## Troubleshooting

### Common Issues:

1. **Timeout Errors**: Reduce lead limit or optimize queries
2. **Import Errors**: Check requirements.txt includes all dependencies
3. **Template Not Found**: Ensure templates/ folder is included
4. **API Key Issues**: Verify environment variables are set correctly

### Debug Commands:

```bash
# Check deployment logs
vercel logs

# List environment variables
vercel env ls

# Run function locally
vercel dev
```