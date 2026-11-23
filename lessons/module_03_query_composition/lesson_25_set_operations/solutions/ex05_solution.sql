-- SOLUTION 25.5 — Net cash by year
-- (Reveal only after attempting: python3 sqlm.py solution 25.5)

SELECT activity_year,
       ROUND(SUM(amount), 2) AS net_amount
FROM (SELECT strftime('%Y', o.order_date) AS activity_year,
             i.quantity * i.unit_price    AS amount
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      UNION ALL
      SELECT strftime('%Y', return_date), -refund_amount
      FROM returns) AS ledger
GROUP BY activity_year;
