import requests

def wiki_search(disease: str):
    """
    Returns the summary of a disease from Wikipedia.
    Completely free, no API key required.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{disease.replace(' ', '%20')}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    summary = data.get("extract")

    if not summary:
        return None

    return summary
