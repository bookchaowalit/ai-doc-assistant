---
title: AI Doc Assistant — Requirements Traceability Matrix
doc_id: ADA-DOC-08
doc_type: rtm
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: BA + QA
related: 05-srs.md, 06-ux-flows.md, 07-test-uat.md
---

# 08 — Requirements Traceability Matrix

## 1. ตาราง RTM

| FR (BR ต้นทาง) | US | หน้าจอ | TC | สถานะหลักฐาน |
|---|---|---|---|---|
| FR-01 (BR-001) | US-01 | SC-01, SC-05 | TC-01, TC-04, TC-16 | ผ่าน |
| FR-02 (BR-002) | US-07 | SC-02 | TC-03 | ผ่าน (unit) |
| FR-03 (BR-003) | US-03, US-04 | SC-03, SC-04 | TC-07, TC-08 | ยังไม่รัน |
| FR-04 (BR-004) | US-03, US-04 | SC-04 | TC-07, TC-08 | ยังไม่รัน |
| FR-05 (BR-005) | US-02, US-05 | SC-04 | TC-02, TC-09 | บางส่วน (KB ว่างผ่าน) |
| FR-06 (BR-006) | US-06 | SC-04 | TC-05, TC-10 | มีเทสต์ boundary; evaluation ยังไม่รัน |
| FR-07 (BR-007) | US-07 | SC-02 | TC-03 | ผ่าน (unit); security review ค้าง |
| FR-08 (BR-008) | — | ไม่มี (ต้องมีหน้า login) | TC-12 | ยังไม่ implement |
| FR-09 (BR-009) | US-08 | ไม่มี | TC-13 | ยังไม่ implement |
| FR-10 (BR-010) | — | SC-04 (metrics) | TC-04, TC-11 | บางส่วน |
| FR-11 (BR-011) | US-09 | — | TC-14 | ยังไม่ซ้อม |
| FR-12 (BR-012) | US-10 | SC-04 | TC-15 | ยังไม่เริ่ม |

สรุป: 12 FR มี TC ครบ 100%; มีหลักฐานผ่าน 3 รายการ (FR-01, FR-02, FR-07 ระดับ unit), บางส่วน 2 รายการ (FR-05, FR-10)

## 2. ช่องว่างที่ยังไม่ครอบคลุม

1. ทุก requirement ด้านคุณภาพ AI (FR-03–FR-06) ขาดผล evaluation ที่ใช้ provider เพราะยังไม่มี `OPENAI_API_KEY` ที่อนุมัติ
2. FR-08 (auth/tenant) และ FR-09 (durable data/deletion) ยังไม่มีโค้ดและไม่มีหน้าจอรองรับ
3. NFR-08 (RPO/RTO) และ NFR-09 (deletion) ไม่มี TC ที่รันได้จนกว่าจะมี durable store
4. ผลล่าสุดของ `test_api_contract.py`, `test_prompt_injection_boundary.py`, `test_ui_safety.cjs` ไม่มีบันทึก
5. ไม่มีผู้ทดสอบ UAT และผู้รับมอบ (receiving owner) ที่ได้รับมอบหมาย
6. RTM ต้นทาง (`requirements-traceability-matrix.md`) ยังไม่ได้รับอนุมัติเป็น baseline

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| BA + QA | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Accountable sponsor | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `roles/pilots/ai-doc-assistant/requirements-traceability-matrix.md`, `business-requirements.md`, `user-stories.md`
- `05-srs.md`, `06-ux-flows.md`, `07-test-uat.md`, `03-nfr-security.md`
