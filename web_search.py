import requests
import os

def web_search(query, api_key=None):
    if api_key is None:
        api_key = os.getenv("SERPAPI_API_KEY")

    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": 5,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json().get("organic_results", [])
    return [r.get("snippet") for r in results if r.get("snippet")]
