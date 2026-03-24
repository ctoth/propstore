"""Search CrossRef for Ghidini & Giunchiglia 2001 paper DOI."""
import urllib.request
import json

url = "https://api.crossref.org/works?query=Local+Models+Semantics+Contextual+Reasoning+Ghidini+Giunchiglia&rows=5"
req = urllib.request.Request(url, headers={"User-Agent": "propstore/1.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())

for item in data["message"]["items"]:
    doi = item.get("DOI", "?")
    title = (item.get("title") or ["?"])[0][:100]
    authors = ", ".join(a.get("family", "?") for a in item.get("author", []))
    year = item.get("published-print", {}).get("date-parts", [[None]])[0][0]
    print(f"DOI: {doi}")
    print(f"Title: {title}")
    print(f"Authors: {authors}")
    print(f"Year: {year}")
    print()
