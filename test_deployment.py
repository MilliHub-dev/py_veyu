#!/usr/bin/env python3
"""
Test script to verify Railway deployment configuration locally
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_requirements():
    """Test that all requirements can be installed"""
    logger.info("Testing requirements.txt...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'check'
        ], capture_output=True, text=True, check=True)
        logger.info("✅ All requirements are compatible")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Requirements check failed: {e.stderr}")
        return False

def test_django_check():
    """Test Django system check"""
    logger.info("Running Django system check...")
    
    # Set environment for testing
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.railway_settings')
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'check', '--deploy'
        ], capture_output=True, text=True, check=True)
        logger.info("✅ Django system check passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Django check failed: {e.stderr}")
        return False

def test_migrations():
    """Test migrations"""
    logger.info("Testing migrations...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'showmigrations'
        ], capture_output=True, text=True, check=True)
        logger.info("✅ Migrations check passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migrations check failed: {e.stderr}")
        return False

def test_collectstatic():
    """Test static files collection"""
    logger.info("Testing static files collection...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput', '--dry-run'
        ], capture_output=True, text=True, check=True)
        logger.info("✅ Static files collection test passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Static files test failed: {e.stderr}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Testing Railway deployment configuration...")
    
    tests = [
        ("Requirements Check", test_requirements),
        ("Django System Check", test_django_check),
        ("Migrations Check", test_migrations),
        ("Static Files Check", test_collectstatic),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n📊 Test Results:")
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Ready for Railway deployment.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Fix issues before deploying.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)