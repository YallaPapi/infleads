#!/bin/bash

echo "🚀 Deploying R27 Infinite AI Leads Agent to Vercel"
echo "================================================"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Please install it first:"
    echo "npm install -g vercel"
    exit 1
fi

# Check if logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel first:"
    vercel login
fi

echo "📦 Deploying to Vercel..."

# Deploy to production
vercel --prod

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set your environment variables in Vercel dashboard:"
echo "   - GOOGLE_API_KEY (required)"
echo "   - OPENAI_API_KEY (optional)"
echo "   - MAILTESTER_API_KEY (optional)"
echo "   - INSTANTLY_API_KEY (optional)"
echo ""
echo "2. Or set them via CLI:"
echo "   vercel env add GOOGLE_API_KEY"
echo ""
echo "3. Redeploy after setting environment variables:"
echo "   vercel --prod"
echo ""
echo "🌐 Your app should be live at your Vercel URL!"