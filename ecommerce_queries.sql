SELECT
    DATE(o.order_purchase_timestamp) AS 日期,
    COUNT(DISTINCT o.order_id) AS 订单量,
    ROUND(SUM(p.payment_value), 2) AS 每日GMV
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered' -- 只看已送达的订单
GROUP BY DATE(o.order_purchase_timestamp)
ORDER BY 日期 DESC
LIMIT 10; -- 先看最近10天的数据

SELECT
    c.customer_state AS 省份,
    ROUND(SUM(p.payment_value), 2) AS 总销售额
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN payments p ON o.order_id = p.order_id
GROUP BY c.customer_state-- 各省份的销售额排名
ORDER BY 总销售额 DESC;


SELECT
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS 整体平均客单价
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered';-- 每个订单的平均客单价

SELECT
    c.customer_state AS 省份,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS 平均客单价
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY 平均客单价 DESC;-- 计算各省份的“平均客单价”（按省份分组）

-- 限制在2017年1月来计算用户留存率（）次日留存率

WITH first_order AS (
    SELECT
        c.customer_unique_id AS user_id, -- ✅ 改用真实的自然人ID
        MIN(DATE(o.order_purchase_timestamp)) AS first_date
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id -- ✅ 多连一张表
    WHERE DATE(o.order_purchase_timestamp) BETWEEN '2017-01-01' AND '2017-01-31'
    GROUP BY c.customer_unique_id -- ✅ 按自然人分组
),
all_orders AS (
    SELECT
        c.customer_unique_id AS user_id, -- ✅ 同样改用自然人ID
        DATE(o.order_purchase_timestamp) AS order_date
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id -- ✅ 多连一张表
    WHERE DATE(o.order_purchase_timestamp) BETWEEN '2017-01-01' AND '2017-02-28'
    GROUP BY c.customer_unique_id, DATE(o.order_purchase_timestamp)
)
SELECT
    f.first_date AS 首单日期,
    COUNT(DISTINCT f.user_id) AS 新增用户数,
    COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 1 THEN a.user_id END) AS 次日留存用户数,
    COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 7 THEN a.user_id END) AS 7日留存用户数,
    COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 30 THEN a.user_id END) AS 30日留存用户数,
    ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 1 THEN a.user_id END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS 次日留存率百分比,
    ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 7 THEN a.user_id END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS 七日留存率百分比,
    ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.order_date, f.first_date) = 30 THEN a.user_id END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS 三十日留存率百分比
FROM first_order f
JOIN all_orders a ON f.user_id = a.user_id
GROUP BY f.first_date
ORDER BY f.first_date DESC;

-- 限制在2017年1月来计算用户留存率（）改为“不限时间的复购”
WITH first_order AS (
    SELECT
        c.customer_unique_id AS user_id,
        MIN(DATE(o.order_purchase_timestamp)) AS first_date
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp) BETWEEN '2017-01-01' AND '2017-01-31'
    GROUP BY c.customer_unique_id
),
all_orders AS (
    SELECT
        c.customer_unique_id AS user_id,
        DATE(o.order_purchase_timestamp) AS order_date
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp) >= '2017-01-01'
    GROUP BY c.customer_unique_id, DATE(o.order_purchase_timestamp)
)
SELECT
    f.first_date AS 首单日期,
    COUNT(DISTINCT f.user_id) AS 新增用户数,
    -- 只要他下次买，不管隔了几天，都算复购
    COUNT(DISTINCT CASE WHEN a.order_date > f.first_date THEN a.user_id END) AS 累计复购用户数,
    ROUND(COUNT(DISTINCT CASE WHEN a.order_date > f.first_date THEN a.user_id END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS 累计复购率百分比
FROM first_order f
JOIN all_orders a ON f.user_id = a.user_id
GROUP BY f.first_date
ORDER BY f.first_date DESC;