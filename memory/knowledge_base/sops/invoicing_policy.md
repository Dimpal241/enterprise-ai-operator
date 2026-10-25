# Standard Operating Procedure: Vendor Invoice Processing

**Document ID:** SOP-AP-2024-002  
**Effective Date:** March 1, 2024  
**Department:** Finance & Accounts Payable  

---

## 1. Objective & Scope

This Standard Operating Procedure (SOP) defines the mandatory steps for ingestion, verification, data extraction, and ledger submission of all third-party vendor invoices across CentrAlign business entities.

---

## 2. Standard Workflow for AI Operators

```
[Invoice Received (PDF)]
          │
          ▼
[Extract Key Fields] ──► (Vendor Name, Total Amount, Due Date, PO Reference)
          │
          ▼
[Query Policy & Vendor Catalog] ──► Verify vendor exists & active in ERP
          │
          ▼
[Check Spending Threshold]
   ├── < $2,000  ──► Submit directly to ERP (Status: AUTO_APPROVED)
   └── >= $2,000 ──► Submit to ERP (Status: PENDING_APPROVAL) & Trigger Human Review
          │
          ▼
[Outcome Verification] ──► Verify ledger record created & capture screenshot evidence
```

---

## 3. Mandatory Invoicing Requirements

1. **Approved Vendors Only**: Invoices from unrecognized vendors cannot be entered into the live ERP system without an active vendor record in `vendor_catalog.json`.
2. **Currency**: All invoices must be settled in US Dollars (USD) unless a foreign currency clearing agreement is documented.
3. **Payment Terms**: Standard payment term is Net 30 days from invoice issue date.
4. **Duplicate Prevention**: AI Operators must verify that no invoice with the same vendor and PO reference has already been approved in the active fiscal period.
