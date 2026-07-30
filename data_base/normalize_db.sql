=======================
Добавляем внешние ключи
=======================
ALTER TABLE olist_order_payments_dataset
ADD CONSTRAINT fk_order_id_payments
FOREIGN KEY (order_id)
REFERENCES olist_orders_dataset(order_id)

ALTER TABLE olist_products_dataset
ADD PRIMARY KEY (product_id);
ALTER TABLE olist_order_items_dataset
ADD CONSTRAINT fk_product_id
FOREIGN KEY (product_id)
REFERENCES olist_products_dataset(product_id)

ALTER TABLE product_category_name_translation
ADD PRIMARY KEY (product_category_name)
ALTER TABLE olist_products_dataset
ADD CONSTRAINT fk_product_category_name
FOREIGN KEY (product_category_name)
REFERENCES product_category_name_translation(product_category_name)

===============================================================
Проверяем, хранит ли в себе столбец geolocation_zip_code_prefix
из таблицы olist_geolocation_dataset уникальные значения
===============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT geolocation_zip_code_prefix) AS unique_values,
    COUNT(*) - COUNT(DISTINCT geolocation_zip_code_prefix) AS duplicates_count
FROM olist_geolocation_dataset;

===========================================================================
Вычисляем, есть ли в таблице customers и sellers такие значения зип кода,
которых нет в таблице geolocation, и сколько их (278 customers и 7 sellers)
===========================================================================

SELECT COUNT(*) 
FROM olist_customers_dataset c
LEFT JOIN olist_geolocation_dataset g 
    ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
WHERE g.geolocation_zip_code_prefix IS NULL;

SELECT COUNT(*) 
FROM olist_sellers_dataset s
LEFT JOIN olist_geolocation_dataset g 
    ON s.seller_zip_code_prefix = g.geolocation_zip_code_prefix
WHERE g.geolocation_zip_code_prefix IS NULL;

===================================================================
Создаем новую таблицу с данными из старой olist_geolocation_dataset
и добавляем первичный ключ
===================================================================

CREATE TABLE olist_zip_geo_dataset AS
SELECT
	geolocation_zip_code_prefix,
	AVG(geolocation_lat) AS lat,
	AVG(geolocation_lng) AS lng,
	MAX(geolocation_city) AS city,
	MAX(geolocation_state) AS geo_state
FROM olist_geolocation_dataset
GROUP BY geolocation_zip_code_prefix

ALTER TABLE olist_zip_geo_dataset
ADD PRIMARY KEY (geolocation_zip_code_prefix)

============================================================================
Проверяем, какие вообще значения хранятся в зип кодах у customers и sellers,
которых нет в главной таблице
============================================================================

SELECT geolocation_zip_code_prefix
FROM olist_zip_geo_dataset
ORDER BY geolocation_zip_code_prefix
DESC LIMIT 20;

==================================================================
Так как зип коды выглядят реалистично, то скорее всего, они просто
не внесены в таблицу olist_zip_geo_dataset, исправим это
==================================================================

INSERT INTO olist_zip_geo_dataset (geolocation_zip_code_prefix, city, geo_state, lat, lng)
SELECT DISTINCT
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    (SELECT AVG(lat) FROM olist_zip_geo_dataset WHERE city = c.customer_city) AS avg_lat,
    (SELECT AVG(lng) FROM olist_zip_geo_dataset WHERE city = c.customer_city) AS avg_lng
FROM olist_customers_dataset c
WHERE c.customer_zip_code_prefix NOT IN (
    SELECT geolocation_zip_code_prefix
    FROM olist_zip_geo_dataset
);


INSERT INTO olist_zip_geo_dataset (geolocation_zip_code_prefix, city, geo_state, lat, lng)
SELECT DISTINCT
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    (SELECT AVG(lat) FROM olist_zip_geo_dataset WHERE city = s.seller_city) AS avg_lat,
    (SELECT AVG(lng) FROM olist_zip_geo_dataset WHERE city = s.seller_city) AS avg_lng
FROM olist_sellers_dataset s
WHERE s.seller_zip_code_prefix NOT IN (
    SELECT geolocation_zip_code_prefix
    FROM olist_zip_geo_dataset
);

============================================================================================
Связываем таблицы customers и sellers с новой нормализованной таблицей olist_zip_geo_dataset
============================================================================================

ALTER TABLE olist_customers_dataset
ADD CONSTRAINT fk_customer_zip_code_prefix
FOREIGN KEY (customer_zip_code_prefix)
REFERENCES olist_zip_geo_dataset(geolocation_zip_code_prefix);

ALTER TABLE olist_sellers_dataset
ADD CONSTRAINT fk_seller_zip_code_prefix
FOREIGN KEY (seller_zip_code_prefix)
REFERENCES olist_zip_geo_dataset(geolocation_zip_code_prefix);

========================================================================
Удаляем лишние столбцы из таблиц customers и sellers, так как информация
об этих столбцах уже есть в таблице olist_zip_geo_dataset
========================================================================

