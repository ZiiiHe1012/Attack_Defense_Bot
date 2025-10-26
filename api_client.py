import requests
import json
from typing import Optional

token = "jI3sZMsJLctmIl87PAEQNeRq6NE9ymyx7M-rVk_MOWWA-kNbPDx-o8nAG0UUsmC-"

def dialogue( 
    user_input: str, 
    custom_prompt: str = None, 
    temperature: float = None, 
    max_tokens: int = None
) -> dict:
    
    url = "http://10.1.0.220:9002/api/dialogue"

    payload = {
        "token": token,
        "user_input": user_input
    }
    if custom_prompt is not None:
        payload["custom_prompt"] = custom_prompt
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    response = requests.post(url, json=payload)
    result = response.json()
    return result

def search_similar_files(
    database_name: str,
    token: str,
    query: str,
    top_k: int = None,
    metric_type: str = None,
    score_threshold: float = None,
    expr: Optional[str] = None
) -> dict:
    
    url = f"http://10.1.0.220:9002/api/databases/{database_name}/search"

    payload = {
        "token": token,
        "query": query,
    }
    if top_k is not None:
        payload["top_k"] = top_k
    if metric_type is not None:
        payload["metric_type"] = metric_type
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold
    if expr is not None:
        payload["expr"] = expr
    
    response = requests.post(url, json=payload)
    result = response.json()
    return result

