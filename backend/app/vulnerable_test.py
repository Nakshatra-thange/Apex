# File: vulnerable_test.py

import requests  # This is a known insecure dependency in our config

def get_user_data(user_id):
    # This is a hardcoded secret, which our regex should find.
    api_key = "a_super_secret_hardcoded_api_key_12345"
    
    # This is a classic SQL injection pattern that our regex should find.
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    
    print("Executing query...")