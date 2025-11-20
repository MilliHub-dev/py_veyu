"""
Quick script to decode and validate the JWT token from the request
"""
import jwt
import json
from datetime import datetime

# The token from your request
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzNjUxNzAxLCJpYXQiOjE3NjM2NDcxMDMsImp0aSI6Ijg4MmI1MzU1MDNjZTQ2OTNiOWIzZjkyNjQ5Y2IwMWQwIiwidXNlcl9pZCI6NjksInVzZXJfdHlwZSI6ImRlYWxlciIsImVtYWlsIjoiZGV2b3BzLm1pbGxpaHViQGdtYWlsLmNvbSIsInByb3ZpZGVyIjoidmV5dSIsImlzcyI6InZleS11LXBsYXRmb3JtIn0.NfihR9jRQL2kmUb31mdT0bMfFiGbkXQGYQxEoXoBy5A"

# Decode without verification to see the payload
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("Token Payload:")
    print(json.dumps(decoded, indent=2))
    
    # Check expiration
    exp_timestamp = decoded.get('exp')
    if exp_timestamp:
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        print(f"\nToken expires at: {exp_datetime}")
        print(f"Current time: {now}")
        print(f"Token is {'EXPIRED' if now > exp_datetime else 'VALID'}")
        
    # Check issuer
    issuer = decoded.get('iss')
    print(f"\nIssuer: {issuer}")
    
    # Check user info
    print(f"User ID: {decoded.get('user_id')}")
    print(f"User Type: {decoded.get('user_type')}")
    print(f"Email: {decoded.get('email')}")
    
except Exception as e:
    print(f"Error decoding token: {e}")
