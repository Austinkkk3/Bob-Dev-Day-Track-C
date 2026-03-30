import os
import time
import requests
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
CLOUD_URL = os.getenv("CLOUD_URL")
LLM_NAME = os.getenv("LLM_NAME")

# Token cache
_token_cache: Optional[dict] = None


def _get_iam_token() -> str:
    """
    Exchange API key for IAM Bearer token.
    Caches token for 50 minutes (tokens expire after 60 minutes).
    """
    global _token_cache
    
    # Check if cached token is still valid
    if _token_cache is not None:
        elapsed = time.time() - _token_cache["timestamp"]
        if elapsed < 3000:  # 50 minutes in seconds
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
    
    # Cache the token
    _token_cache = {
        "token": access_token,
        "timestamp": time.time()
    }
    
    return access_token


def invoke_llm(prompt: str) -> str:
    """
    Invoke IBM watsonx.ai text generation endpoint.
    
    Args:
        prompt: The input prompt for text generation
        
    Returns:
        Generated text response
    """
    # Get IAM token
    token = _get_iam_token()
    
    # Prepare request
    url = f"{CLOUD_URL}/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model_id": LLM_NAME,
        "input": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "temperature": 0.0,
            "repetition_penalty": 1.05,
            "stop_sequences": ["```"]
        },
        "project_id": PROJECT_ID
    }
    
    # Make request
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Extract generated text
    result = response.json()
    generated_text = result["results"][0]["generated_text"]
    
    return generated_text

# Made with Bob
