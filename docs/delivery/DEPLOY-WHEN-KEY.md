# Deploy AI Doc when OPENAI_API_KEY is available

Do **not** paste the key into Git. Export it in the shell session only.

```bash
export OPENAI_API_KEY='sk-...'   # real key from OpenAI dashboard

# Optional: also store in Infisical path /openai for next time
# infisical secrets set OPENAI_API_KEY=... --path /openai

# Then ask the agent: deploy ai-doc
```

## What the agent will do after the key is present

1. Create or update a Render Web Service from `github.com/bookchaowalit/ai-doc-assistant`
2. Set `OPENAI_API_KEY` as a Render secret (not committed)
3. Smoke: `/health`, upload sample docs, one Thai query
4. Replace `[DEMO_URL]` in the outreach draft (private: business-catalog `docs/business/ai-doc-assistant-outreach.md`)
5. Mark task `#1969` done

## Current blockers (2026-08-11)

| Check | Result |
|---|---|
| Nested code on GitHub | Ready (`815d8e7`) |
| Render CLI login | Yes |
| Infisical auth for OPENAI | **Not configured** in this session |
| Local/env real OpenAI key | **Missing** |
