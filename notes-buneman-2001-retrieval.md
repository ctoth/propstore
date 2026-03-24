# Buneman 2001 Paper Retrieval Session

## GOAL
Retrieve and process "Why and Where: A Characterization of Data Provenance" by Buneman, Khanna, Tan (2001)

## DONE
- Searched for paper via search_papers.py - found with DOI 10.1007/3-540-44503-X_20
- fetch_paper.py created directory papers/Buneman_2001_CharacterizationDataProvenance with metadata.json
- PDF not available via open access (Springer paywall)
- Direct curl to sci-hub returns 403 (DDoS-Guard JS challenge blocks curl)

## STUCK
- Need browser automation to get through sci-hub's DDoS-Guard
- No Playwright MCP or Claude-in-Chrome tools available
- Chrome path provided: /c/Program Files/Google/Chrome/Application/chrome.exe
- Need to try: WebFetch deferred tool, or direct PDF from alternative sources

## NEXT
- Try WebFetch deferred tool
- Try alternative PDF sources (author pages, CiteSeerX, Penn CS dept)
- If all fail, ask Q to download manually
