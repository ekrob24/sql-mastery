-- SOLUTION 25.4 — Sales and refunds ledger by year
-- (Reveal only after attempting: python3 sqlm.py solution 25.4)

SELECT strftime('%Y', o.order_date)          AS activity_year,
       'sale'                                  AS activity_type,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS amount
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY strftime('%Y', o.order_date)
UNION ALL
SELECT strftime('%Y', r.return_date),
       'refund',
       ROUND(-SUM(r.refund_amount), 2)
FROM returns AS r
GROUP BY strftime('%Y', r.return_date);
