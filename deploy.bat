# Quick Railway Deployment Script

echo "🚀 Preparing for Railway deployment..."

# Add all files
git add .

# Commit
git commit -m "Fix Railway deployment configuration"

# Push to GitHub
git push

echo "✅ Pushed to GitHub!"
echo "🔄 Railway will auto-deploy in a few moments..."
echo ""
echo "📝 Next steps:"
echo "1. Go to Railway dashboard"
echo "2. Wait for deployment to complete (2-3 minutes)"
echo "3. Check Deploy Logs for any errors"
echo "4. Copy your Railway URL"
echo "5. Update frontend/js/config.js with the Railway URL"
echo ""
echo "Need help? Check DEPLOYMENT_GUIDE_BENGALI.md"
