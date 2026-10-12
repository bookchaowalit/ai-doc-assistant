---
title: AI Doc Assistant — User Flow และ Screen Inventory
doc_id: ADA-DOC-06
doc_type: ux-flows
version: 0.1
date: 2026-10-07
status: ร่างเพื่อพิจารณา
owner: UX/UI (AI Product Delivery)
related: 05-srs.md, 07-test-uat.md, 08-rtm.md
---

# 06 — User Flow และ Screen Inventory

## 1. รายการหน้าจอ

ระบบมีหน้า UI เดียว (`static/index.html` เสิร์ฟที่ `/`) แบ่งเป็นส่วน ๆ และหน้า Swagger ของ FastAPI

| ID | หน้าจอ/ส่วน | Element หลัก | บทบาท | สถานะ |
|---|---|---|---|---|
| SC-01 | Header + สถิติ KB | หัวเรื่อง "RAG-as-a-Service", `#stats` | Operator | สร้างแล้ว |
| SC-02 | ส่วนอัปโหลดเอกสาร | `#file-input` (accept `.pdf,.docx,.txt`), `#upload-status` | Operator | สร้างแล้ว |
| SC-03 | Welcome + คำถามตัวอย่าง | `#welcome`, ปุ่มตัวอย่าง 3 ปุ่ม (อังกฤษ 1, ไทย 2) | Operator | สร้างแล้ว |
| SC-04 | แชตถาม-ตอบ | `#chat`, `#question` (placeholder "พิมพ์คำถาม..."), ปุ่ม `#send-btn` "ถาม"; แสดงคำตอบ แหล่งอ้างอิง และ metrics | Operator | สร้างแล้ว |
| SC-05 | Swagger UI | `/docs` | ผู้ดูแล/นักพัฒนา | มีจาก FastAPI |

## 2. User flow หลัก

```mermaid
flowchart TD
  A["เปิด / (SC-01)"] --> B["เลือกไฟล์ (SC-02)"]
  B --> C{"ชนิด/ขนาด/ชื่อไฟล์ถูกต้อง?"}
  C -->|"ไม่"| C1["แสดง error 400/413/415"]
  C -->|"ใช่"| D{"มี provider key?"}
  D -->|"ไม่"| D1["แสดง 503 provider ไม่ได้ตั้งค่า"]
  D -->|"ใช่"| E["แสดงจำนวน chunk ที่สร้าง"]
  E --> F["พิมพ์คำถามหรือกดตัวอย่าง (SC-03/SC-04)"]
  F --> G{"พบหลักฐาน?"}
  G -->|"ไม่"| G1["ตอบไม่พบ grounded=false"]
  G -->|"ใช่"| H["คำตอบ + แหล่งอ้างอิง + latency/cost"]
  H --> I["ผู้ตรวจ (มนุษย์) ทบทวนก่อนนำไปใช้"]
```

## 3. Design system / Component

- HTML/CSS/JS ไฟล์เดียว ไม่มี framework; UI ภาษาไทยเป็นหลักพร้อมตัวอย่างภาษาอังกฤษ
- Safety ของ UI: คำถาม คำตอบ metadata ของ citation และ error ถูก render เป็น text (กัน XSS) และกันการกดส่งซ้ำ — ตรวจด้วย `test_ui_safety.cjs`
- รองรับ mobile ผ่าน `enterkeyhint="send"` ในช่องคำถาม; การออกแบบ responsive โดยละเอียด **[ต้องยืนยัน]**
- `README.md` เคยวางแผน Next.js chat UI แต่เลือกใช้ inline HTML แทน
- ยังไม่มีหน้าจอ login, จัดการเอกสาร (ลบ/ดูรายการ) หรือ dashboard analytics

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| UX/UI (AI Product Delivery) | ร่างเพื่อพิจารณา | 2026-10-07 | ________ |
| Product owner | รอพิจารณา | ________ | ________ |

## แหล่งข้อมูล

- `engagements/internal/solo-empire/ai-doc-assistant/static/index.html`, `main.py`, `README.md`, `test_ui_safety.cjs`
- `roles/pilots/ai-doc-assistant/research-and-design-handoff.md`
