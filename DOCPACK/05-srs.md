---
title: AI Doc Assistant — Software Requirements (SRS)
doc_id: ADA-DOC-05
doc_type: srs
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: BA
related: 01-prd.md, 06-ux-flows.md, 07-test-uat.md, 08-rtm.md
---

# 05 — Software Requirements (SRS)

> รหัส FR-01..FR-12 ในเอกสารนี้ตรงกับ BR-001..BR-012 ของ requirement set `AI-DOC-REQ-SET-2026-08-08` และ US-01..US-10 ตรงกับ acceptance example AC-01..AC-10

## 1. บทบาทและสิทธิ์

| บทบาท | สิทธิ์ปัจจุบัน (โค้ด) | สิทธิ์เป้าหมาย |
|---|---|---|
| ผู้เรียก API ใด ๆ | เรียกได้ทุก endpoint ไม่ต้องยืนยันตัวตน | ต้องไม่มีสิทธิ์ (FR-08) |
| Operator ที่ได้รับอนุญาต | — | อัปโหลดเอกสารที่อนุมัติ, ถามคำถาม, ดู stats ภายใน tenant ของตน |
| ผู้ดูแลแพลตฟอร์ม | เข้าถึง probe และ deploy ผ่าน GitOps | ปิด upload/query, rollback, ดู log ที่ redact แล้ว |
| ผู้ตรวจคำตอบ (Human reviewer) | — | ตรวจคำตอบที่มีผลทางกฎหมาย/การเงินก่อนใช้ (FR-12) |

## 2. User stories และ acceptance criteria

| ID | Story | Given / When / Then |
|---|---|---|
| US-01 (AC-01) | Operator ตรวจว่าระบบพร้อมโดยไม่มี key | Given ไม่มี key When เรียก health/readiness/docs/stats Then ตอบได้โดยไม่อ่าน secret |
| US-02 (AC-02) | Operator ถามเมื่อ KB ว่าง | Given KB ว่าง When query Then ตอบไม่พบ, `grounded=false`, cost 0 |
| US-03 (AC-03) | Operator ถามภาษาไทย | Given KB มีเอกสารที่ตอบได้ When query Then คำตอบอ้างอิง source/chunk ที่ถูกต้อง |
| US-04 (AC-04) | Operator ถามภาษาอังกฤษ | เช่นเดียวกับ US-03 |
| US-05 (AC-05) | Operator ถามสิ่งที่ไม่มีในเอกสาร | Then ไม่แต่งคำตอบหรือ citation |
| US-06 (AC-06) | มีคำสั่งแฝงในเอกสาร/คำถาม | Then ถือเป็นข้อมูลไม่น่าเชื่อถือ policy ยังมีผล |
| US-07 (AC-07) | Operator อัปโหลดไฟล์ | Given ได้รับอนุญาตและไฟล์อยู่ในขอบเขต Then ประมวลผล; ไฟล์ผิดชนิด/path/ขนาด ถูกปฏิเสธ ไม่เขียนไฟล์ผิดที่ |
| US-08 (AC-08) | ลบ/หมดอายุเอกสาร | Then object, metadata, vector, cache, log ถูกจัดการตาม policy และตรวจสอบได้ |
| US-09 (AC-09) | gate ล้มเหลว | When owner สั่ง rollback Then upload/query ถูกปิดและกลับสู่ `DEMO_ONLY` |
| US-10 (AC-10) | คำตอบอาจมีผลต่อการตัดสินใจสำคัญ | Then ต้องมีมนุษย์ตรวจ และไม่เกิดการกระทำภายนอกอัตโนมัติ |

## 3. Functional requirements

| ID | Requirement | Priority | Phase | สถานะ |
|---|---|---|---|---|
| FR-01 | Health/readiness ที่ไม่ต้องใช้ provider key | Must | Pilot | ผ่าน (local smoke) |
| FR-02 | รับเฉพาะ `.txt`, `.pdf`, `.docx` และแจ้ง error ชัดเจน | Must | Pilot | สร้างแล้ว; unit test ผ่าน |
| FR-03 | รองรับคำถามไทยและอังกฤษกับ corpus ที่กำหนดหนึ่งชุด | Must | Pilot | สร้างแล้ว; ยังไม่ประเมิน |
| FR-04 | คำตอบต้องอิงหลักฐานและมี source/chunk citation | Must | Pilot | สร้างแล้ว; ยังไม่ประเมิน |
| FR-05 | ไม่มีหลักฐาน/ต่ำกว่า threshold ต้องตอบไม่พบและไม่สร้าง citation ปลอม | Must | Pilot | KB ว่างผ่าน; populated ยังไม่รัน |
| FR-06 | คำสั่งในเอกสาร/คำถามต้องไม่ override policy | Must | Pilot | มี boundary test; ยังไม่ประเมิน |
| FR-07 | ตรวจชื่อไฟล์ path ชนิด ขนาด และทรัพยากร | Must | Pilot | สร้างแล้ว (`815d8e7`); security review ค้าง |
| FR-08 | Authentication + single-tenant หรือ tenant isolation ก่อนใช้นอกเดโม | Must | ก่อน staging | ยังไม่มี |
| FR-09 | Data contract ครอบคลุม retention, deletion, backup, restore ก่อนใช้กับลูกค้า | Must | ก่อน staging | เอกสารร่าง; ยังไม่ implement |
| FR-10 | บันทึก latency, cost, failure, evaluation version, release version | Should | Pilot | บางส่วน (field ใน response) |
| FR-11 | ปิด upload/query และกลับสู่ `DEMO_ONLY` ได้เมื่อ gate ล้มเหลว | Must | Pilot | ยังไม่ซ้อม |
| FR-12 | คำตอบที่มีผลทางกฎหมาย/การเงิน/HR ต้องผ่านมนุษย์ และไม่ trigger action อัตโนมัติ | Must | Pilot | นโยบายมี; ยังไม่มี UAT |

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| BA | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Accountable sponsor | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `roles/pilots/ai-doc-assistant/business-requirements.md`, `user-stories.md`, `stakeholder-map.md`
- `operations/ai/AI-DOC-ASSISTANT-PRODUCT-SCOPE.md`
- `engagements/internal/solo-empire/ai-doc-assistant/main.py`, `rag_engine.py`
