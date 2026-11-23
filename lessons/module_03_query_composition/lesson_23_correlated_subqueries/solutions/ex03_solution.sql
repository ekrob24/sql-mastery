-- SOLUTION 23.3 — Lines sold below the product's typical price
-- (Reveal only after attempting: python3 sqlm.py solution 23.3)

SELECT x.order_item_id, x.product_id, x.unit_price, x.avg_product_price
FROM (SELECT i.order_item_id,
             i.product_id,
             i.unit_price,
             ROUND((SELECT AVG(i2.unit_price)
                    FROM order_items AS i2
                    JOIN orders AS o2 ON o2.order_id = i2.order_id
                    WHERE o2.order_status IN ('completed', 'shipped', 'returned')
                      AND i2.product_id = i.product_id), 2) AS avg_product_price,
             (SELECT AVG(i2.unit_price)
              FROM order_items AS i2
              JOIN orders AS o2 ON o2.order_id = i2.order_id
              WHERE o2.order_status IN ('completed', 'shipped', 'returned')
                AND i2.product_id = i.product_id) AS raw_avg
      FROM order_items AS i
      JOIN orders AS o ON o.order_id = i.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')) AS x
WHERE x.unit_price < x.raw_avg;
