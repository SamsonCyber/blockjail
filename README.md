# blockjail

**Tiny local jailbreak / prompt-injection gate for solo apps.**

No steganography stack. No API key. No model call.  
Pattern + normalize + light decode (hex / rot13 / base64 / percent / QP).

If you need image stego, authority/polarization detectors, and multi-channel forensics, use [stegoff](https://github.com/SamsonCyber/stegoff).  
If you just need “block obvious jailbreaks before the LLM”, use this.

## Install

```bash
pip install blockjail
# or from source
pip install -e .
```

## Python

```python
from blockjail import check, is_blocked

user = request.json["message"]

if is_blocked(user):
    return {"error": "blocked"}

# or richer:
v = check(user)
if v.blocked:
    return {"error": "blocked", "categories": list(v.categories)}
```

```python
# FastAPI-style middleware sketch
from blockjail import check

@app.middleware("http")
async def jail_gate(request, call_next):
    if request.url.path == "/chat" and request.method == "POST":
        body = await request.json()
        if check(body.get("message", "")).blocked:
            return JSONResponse({"error": "jailbreak_blocked"}, status_code=400)
    return await call_next(request)
```

## CLI

```bash
blockjail "Ignore all previous instructions"
# BLOCK instruction_override,...
echo $?   # 2

blockjail "Meeting at 3pm"
# ALLOW
echo $?   # 0

blockjail --json "reveal the system prompt"
```

Exit codes: `0` allow, `2` block.

## What it catches

- Classic “ignore previous instructions…” family  
- Prompt leak / system prompt probes  
- DAN / developer-mode style keywords  
- Soft paraphrases (first message, bootstrap policy, preamble disclosure, …)  
- Underscore / char-spaced tokenizer games  
- Light encodings: hex, rot13, base64, percent, quoted-printable  
- Minimal Chinese / Russian direct overrides  

## What it does **not** do

- Image / audio steganography  
- Semantic synonym micro-payloads that look like normal prose  
- Full NLU intent modeling (no LLM judge)  
- Network allowlists, tool sandboxing, or auth  

Those need other layers. blockjail is the cheap front door.

## License

MIT
