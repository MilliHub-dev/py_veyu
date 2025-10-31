import random
import string

def make_random_otp(length=6):
    """Generate a random OTP of specified length.
    
    Args:
        length (int): Length of the OTP. Defaults to 6.
        
    Returns:
        str: A random numeric OTP of the specified length.
    """
    # Generate a random string of digits
    return ''.join(random.choices(string.digits, k=length))
