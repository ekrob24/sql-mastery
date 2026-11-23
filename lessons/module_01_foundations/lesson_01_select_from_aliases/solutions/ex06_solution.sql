-- SOLUTION 1.6 — Refund ledger with literal columns
-- (Reveal only after attempting: python3 sqlm.py solution 1.6)

SELECT return_id,
       return_date,
       'refund'        AS transaction_type,
       -refund_amount  AS signed_amount
FROM returns;