ALTER TABLE olist_customers_dataset
DROP COLUMN IF EXISTS customer_city,
DROP COLUMN IF EXISTS customer_state;

ALTER TABLE olist_sellers_dataset
DROP COLUMN IF EXISTS seller_city,
DROP COLUMN IF EXISTS seller_state;

========================================
Продолжаем менять типы данных в таблицах
========================================

ALTER TABLE olist_orders_dataset
MODIFY COLUMN order_purchase_timestamp TIMESTAMP,

ALTER TABLE olist_orders_dataset
MODIFY COLUMN order_delivered_carrier_date TIMESTAMP,

ALTER TABLE olist_orders_dataset
MODIFY COLUMN order_delivered_customer_date TIMESTAMP,

ALTER TABLE olist_orders_dataset
MODIFY COLUMN order_estimated_delivery_date TIMESTAMP

==============================
Заменяем пустые строки на NULL
==============================

UPDATE olist_orders_dataset
SET order_purchase_timestamp = NULL
WHERE order_purchase_timestamp = ' ';

UPDATE olist_orders_dataset
SET order_delivered_carrier_date = NULL
WHERE order_delivered_carrier_date = ' ';

UPDATE olist_orders_dataset
SET order_approved_at = NULL
WHERE order_approved_at = ' ';

UPDATE olist_orders_dataset
SET order_delivered_customer_date = NULL
WHERE order_delivered_customer_date = ' ';

UPDATE olist_orders_dataset
SET order_estimated_delivery_date = NULL
WHERE order_estimated_delivery_date = ' '

========================================
Меняем тип данных с VARCHAR на TIMESTAMP
========================================

ALTER TABLE olist_orders_dataset
ALTER COLUMN order_purchase_timestamp TYPE TIMESTAMP
USING order_purchase_timestamp::TIMESTAMP;

ALTER TABLE olist_orders_dataset
ALTER COLUMN order_approved_at TYPE TIMESTAMP
USING order_approved_at::TIMESTAMP;

ALTER TABLE olist_orders_dataset
ALTER COLUMN order_delivered_carrier_date TYPE TIMESTAMP
USING order_delivered_carrier_date::TIMESTAMP;

ALTER TABLE olist_orders_dataset
ALTER COLUMN order_delivered_customer_date TYPE TIMESTAMP
USING order_delivered_customer_date::TIMESTAMP;

ALTER TABLE olist_orders_dataset
ALTER COLUMN order_estimated_delivery_date TYPE TIMESTAMP
USING order_estimated_delivery_date::TIMESTAMP;

ALTER TABLE olist_order_items_dataset
ALTER COLUMN shipping_limit_date TYPE TIMESTAMP
USING shipping_limit_date::TIMESTAMP;

ALTER TABLE olist_order_reviews_dataset
ALTER COLUMN review_creation_date TYPE TIMESTAMP
USING review_creation_date::TIMESTAMP;

ALTER TABLE olist_order_reviews_dataset
ALTER COLUMN review_answer_timestamp TYPE TIMESTAMP
USING review_answer_timestamp::TIMESTAMP

=============================================================
Объединяем таблицы в одну для задачи рекомендательной системы
=============================================================

CREATE VIEW orders_master AS
SELECT 
    o.order_id,
    c.customer_unique_id,
	zc.city AS customer_city,
	zc.state AS customer_state,
	zc.lat AS customer_lat,
	zc.lng AS customer_lng,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    oi.order_item_id,
    p.product_category_name,
	p.product_name_lenght,
	p.product_description_lenght,
    p.product_weight_g,
	p.product_length_cm,
	p.product_height_cm,
	p.product_width_cm,
	zs.city AS seller_city,
	zs.state AS seller_state,
	zs.lat AS seller_lat,
	zs.lng AS seller_lng,
	oi.shipping_limit_date,
    oi.price,
    oi.freight_value,
	op.payment_sequential,
    op.payment_type,
    op.payment_installments,
    op.payment_value AS total_payment,
    ore.review_score,
	ore.review_comment_title,
    ore.review_comment_message,
	ore.review_creation_date,
	ore.review_answer_timestamp
FROM olist_orders_dataset o
LEFT JOIN olist_customers_dataset c ON o.customer_id = c.customer_id
LEFT JOIN olist_order_items_dataset oi ON o.order_id = oi.order_id
LEFT JOIN olist_products_dataset p ON oi.product_id = p.product_id
LEFT JOIN olist_sellers_dataset s ON oi.seller_id = s.seller_id
LEFT JOIN olist_order_payments_dataset op ON o.order_id = op.order_id
LEFT JOIN olist_order_reviews_dataset ore ON o.order_id = ore.order_id
LEFT JOIN olist_zip_geo_dataset zc ON c.customer_zip_code_prefix = zc.geolocation_zip_code_prefix
LEFT JOIN olist_zip_geo_dataset zs ON s.seller_zip_code_prefix = zs.geolocation_zip_code_prefix


