"""
IBM watsonx.ai REST API Gateway
Handles IAM token generation and LLM invocation using REST API
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Environment variables
API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
CLOUD_URL = os.getenv("CLOUD_URL", "https://us-south.ml.cloud.ibm.com")
LLM_NAME = os.getenv("LLM_NAME", "ibm/granite-3-8b-instruct")

# Token cache
_token_cache = {
    "token": None,
    "expires_at": 0
}


def _get_iam_token() -> str:
    """
    Get IBM Cloud IAM Bearer Token using API Key.
    Caches token for 50 minutes (IBM tokens valid for 60 minutes).
    """
    current_time = time.time()
    
    # Return cached token if still valid
    if _token_cache["token"] and current_time < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    # Request new token
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": API_KEY
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Cache token for 50 minutes (3000 seconds)
    _token_cache["token"] = access_token
    _token_cache["expires_at"] = current_time + 3000
    
    return access_token


def invoke_llm(prompt: str) -> str:
    """
    Invoke IBM watsonx.ai LLM using REST API.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        Generated text from the LLM
    """
    token = _get_iam_token()
    
    url = f"{CLOUD_URL}/ml/v1/text/generation?version=2023-05-29"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "input": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "temperature": 0.0,
            "repetition_penalty": 1.05,
            "stop_sequences": ["```"]
        },
        "model_id": LLM_NAME,
        "project_id": PROJECT_ID
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    generated_text = data["results"][0]["generated_text"]
    
    return generated_text

# Made with Bob
