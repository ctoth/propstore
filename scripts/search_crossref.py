import urllib.request
import json
import sys

query = "Karacapilidis+Papadias+computer+supported+argumentation+collaborative+decision"
url = f"https://api.crossref.org/works?query={query}&rows=5"

req = urllib.request.Request(url, headers={"User-Agent": "propstore/1.0 (mailto:research@example.com)"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())

items = data["message"]["items"]
for i in items[:5]:
    title = i.get("title", [""])[0] if i.get("title") else ""
    doi = i.get("DOI", "")
    authors = ", ".join(a.get("family", "") for a in i.get("author", []))
    year = ""
    for date_key in ["published-print", "published-online", "created"]:
        if date_key in i:
            parts = i[date_key].get("date-parts", [[""]])
            if parts and parts[0]:
                year = parts[0][0]
                break
    print(f"Title: {title}")
    print(f"DOI: {doi}")
    print(f"Authors: {authors}")
    print(f"Year: {year}")
    print("---")
