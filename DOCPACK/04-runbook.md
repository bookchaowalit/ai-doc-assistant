---
title: AI Doc Assistant — Runbook การติดตั้งและดูแลระบบ
doc_id: ADA-DOC-04
doc_type: runbook
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: DevOps / Operations and Platform
related: 02-architecture.md, 03-nfr-security.md, 07-test-uat.md
---

# 04 — Runbook การติดตั้งและดูแลระบบ

## 1. Environments

| Env | ที่อยู่ | Data contract | สถานะ |
|---|---|---|---|
| Local | `http://localhost:8000` (`python main.py` หรือ uvicorn) | — | ใช้ได้ |
| k3d dev | `ai-doc-assistant.dev.local` (cluster `k3d-solo-dev`) | `pilot-local` | `/health`, `/readyz` ผ่าน (2026-08-11) |
| Homelab | `ai-doc-assistant.homelab.local` (LAN ส่วนตัว), Argo `ai-doc-assistant-homelab` | `DEMO_ONLY` | image `git-3bd4563…` |
| Staging | values ใน `infra/platform/gitops/applications/values/staging/` | `staging-durable-planned` | `deploymentEnabled: false` |
| Public demo (PaaS) | ยังไม่มี (`[DEMO_URL]` ใน `OUTREACH.md`) | — | เลื่อนจนกว่าจะมี key; ผู้ให้บริการ **[ต้องยืนยัน]** |

## 2. Build / Deploy

**Local**

```bash
cd engagements/internal/solo-empire/ai-doc-assistant
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Container:** `docker build -t rag-demo .` → image `python:3.11-slim`, ผู้ใช้ non-root, port 8000

**Homelab (GitOps):** build และ push image tag `git-<app-repo-sha>` ไป private registry → อัปเดต tag ใน values ที่ Git track → Argo CD sync; ห้ามใช้ `:latest` (รายละเอียดใน `AI-DOC-ASSISTANT-HOMELAB-RUNBOOK.md`)

**PaaS (เมื่อได้รับอนุมัติ):** `render.yaml` (service `rag-demo`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`) หรือ `railway.toml` (Nixpacks, restart `ON_FAILURE` สูงสุด 3 ครั้ง) — การ deploy สาธารณะต้องมี approval ด้านค่าใช้จ่ายและ release gate (DEC-AIDOC-006)

## 3. Config / Secret (ชื่อตัวแปรเท่านั้น)

| ตัวแปร | จำเป็น | หน้าที่ |
|---|---|---|
| `OPENAI_API_KEY` | สำหรับ upload/query | key ของ provider — เก็บใน secret store/Render secret เท่านั้น ห้าม commit |
| `CORS_ALLOW_ORIGINS` | ไม่ | รายการ origin คั่นด้วย comma (ค่า default `http://localhost:8000`) |
| `PORT` | PaaS | port ที่แพลตฟอร์มกำหนด |
| `PYTHON_VERSION` | Render | เวอร์ชัน Python |

## 4. Health check

```bash
curl -fsS http://localhost:8000/health    # {"status":"ok"}
curl -fsS http://localhost:8000/healthz   # {"status":"ok"}
curl -fsS http://localhost:8000/readyz    # {"status":"ready"}
curl -fsS http://localhost:8000/stats     # จำนวนเอกสาร/chunk
```

Smoke หลังมี key: อัปโหลด `sample-documents/company-policy.txt` แล้ว `POST /query` คำถามภาษาไทยหนึ่งข้อ ต้องได้ `grounded=true` และมี `sources`; Homelab ใช้ resilience suite ตาม runbook (คาดหวัง Argo `Synced/Healthy`, probe ทั้งสาม HTTP 200)

## 5. Rollback

- Homelab: เปลี่ยน tag ใน values กลับเป็น `git-<sha>` ก่อนหน้าแล้วให้ Argo sync
- ปิดความเสี่ยง (NFR-10): ถอด `OPENAI_API_KEY` ออก → upload/query คืน 503 แต่ health ยังผ่าน = กลับสู่ `DEMO_ONLY` โดยไม่ต้อง redeploy โค้ด **[สมมติฐาน]** ว่าเป็นกลไก disable ที่ยอมรับได้ ต้องให้ owner อนุมัติ

## 6. Incident / Troubleshooting

| อาการ | สาเหตุ | การแก้ |
|---|---|---|
| `/upload` หรือ `/query` ได้ 503 "AI provider is not configured" | ไม่มี `OPENAI_API_KEY` | ตั้ง key ผ่าน secret store (ต้องมี approval ตาม DEC-AIDOC-004) |
| 415 / 413 / 400 ตอนอัปโหลด | นามสกุลไม่รองรับ / เกิน 10 MiB / ชื่อไฟล์มี path | ใช้ไฟล์ที่ถูกต้อง |
| 422 "Document could not be processed" | อ่านไฟล์ไม่ได้ (encoding/ไฟล์เสีย) | ตรวจไฟล์ต้นฉบับ |
| คำตอบ "ไม่พบ" ทุกคำถามหลัง restart | Chroma in-memory ถูกล้าง | อัปโหลดเอกสารใหม่ (ข้อจำกัด DEMO_ONLY) |
| ผลลัพธ์ต่างกันระหว่าง request | มีมากกว่า 1 replica แต่ละตัวมี Chroma แยก | ตั้ง replica = 1 |
| CORS error ในเบราว์เซอร์ | origin ไม่อยู่ใน `CORS_ALLOW_ORIGINS` | เพิ่ม origin แล้ว restart |

## 7. Backup / Restore

ไม่มี — ข้อมูลเป็น in-memory และเอกสารต้นฉบับคือ `sample-documents/` ใน Git (กู้คืนโดยอัปโหลดซ้ำ) การ backup จริงรอ durable data plane และ restore drill (`AI-DOC-ASSISTANT-RECOVERY-DRILL-2026-08-08.md`)

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Operations and Platform | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Accountable sponsor | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `operations/ai/AI-DOC-ASSISTANT-HOMELAB-RUNBOOK.md`, `AI-DOC-ASSISTANT-PILOT-RUNBOOK.md`
- `clients/solo-empire/ai-doc-assistant/STATUS-2026-08-11.md`, `DEPLOY-WHEN-KEY.md`
- `engagements/internal/solo-empire/ai-doc-assistant/main.py`, `Dockerfile`, `render.yaml`, `railway.toml`, `DEPLOYMENT.md`
- `infra/platform/onboarding/apps/ai-doc-assistant.yaml`, `infra/platform/gitops/applications/values/staging/ai-doc-assistant.yaml`
- `roles/pilots/ai-doc-assistant/runbook.md`, `decision-log.md`
