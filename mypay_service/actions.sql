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

SELECT * FROM "V_ORDER_COMPLETE" LIMIT 5;

-- Create error logging table
CREATE TABLE IF NOT EXISTS "TR_ERROR_LOG" (
    id SERIAL PRIMARY KEY,
    error_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    procedure_name VARCHAR(100),
    error_message TEXT,
    error_details TEXT,
    user_id INTEGER,
    additional_data JSONB
);

CREATE OR REPLACE PROCEDURE topup_mypay_balance(
    p_user_id INTEGER,
    p_amount NUMERIC(10,2),
    OUT p_new_balance NUMERIC(10,2)
) AS $$
BEGIN
    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Top-up amount must be positive';
    END IF;

    BEGIN
        -- Update balance
        UPDATE "TR_MYPAY_BALANCE"
        SET balance = balance + p_amount
        WHERE userid = p_user_id
        RETURNING balance INTO p_new_balance;

        -- Log transaction
        INSERT INTO "TR_MYPAY_TRANSACTION" (
            sender_id,
            receiver_id,
            amount,
            transaction_type,
            transaction_date
        ) VALUES (
            p_user_id,
            p_user_id,
            p_amount,
            'TOPUP',
            CURRENT_TIMESTAMP
        );

    EXCEPTION WHEN OTHERS THEN
        INSERT INTO "TR_ERROR_LOG" (
            procedure_name,
            error_message,
            error_details,
            user_id,
            additional_data
        ) VALUES (
            'topup_mypay_balance',
            SQLERRM,
            SQLSTATE,
            p_user_id,
            jsonb_build_object('amount', p_amount)
        );
        RAISE;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE transfer_mypay_balance(
    p_sender_id INTEGER,
    p_receiver_id INTEGER,
    p_amount NUMERIC(10,2),
    OUT p_new_balance NUMERIC(10,2)
) AS $$
BEGIN
    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive';
    END IF;

    -- Check sufficient balance
    IF NOT EXISTS (
        SELECT 1 FROM "TR_MYPAY_BALANCE"
        WHERE userid = p_sender_id AND balance >= p_amount
    ) THEN
        RAISE EXCEPTION 'Insufficient balance';
    END IF;

    BEGIN
        -- Update sender balance
        UPDATE "TR_MYPAY_BALANCE"
        SET balance = balance - p_amount
        WHERE userid = p_sender_id
        RETURNING balance INTO p_new_balance;

        -- Update receiver balance
        UPDATE "TR_MYPAY_BALANCE"
        SET balance = balance + p_amount
        WHERE userid = p_receiver_id;

        -- Log transaction
        INSERT INTO "TR_MYPAY_TRANSACTION" (
            sender_id,
            receiver_id,
            amount,
            transaction_type,
            transaction_date
        ) VALUES (
            p_sender_id,
            p_receiver_id,
            p_amount,
            'TRANSFER',
            CURRENT_TIMESTAMP
        );

    EXCEPTION WHEN OTHERS THEN
        INSERT INTO "TR_ERROR_LOG" (
            procedure_name,
            error_message,
            error_details,
            user_id,
            additional_data
        ) VALUES (
            'transfer_mypay_balance',
            SQLERRM,
            SQLSTATE,
            p_sender_id,
            jsonb_build_object(
                'receiver_id', p_receiver_id,
                'amount', p_amount
            )
        );
        RAISE;
    END;
END;
$$ LANGUAGE plpgsql;

