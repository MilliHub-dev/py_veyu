#!/bin/bash
# Script to verify Vercel environment variables are set

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Vercel Environment Variables Verification Tool        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not installed"
    echo ""
    echo "Install with: npm i -g vercel"
    echo ""
    echo "Or check manually in Vercel Dashboard:"
    echo "https://vercel.com/dashboard → Project → Settings → Environment Variables"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Required environment variables
REQUIRED_VARS=(
    "DJANGO_SECRET_KEY"
    "DATABASE_URL"
    "CLOUDINARY_URL"
    "EMAIL_HOST_USER"
    "EMAIL_HOST_PASSWORD"
    "EMAIL_HOST"
    "EMAIL_PORT"
    "DEFAULT_FROM_EMAIL"
)

echo "Checking required environment variables..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MISSING_COUNT=0
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if vercel env ls 2>/dev/null | grep -q "^$var"; then
        echo "✅ $var"
    else
        echo "❌ $var - NOT SET"
        MISSING_COUNT=$((MISSING_COUNT + 1))
        MISSING_VARS+=("$var")
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $MISSING_COUNT -eq 0 ]; then
    echo "🎉 All required environment variables are set!"
    echo ""
    echo "Next steps:"
    echo "1. Redeploy: vercel --prod"
    echo "2. Test: curl https://your-app.vercel.app/health"
    echo "3. Check logs: vercel logs --follow"
else
    echo "⚠️  $MISSING_COUNT variable(s) missing"
    echo ""
    echo "Missing variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  • $var"
    done
    echo ""
    echo "To add variables:"
    echo ""
    echo "Option 1 - Vercel Dashboard (Recommended):"
    echo "  1. Go to: https://vercel.com/dashboard"
    echo "  2. Select your project"
    echo "  3. Settings → Environment Variables"
    echo "  4. Add each missing variable"
    echo "  5. Select: Production, Preview, Development"
    echo ""
    echo "Option 2 - CLI:"
    echo "  vercel env add VARIABLE_NAME"
    echo ""
    echo "See check_deployment.md for values to use"
fi

echo ""
echo "╚════════════════════════════════════════════════════════════╝"
