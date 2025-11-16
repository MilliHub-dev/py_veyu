"""
Cloudinary configuration test utility
"""
import os
import logging
from django.conf import settings
import cloudinary
import cloudinary.api


logger = logging.getLogger(__name__)


def test_cloudinary_configuration():
    """
    Test Cloudinary configuration and connectivity
    
    Returns:
        Dict with test results
    """
    results = {
        'configured': False,
        'connected': False,
        'cloud_name': None,
        'api_key_present': False,
        'errors': []
    }
    
    try:
        # Check if CLOUDINARY_URL is set
        cloudinary_url = getattr(settings, 'CLOUDINARY_URL', None) or os.getenv('CLOUDINARY_URL')
        
        if not cloudinary_url:
            results['errors'].append("CLOUDINARY_URL not found in settings or environment")
            return results
        
        results['configured'] = True
        
        # Check Cloudinary config
        config = cloudinary.config()
        
        if config.cloud_name:
            results['cloud_name'] = config.cloud_name
        else:
            results['errors'].append("Cloud name not configured")
        
        if config.api_key:
            results['api_key_present'] = True
        else:
            results['errors'].append("API key not configured")
        
        if not config.api_secret:
            results['errors'].append("API secret not configured")
        
        # Test connectivity
        try:
            # Simple API call to test connectivity
            cloudinary.api.ping()
            results['connected'] = True
            logger.info("Cloudinary connectivity test successful")
        except Exception as e:
            results['errors'].append(f"Connectivity test failed: {str(e)}")
            logger.error(f"Cloudinary connectivity test failed: {str(e)}")
        
    except Exception as e:
        results['errors'].append(f"Configuration test failed: {str(e)}")
        logger.error(f"Cloudinary configuration test failed: {str(e)}")
    
    return results


def get_cloudinary_info():
    """
    Get Cloudinary account information
    
    Returns:
        Dict with account info or None if unavailable
    """
    try:
        # Get usage information
        usage = cloudinary.api.usage()
        
        return {
            'plan': usage.get('plan', 'Unknown'),
            'credits': usage.get('credits', {}),
            'objects': usage.get('objects', {}),
            'bandwidth': usage.get('bandwidth', {}),
            'storage': usage.get('storage', {}),
            'requests': usage.get('requests', 0),
            'resources': usage.get('resources', 0),
            'derived_resources': usage.get('derived_resources', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get Cloudinary info: {str(e)}")
        return None


def validate_business_verification_config():
    """
    Validate business verification specific configuration
    
    Returns:
        Dict with validation results
    """
    results = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    try:
        # Check business verification settings
        bv_settings = getattr(settings, 'CLOUDINARY_BUSINESS_VERIFICATION', {})
        
        if not bv_settings:
            results['warnings'].append("CLOUDINARY_BUSINESS_VERIFICATION settings not found, using defaults")
        
        # Validate required folders
        base_folder = bv_settings.get('BASE_FOLDER', 'verification')
        if not base_folder:
            results['errors'].append("BASE_FOLDER not configured")
            results['valid'] = False
        
        # Validate document folders
        doc_folders = bv_settings.get('DOCUMENT_FOLDERS', {})
        required_docs = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
        
        for doc_type in required_docs:
            if doc_type not in doc_folders:
                results['warnings'].append(f"Document folder not configured for {doc_type}")
        
        # Validate file size limits
        max_size = bv_settings.get('MAX_FILE_SIZE', 5 * 1024 * 1024)
        if max_size > 10 * 1024 * 1024:  # 10MB
            results['warnings'].append("MAX_FILE_SIZE is quite large, consider reducing for better performance")
        
        # Validate security settings
        secure_expiry = bv_settings.get('SECURE_URL_EXPIRY', 3600)
        if secure_expiry > 86400:  # 24 hours
            results['warnings'].append("SECURE_URL_EXPIRY is very long, consider shorter expiry for better security")
        
    except Exception as e:
        results['errors'].append(f"Configuration validation failed: {str(e)}")
        results['valid'] = False
    
    return results


def run_full_cloudinary_test():
    """
    Run comprehensive Cloudinary test suite
    
    Returns:
        Dict with all test results
    """
    print("Running Cloudinary Configuration Tests...")
    print("=" * 50)
    
    # Test basic configuration
    config_test = test_cloudinary_configuration()
    print(f"Configuration Test: {'PASS' if config_test['configured'] else 'FAIL'}")
    print(f"Connectivity Test: {'PASS' if config_test['connected'] else 'FAIL'}")
    
    if config_test['cloud_name']:
        print(f"Cloud Name: {config_test['cloud_name']}")
    
    if config_test['errors']:
        print("Errors:")
        for error in config_test['errors']:
            print(f"  - {error}")
    
    print()
    
    # Test business verification config
    bv_test = validate_business_verification_config()
    print(f"Business Verification Config: {'PASS' if bv_test['valid'] else 'FAIL'}")
    
    if bv_test['warnings']:
        print("Warnings:")
        for warning in bv_test['warnings']:
            print(f"  - {warning}")
    
    if bv_test['errors']:
        print("Errors:")
        for error in bv_test['errors']:
            print(f"  - {error}")
    
    print()
    
    # Get account info if connected
    if config_test['connected']:
        info = get_cloudinary_info()
        if info:
            print("Account Information:")
            print(f"  Plan: {info.get('plan', 'Unknown')}")
            print(f"  Resources: {info.get('resources', 0)}")
            print(f"  Requests: {info.get('requests', 0)}")
    
    print("=" * 50)
    
    return {
        'configuration': config_test,
        'business_verification': bv_test,
        'account_info': get_cloudinary_info() if config_test['connected'] else None
    }


if __name__ == "__main__":
    # This allows running the test from command line
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
    django.setup()
    
    run_full_cloudinary_test()