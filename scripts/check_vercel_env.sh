#!/bin/bash
# Quick script to check if Vercel environment is properly configured

echo "=================================="
echo "Vercel Environment Check"
echo "=================================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not installed"
    echo "   Install with: npm i -g vercel"
    exit 1
fi

echo "✅ Vercel CLI installed"
echo ""

# Check required environment variables
echo "Checking environment variables..."
echo ""

REQUIRED_VARS=(
    "DJANGO_SECRET_KEY"
    "DATABASE_URL"
    "CLOUDINARY_URL"
    "EMAIL_HOST_USER"
    "EMAIL_HOST_PASSWORD"
)

MISSING=0

for var in "${REQUIRED_VARS[@]}"; do
    # Check if variable is set in Vercel
    if vercel env ls | grep -q "$var"; then
        echo "✅ $var is set"
    else
        echo "❌ $var is MISSING"
        MISSING=$((MISSING + 1))
    fi
done

echo ""

if [ $MISSING -eq 0 ]; then
    echo "✅ All required environment variables are set"
    echo ""
    echo "Next steps:"
    echo "1. Deploy: vercel --prod"
    echo "2. Check logs: vercel logs --follow"
    echo "3. Test health: curl https://your-app.vercel.app/health"
else
    echo "❌ $MISSING environment variable(s) missing"
    echo ""
    echo "Add missing variables:"
    echo "  vercel env add VARIABLE_NAME"
    echo ""
    echo "Or use Vercel Dashboard:"
    echo "  https://vercel.com/dashboard → Project → Settings → Environment Variables"
fi

echo ""
echo "=================================="
