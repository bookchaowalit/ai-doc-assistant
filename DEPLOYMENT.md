# Deployment Guide — RAG Demo

## Option 1: Railway (Recommended — Easiest)

### Prerequisites
- [Railway](https://railway.app) account
- Railway CLI installed (`npm i -g @railway/cli`)

### Steps
1. Login: `railway login`
2. Create project: `railway init`
3. Add environment variable:
   ```bash
   railway variables set OPENAI_API_KEY="sk-your-key-here"
   ```
4. Deploy:
   ```bash
   railway up
   ```
5. Get URL:
   ```bash
   railway domain
   ```

### Cost: ~$5/month (hobby plan)

---

## Option 2: Render

### Prerequisites
- [Render](https://render.com) account
- GitHub repo connected

### Steps
1. Push `infra/rag-demo/` to GitHub
2. Go to Render Dashboard → New → Web Service
3. Connect your repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variable:
   - Key: `OPENAI_API_KEY`
   - Value: `sk-your-key-here`
6. Add Persistent Disk:
   - Mount path: `/app/chroma-data`
   - Size: 1 GB
7. Deploy!

### Cost: Free tier available, $7/month for persistent disk

---

## Option 3: Docker (Any Platform)

### Build
```bash
docker build -t rag-demo .
```

### Run
```bash
docker run -d \
  --name rag-demo \
  -p 8000:8000 \
  -e OPENAI_API_KEY="sk-your-key-here" \
  -v rag-data:/app/chroma-data \
  rag-demo
```

### Access
Open http://localhost:8000

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key (starts with `sk-`) |

---

## Post-Deployment

1. **Test the API**:
   ```bash
   curl https://your-domain.com/health
   ```

2. **Upload sample documents** (one request per file):
   ```bash
   curl -X POST https://your-domain.com/upload -F "file=@sample-documents/company-policy.txt"
   curl -X POST https://your-domain.com/upload -F "file=@sample-documents/thai-legal-contract.txt"
   ```

3. **Try a query**:
   ```bash
   curl -X POST https://your-domain.com/query \
     -H "Content-Type: application/json" \
     -d '{"question": "ค่าชดเชยได้เท่าไหร่?", "top_k": 3}'
   ```

4. **Update portfolio landing page** to point to the live demo URL

---

## Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| Railway/Render hosting | $5-7 |
| OpenAI API (light usage) | $5-10 |
| **Total** | **$10-17/month** |

For demo purposes with minimal queries, expect ~$10/month.
