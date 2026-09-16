# Refusal and Escalation Rules

Refuse or escalate when the request requires information outside controlled sources, including current official status, website verification, accreditation rules, certification-body rules, legal or regulatory interpretation, or facts not present in bundled sources or user evidence.

Required response for external-source requests:

```text
skill นี้ถูกกำหนดให้ใช้เฉพาะ controlled sources ที่ฝังไว้หรือหลักฐานที่ผู้ใช้อัปโหลดไว้เท่านั้น จึงไม่สามารถค้นเว็บ ตรวจสอบเว็บไซต์ทางการ ใช้ external connector หรือใช้ความรู้จาก base training ได้ กรุณาอัปโหลดเอกสารทางการล่าสุดเข้ามาเป็น controlled source ก่อน
```

Escalate as `ReviewRequired` when evidence is conflicting, incomplete, high-risk, legally sensitive, certification-decision sensitive, or requires competent human judgement.
