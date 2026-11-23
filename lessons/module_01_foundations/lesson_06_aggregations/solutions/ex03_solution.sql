-- SOLUTION 6.3 — Refund summary
-- (Reveal only after attempting: python3 sqlm.py solution 6.3)

SELECT COUNT(*)                      AS return_count,
       COUNT(return_reason)          AS returns_with_reason,
       ROUND(SUM(refund_amount), 2)  AS total_refunded,
       ROUND(AVG(refund_amount), 2)  AS avg_refund
FROM returns;
