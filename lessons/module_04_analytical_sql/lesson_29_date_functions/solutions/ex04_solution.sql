-- SOLUTION 29.4 — How long until a return?
-- (Reveal only after attempting: python3 sqlm.py solution 29.4)

SELECT r.return_id,
       o.order_id,
       o.order_date,
       r.return_date,
       CAST(julianday(r.return_date) - julianday(o.order_date) AS INTEGER) AS days_to_return
FROM returns AS r
JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
JOIN orders      AS o  ON o.order_id       = oi.order_id;

/* Snowflake notes:
DATEDIFF(day, o.order_date, r.return_date) AS days_to_return
*/
