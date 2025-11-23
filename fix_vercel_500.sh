#!/bin/bash
# Quick fix script for Vercel 500 errors
# Run this to diagnose and get fix instructions

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Vercel 500 Error - Quick Diagnostic Tool          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Run diagnostic script
echo "Running diagnostics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "diagnose_vercel.py" ]; then
    python3 diagnose_vercel.py
else
    echo "❌ diagnose_vercel.py not found"
    echo ""
    echo "Manual checks:"
    echo ""
    
    # Check environment variables
    echo "1. Environment Variables Check:"
    echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    VARS=("DJANGO_SECRET_KEY" "DATABASE_URL" "CLOUDINARY_URL" "EMAIL_HOST_USER" "EMAIL_HOST_PASSWORD")
    
    for var in "${VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "   ❌ $var not set"
        else
            echo "   ✅ $var is set"
        fi
    done
    
    echo ""
    echo "2. Critical Files Check:"
    echo "   ━━━━━━━━━━━━━━━━━━━━━━"
    
    FILES=("manage.py" "vercel.json" "api/vercel_app.py" "veyu/vercel_settings.py" "requirements.txt")
    
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file exists"
        else
            echo "   ❌ $file missing"
        fi
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Read VERCEL_QUICK_FIX.md for immediate solutions"
echo "2. Set missing environment variables in Vercel dashboard"
echo "3. Redeploy: vercel --prod"
echo "4. Check logs: vercel logs --follow"
echo "5. Test health: curl https://your-app.vercel.app/health"
echo ""
echo "📖 For detailed help, see:"
echo "   • VERCEL_QUICK_FIX.md - Quick solutions"
echo "   • VERCEL_TROUBLESHOOTING.md - Detailed guide"
echo "   • VERCEL_DEPLOYMENT_SUMMARY.md - Complete overview"
echo ""
echo "╚════════════════════════════════════════════════════════════╝"
