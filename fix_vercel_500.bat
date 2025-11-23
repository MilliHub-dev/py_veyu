@echo off
REM Quick fix script for Vercel 500 errors - Windows version
REM Run this to diagnose and get fix instructions

echo ================================================================
echo          Vercel 500 Error - Quick Diagnostic Tool
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Run diagnostic script
echo Running diagnostics...
echo ----------------------------------------------------------------
echo.

if exist diagnose_vercel.py (
    python diagnose_vercel.py
) else (
    echo X diagnose_vercel.py not found
    echo.
    echo Manual checks:
    echo.
    
    echo 1. Environment Variables Check:
    echo    --------------------------------
    
    if defined DJANGO_SECRET_KEY (
        echo    [OK] DJANGO_SECRET_KEY is set
    ) else (
        echo    [X] DJANGO_SECRET_KEY not set
    )
    
    if defined DATABASE_URL (
        echo    [OK] DATABASE_URL is set
    ) else (
        echo    [X] DATABASE_URL not set
    )
    
    if defined CLOUDINARY_URL (
        echo    [OK] CLOUDINARY_URL is set
    ) else (
        echo    [X] CLOUDINARY_URL not set
    )
    
    if defined EMAIL_HOST_USER (
        echo    [OK] EMAIL_HOST_USER is set
    ) else (
        echo    [X] EMAIL_HOST_USER not set
    )
    
    if defined EMAIL_HOST_PASSWORD (
        echo    [OK] EMAIL_HOST_PASSWORD is set
    ) else (
        echo    [X] EMAIL_HOST_PASSWORD not set
    )
    
    echo.
    echo 2. Critical Files Check:
    echo    ----------------------
    
    if exist manage.py (
        echo    [OK] manage.py exists
    ) else (
        echo    [X] manage.py missing
    )
    
    if exist vercel.json (
        echo    [OK] vercel.json exists
    ) else (
        echo    [X] vercel.json missing
    )
    
    if exist api\vercel_app.py (
        echo    [OK] api\vercel_app.py exists
    ) else (
        echo    [X] api\vercel_app.py missing
    )
    
    if exist veyu\vercel_settings.py (
        echo    [OK] veyu\vercel_settings.py exists
    ) else (
        echo    [X] veyu\vercel_settings.py missing
    )
    
    if exist requirements.txt (
        echo    [OK] requirements.txt exists
    ) else (
        echo    [X] requirements.txt missing
    )
)

echo.
echo ----------------------------------------------------------------
echo.
echo Next Steps:
echo.
echo 1. Read VERCEL_QUICK_FIX.md for immediate solutions
echo 2. Set missing environment variables in Vercel dashboard
echo 3. Redeploy: vercel --prod
echo 4. Check logs: vercel logs --follow
echo 5. Test health: curl https://your-app.vercel.app/health
echo.
echo For detailed help, see:
echo   * VERCEL_QUICK_FIX.md - Quick solutions
echo   * VERCEL_TROUBLESHOOTING.md - Detailed guide
echo   * VERCEL_DEPLOYMENT_SUMMARY.md - Complete overview
echo.
echo ================================================================
echo.
pause
