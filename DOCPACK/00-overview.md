---
title: AI Doc Assistant — ภาพรวมระบบและสารบัญเอกสาร
doc_id: ADA-DOC-00
doc_type: overview
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: Product (AI Product Delivery)
related: 01-prd.md, 02-architecture.md, 03-nfr-security.md, 04-runbook.md, 05-srs.md, 06-ux-flows.md, 07-test-uat.md, 08-rtm.md
---

# 00 — ภาพรวมระบบและสารบัญเอกสาร

## สรุประบบ

AI Doc Assistant (engagement `ai-doc-assistant`, task `#1969`) เป็นแอป FastAPI สาธิตแนวคิด "RAG-as-a-Service": ผู้ใช้อัปโหลดเอกสาร `.txt`/`.pdf`/`.docx` ระบบตัดเป็น chunk สร้าง embedding ด้วย OpenAI `text-embedding-3-small` เก็บใน ChromaDB แล้วตอบคำถามภาษาไทย/อังกฤษด้วย `gpt-4o` พร้อมแหล่งอ้างอิง ค่า latency และต้นทุนต่อคำถาม ถ้าไม่พบหลักฐานจะตอบ "ไม่พบ" (`grounded=false`) แทนการเดา มีหน้าแชต HTML ในตัว ระบบเป็น pilot ภายในของ Solo Empire ใช้กับเอกสารสังเคราะห์เท่านั้น และยังไม่อนุมัติให้ใช้กับลูกค้า สาธารณะ หรือ production

## สถานะปัจจุบัน

| หัวข้อ | สถานะ |
|---|---|
| โค้ด | `master` ล่าสุด `ec6208e` (2026-09-09); การแก้ upload safety และ health ไม่ต้องใช้ key อยู่ใน `815d8e7` |
| Local / k3d pilot | `/health`, `/readyz` ผ่าน; upload/query fail closed เมื่อไม่มี `OPENAI_API_KEY` (STATUS 2026-08-11) |
| Homelab | `DEMO_ONLY` — Chroma และไฟล์อยู่บน storage ชั่วคราว; image `git-3bd4563…` |
| Public demo | **เลื่อน** จนกว่าจะมี `OPENAI_API_KEY` จริง (ENGAGEMENT-REGISTRY, ทบทวน 2026-10-13) |
| Staging | values มีแต่ `deploymentEnabled: false`, data plane เป็น placeholder |
| Lifecycle gate | `blocked` ที่ approval, data, security, evaluation, release และ handoff |
| Evaluation ด้วย provider | ยังไม่รัน (22 เคสออกแบบแล้ว) |

## ผู้ใช้หลัก

- **Operator ภายในที่ได้รับอนุญาต** — อัปโหลดชุดเอกสารที่อนุมัติและถามคำถาม (ตาม product scope)
- **ผู้ดูแลแพลตฟอร์ม** — deploy บน k3d/Homelab, ตรวจ probe, rollback
- **ผู้ชมเดโมเชิงพาณิชย์ (อนาคต)** — สำนักงานกฎหมาย/บัญชี/ประกันที่เป็นกลุ่มเป้าหมายใน `README.md`/`OUTREACH.md` — ยังห้ามส่ง outreach

## ตารางรายการเอกสาร

| รหัส | ไฟล์ | ชื่อเอกสาร | ผู้อ่านหลัก |
|---|---|---|---|
| ADA-DOC-00 | `00-overview.md` | ภาพรวมระบบและสารบัญเอกสาร | ทุกคน |
| ADA-DOC-01 | `01-prd.md` | Product Requirements (PRD) | Product, Sponsor |
| ADA-DOC-02 | `02-architecture.md` | System Architecture | Solution Architect, Platform |
| ADA-DOC-03 | `03-nfr-security.md` | NFR และความปลอดภัย | Security, Operations |
| ADA-DOC-04 | `04-runbook.md` | Runbook การติดตั้งและดูแลระบบ | Operations/DevOps |
| ADA-DOC-05 | `05-srs.md` | Software Requirements (SRS) | BA, AI Delivery |
| ADA-DOC-06 | `06-ux-flows.md` | User Flow และ Screen Inventory | UX, AI Delivery |
| ADA-DOC-07 | `07-test-uat.md` | Test Strategy และ UAT | QA, AI Delivery |
| ADA-DOC-08 | `08-rtm.md` | Requirements Traceability Matrix | BA, QA |

## วิธีอ่าน

1. อ่านเอกสารนี้และ `01-prd.md` เพื่อเข้าใจคำสัญญาของผลิตภัณฑ์และสิ่งที่ห้ามทำ
2. ฝั่งเทคนิคอ่าน `02` → `03` → `04`
3. ฝั่ง BA/QA อ่าน `05` → `07` → `08` — รหัส FR-01..FR-12 ตรงกับ BR-001..BR-012 ใน `roles/pilots/ai-doc-assistant/business-requirements.md`
4. รายละเอียดเชิงลึก (data contract, threat model, evaluation set) อยู่ใน `roles/pilots/ai-doc-assistant/` และ `operations/ai/AI-DOC-ASSISTANT-*.md` — docpack นี้สรุปและอ้างอิง ไม่ได้แทนที่

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product / Pack owner | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Accountable sponsor (venture owner) | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `clients/solo-empire/ai-doc-assistant/README.md`, `STATUS-2026-08-11.md`, `DEPLOY-WHEN-KEY.md`
- `docs/registries/ENGAGEMENT-REGISTRY.yaml` (`slug: ai-doc-assistant`)
- `roles/pilots/ai-doc-assistant/pilot-record.md`, `lifecycle-pack.md`
- `operations/ai/AI-DOC-ASSISTANT-HOMELAB-RUNBOOK.md`, `AI-DOC-ASSISTANT-PRODUCT-SCOPE.md`
- `infra/platform/gitops/applications/values/staging/ai-doc-assistant.yaml`
- `engagements/internal/solo-empire/ai-doc-assistant/` (`README.md`, `main.py`, `rag_engine.py`, git log)
