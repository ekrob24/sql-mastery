-- SOLUTION 32.2 — Customer base over time
-- (Reveal only after attempting: python3 sqlm.py solution 32.2)

SELECT customer_id,
       signup_date,
       COUNT(*) OVER (ORDER BY signup_date, customer_id
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS customers_to_date
FROM customers
ORDER BY signup_date, customer_id;
