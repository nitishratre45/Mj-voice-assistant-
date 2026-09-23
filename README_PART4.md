# MJ Part 4 — Knowledge + Question Engine

Part 4 keeps the working voice system and adds a local knowledge/utility layer.

## New capabilities
- Current time/date questions
- Safe calculator
- Basic MJ identity/capability questions
- System info
- Explicit Google/web search commands
- Better routing: questions are checked before fixed app actions
- Existing conversation/memory/action behavior is preserved

## Examples
- "Abhi kitne baje hain?"
- "Aaj ki date kya hai?"
- "Calculate 25 * 4 + 10"
- "Mere laptop ki info"
- "Google Rohit Sharma latest news"
- "Search Tilak Varma"

For broad factual questions, Part 4 uses an explicit web-search fallback rather than pretending it knows an answer. A future part can add a real AI knowledge provider behind the same interface.

## Run
python .\\mj.py
