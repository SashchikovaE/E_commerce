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

=============================================================================
Вычисляем, есть ли в таблице customers и sellers такие значения зип кода, которых нет в таблице geolocation
=============================================================================

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

==============================================================================
Так как мы обнаружили, что есть такие экземпляры (278 и 7), мы должны записать данные в новую таблицу из всех трех
==============================================================================

CREATE TABLE zip_code(
	zip_code_prefix VARCHAR(5) PRIMARY KEY
);
INSERT INTO zip_code (zip_code_prefix)
SELECT DISTINCT geolocation_zip_code_prefix
FROM olist_geolocation_dataset
WHERE geolocation_zip_code_prefix IS NOT NULL
UNION
SELECT DISTINCT customer_zip_code_prefix
FROM olist_customers_dataset
WHERE customer_zip_code_prefix IS NOT NULL
UNION
SELECT DISTINCT seller_zip_code_prefix
FROM olist_sellers_dataset
WHERE seller_zip_code_prefix IS NOT NULL
ON CONFLICT (zip_code_prefix) DO NOTHING;

====================================================================================
Обнаружила, что на автомате некоторые столбцы опредедлилсь типом данных integer, а так как значения этого столбца начинались с нулей, эти нули автоматически исчезли, поэтому нужно заполнить значения нулями спереди, где это необходимо и изменить тип данных на varchar
====================================================================================

ALTER TABLE zip_code
ADD COLUMN zip_code_prefix_new VARCHAR(5);
UPDATE zip_code
SET zip_code_prefix_new = LPAD(zip_code_prefix, 5, '0');
ALTER TABLE zip_code
DROP COLUMN zip_code_prefix;
ALTER TABLE zip_code
RENAME COLUMN zip_code_prefix_new TO zip_code_prefix;

ALTER TABLE olist_geolocation_dataset
ADD COLUMN geolocation_zip_code_prefix_new VARCHAR(5);
UPDATE olist_geolocation_dataset
SET geolocation_zip_code_prefix_new = LPAD(geolocation_zip_code_prefix::TEXT, 5, '0');
ALTER TABLE olist_geolocation_dataset
DROP COLUMN geolocation_zip_code_prefix;
ALTER TABLE olist_geolocation_dataset
RENAME COLUMN geolocation_zip_code_prefix_new TO geolocation_zip_code_prefix;

ALTER TABLE olist_customers_dataset
ADD COLUMN customer_zip_code_prefix_new VARCHAR(5);
UPDATE olist_customers_dataset
SET customer_zip_code_prefix_new = LPAD(customer_zip_code_prefix::TEXT, 5, '0');
ALTER TABLE olist_customers_dataset
DROP COLUMN customer_zip_code_prefix;
ALTER TABLE olist_customers_dataset
RENAME COLUMN customer_zip_code_prefix_new TO customer_zip_code_prefix;


ALTER TABLE olist_sellers_dataset
ADD COLUMN seller_zip_code_prefix_new VARCHAR(5);
UPDATE olist_sellers_dataset
SET seller_zip_code_prefix_new = LPAD(seller_zip_code_prefix::TEXT, 5, '0');
ALTER TABLE olist_sellers_dataset
DROP COLUMN seller_zip_code_prefix;
ALTER TABLE olist_sellers_dataset
RENAME COLUMN seller_zip_code_prefix_new TO seller_zip_code_prefix;

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

=======================================
Продолжаем связывать оставшиеся таблицы
=======================================

ALTER TABLE zip_code
ADD PRIMARY KEY (zip_code_prefix);

ALTER TABLE olist_geolocation_dataset
ADD CONSTRAINT fk_geolocation_zip_code_prefix
FOREIGN KEY (geolocation_zip_code_prefix)
REFERENCES zip_code(zip_code_prefix);

ALTER TABLE olist_customers_dataset
ADD CONSTRAINT fk_customer_zip_code_prefix
FOREIGN KEY (customer_zip_code_prefix)
REFERENCES zip_code(zip_code_prefix);

ALTER TABLE olist_sellers_dataset
ADD CONSTRAINT fk_seller_zip_code_prefix
FOREIGN KEY (seller_zip_code_prefix)
REFERENCES zip_code(zip_code_prefix)

============
Заменяем пустые строки на NULL
========================

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
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    s.seller_city,
    s.seller_state,
    oi.price,
    oi.freight_value,
    p.product_category_name,
    p.product_weight_g,
    op.payment_type,
    op.payment_installments,
    op.payment_value,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    ore.review_score,
    ore.review_comment_message
FROM olist_orders_dataset o
LEFT JOIN olist_customers_dataset c USING(customer_id)
LEFT JOIN olist_order_items_dataset oi USING(order_id)
LEFT JOIN olist_products_dataset p USING(product_id)
LEFT JOIN olist_order_payments_dataset op USING(order_id)
LEFT JOIN olist_order_reviews_dataset ore USING(order_id)
LEFT JOIN olist_sellers_dataset s USING(seller_id)
