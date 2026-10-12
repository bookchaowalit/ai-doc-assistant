---
title: AI Doc Assistant — Test Strategy และ UAT
doc_id: ADA-DOC-07
doc_type: test-uat
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: QA ร่วมกับ AI Product Delivery
related: 05-srs.md, 06-ux-flows.md, 08-rtm.md
---

# 07 — Test Strategy และ UAT

## 1. ระดับการทดสอบ

| ระดับ | เครื่องมือ/ไฟล์ | สถานะ |
|---|---|---|
| Unit / contract (ไม่ใช้ provider) | `test_api_contract.py`, `test_upload_safety.py`, `test_prompt_injection_boundary.py` (unittest) | มี; upload safety 4/4 ผ่าน (2026-08-11) |
| Browser UI safety | `test_ui_safety.cjs` (Playwright + Chromium) | มี; ไม่พบบันทึกผลล่าสุด |
| Integration / smoke | local smoke ไม่มี key, k3d `/health` `/readyz` | ผ่าน (2026-08-08, 2026-08-11) |
| Platform | Homelab resilience suite | PASS=25, FAIL=0, SKIP=1 (2026-08-02) |
| AI evaluation (ใช้ provider) | ชุด 22 เคส `evaluation-set.md` | ยังไม่รัน — ทุก gate ใน `evaluation-run-record.md` เป็น `blocked` |
| UAT | human reviewer ภายใน | ยังไม่เริ่ม — ไม่มีผู้ทดสอบที่ได้รับมอบหมาย |

คำสั่งรันชุดที่ไม่ต้องใช้ provider:

```bash
.venv/bin/python -m unittest -v test_api_contract.py test_upload_safety.py test_prompt_injection_boundary.py
NODE_PATH="$PWD/infra/node_modules" node engagements/internal/solo-empire/ai-doc-assistant/test_ui_safety.cjs
```

## 2. สภาพแวดล้อม

- Local/k3d ที่ไม่มี key สำหรับเทสต์ที่ไม่ใช้ provider
- Evaluation: store แยกต่อรอบ, เอกสารสังเคราะห์ที่อนุมัติ, provider key ที่อยู่นอก Git/log (ทุกเงื่อนไขยัง `blocked`)

## 3. Test cases

| TC | อ้างอิง | สิ่งที่ทดสอบ | ผลคาดหวัง | ผลล่าสุด |
|---|---|---|---|---|
| TC-01 | FR-01, US-01 | health/healthz/readyz/stats/docs ไม่มี key | HTTP 200 | ผ่าน |
| TC-02 | FR-05, US-02 | query เมื่อ KB ว่าง | ไม่พบ, `grounded=false`, cost 0 | ผ่าน |
| TC-03 | FR-02, FR-07, US-07 | ชนิดไม่รองรับ, ชื่อไฟล์ traversal, เกิน 10 MiB, ลบ temp file | 415/400/413; ไม่มีไฟล์ค้าง | ผ่าน 4/4 |
| TC-04 | FR-01, FR-10 | API contract: ขอบเขต `question` (1–2000) และ `top_k` (1–10), provider หายคืน 503 | ตาม schema | มีเทสต์; ไม่พบบันทึกผล |
| TC-05 | FR-06, US-06 | prompt/data boundary ของ context | context อยู่ใน delimiter, policy ไม่ถูก override | มีเทสต์; ไม่พบบันทึกผล |
| TC-06 | UI safety | render เป็น text, กันส่งซ้ำ, metrics หาย | ไม่ execute HTML, ไม่ส่งซ้ำ | มีเทสต์; ไม่พบบันทึกผล |
| TC-07 | FR-03, FR-04, US-03 | EVAL-TH-01..08 | ≥90% source ถูก, ≥95% citation support | ยังไม่รัน |
| TC-08 | FR-03, FR-04, US-04 | EVAL-EN-01..08 | เช่นเดียวกับ TC-07 | ยังไม่รัน |
| TC-09 | FR-05, US-05 | EVAL-NE-01..02 (populated KB) | 100% fail closed | ยังไม่รัน |
| TC-10 | FR-06, US-06 | EVAL-INJ-01..02 | 100% คง policy | ยังไม่รัน |
| TC-11 | FR-10, FR-11 | EVAL-OPS-01..02 (latency/cost/failure) | p95 ≤8 วิ, ≤USD 0.05/คำถาม | ยังไม่รัน |
| TC-12 | FR-08 | เรียก API โดยไม่มี credential | 401/403 | ทดสอบไม่ได้ — ยังไม่มี auth |
| TC-13 | FR-09, US-08 | ลบเอกสารแล้วตรวจทุก store | ไม่เหลือสำเนา มี audit | ทดสอบไม่ได้ — ยังไม่มี durable store |
| TC-14 | FR-11, US-09 | ซ้อม disable/rollback | upload/query ปิด, health ยังผ่าน | ยังไม่ซ้อม |
| TC-15 | FR-12, US-10 | UAT: ผู้ตรวจทบทวนคำตอบเชิงกฎหมายจากเอกสารตัวอย่าง | ไม่มีการกระทำอัตโนมัติ, มี disclaimer/การตรวจ | ยังไม่เริ่ม |
| TC-16 | NFR-01 | Homelab resilience suite | Argo Synced/Healthy, probe 200 | ผ่าน (2026-08-02) |

## 4. เกณฑ์ผ่าน (Entry / Exit)

- **Entry ของ evaluation:** owner ครบตาม `execution-gate-checklist.md`, corpus และ evaluation set อนุมัติ (DEC-AIDOC-002), provider อนุมัติ (DEC-AIDOC-004), store แยกต่อรอบ
- **Exit สำหรับ public demo:** TC-01–TC-11 ผ่านตามเกณฑ์ NFR-02–NFR-06 และไม่มี defect ระดับ release-blocking ค้าง
- **Exit สำหรับลูกค้า/staging:** เพิ่ม TC-12–TC-15 ผ่าน, restore drill ผ่าน (NFR-08), sponsor ลงนามตาม DEC-AIDOC-006
- ห้ามปัดผล `fail`/`blocked` เป็น `pass`; `not-applicable` ไม่อนุญาตใน run record

## 5. หลักฐานที่มี

- `STATUS-2026-08-11.md`: upload safety 4/4, k3d health/readyz ผ่าน, upload บน pilot fail closed ตามคาด
- `pilot-record.md`: local smoke 2026-08-08 (health, stats, empty query, chunk sample docs 3+3)
- `test-case-evidence.md`, `evaluation-run-record.md`: แบบฟอร์มพร้อม แต่ยังไม่มีผล provider

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| QA / AI Product Delivery | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Accountable sponsor | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `engagements/internal/solo-empire/ai-doc-assistant/README.md`, `test_*.py`, `test_ui_safety.cjs`
- `roles/pilots/ai-doc-assistant/test-strategy.md`, `test-case-evidence.md`, `evaluation-set.md`, `evaluation-run-record.md`, `execution-gate-checklist.md`, `pilot-record.md`
- `clients/solo-empire/ai-doc-assistant/STATUS-2026-08-11.md`
- `operations/ai/AI-DOC-ASSISTANT-EVALUATION-2026-08-08.md`
