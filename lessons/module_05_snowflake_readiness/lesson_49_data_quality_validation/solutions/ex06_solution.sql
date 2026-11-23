-- SOLUTION 49.6 — Refunds vs. line value
-- (Reveal only after attempting: python3 sqlm.py solution 49.6)

WITH r AS (
    SELECT r.return_id,
           ROUND(oi.quantity * oi.unit_price, 2) AS line_value,
           r.refund_amount
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
)
SELECT return_id,
       line_value,
       refund_amount,
       CASE WHEN refund_amount > line_value THEN 'exceeds'
            WHEN refund_amount < line_value THEN 'partial'
            ELSE 'full' END AS refund_check
FROM r;

/* Snowflake notes:
With NUMBER(10,2) columns Snowflake does exact decimal arithmetic, so the rounding
step is a safeguard rather than a necessity. IFF/CASE for the label is identical.
*/
