SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name IN ('TR_ORDER_STATUS', 'ORDER_STATUS')
    AND table_schema = 'public'
ORDER BY 
    table_name,
    ordinal_position;

CREATE OR REPLACE VIEW "V_ORDER_STATUS" AS
SELECT 
    "TR".servicetrid AS transaction_id,
    "TR".statusid AS status_id, 
    "TR".date AS status_change_date,
    "OS".status AS status_name,
    "OS".id AS order_status_id
FROM "TR_ORDER_STATUS" "TR"
LEFT JOIN "ORDER_STATUS" "OS"
    ON "TR".statusid = "OS".id
ORDER BY "TR".date DESC;

-- Verify view
SELECT * FROM "V_ORDER_STATUS" LIMIT 5;

CREATE OR REPLACE VIEW "V_ORDER_COMPLETE" AS 
SELECT 
    "SO".id AS order_id,
    "SO".orderdate AS order_date,
    "SO".servicedate AS service_date,
    "SO".servicetime AS service_time,
    "SO".totalprice AS total_price,
    "SO".customerid AS customer_id,
    "SO".workerid AS worker_id,
    "SO".servicecategoryid AS service_category_id,
    "SO".session,
    "SO".discountcode AS discount_code,
    "SO".paymentmethodid AS payment_method_id,
    "OS".statusid AS status_id,
    "OS".date AS status_date,
    "MP".id AS payment_id,
    "MP".nominal AS payment_amount,
    "MPC".name AS payment_category
FROM "TR_SERVICE_ORDER" "SO"
LEFT JOIN "TR_ORDER_STATUS" "OS" 
    ON "SO".id = "OS".servicetrid
LEFT JOIN "TR_MYPAY" "MP"
    ON "SO".id = "MP".id
LEFT JOIN "TR_MYPAY_CATEGORY" "MPC"
    ON "MP".categoryid = "MPC".id
ORDER BY 
    "SO".orderdate DESC,
    "SO".servicetime DESC;

-- Verify view
SELECT * FROM "V_ORDER_COMPLETE" LIMIT 5;