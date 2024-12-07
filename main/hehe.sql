CREATE OR REPLACE FUNCTION validate_voucher()
RETURNS TRIGGER AS $$
BEGIN
    -- Declare variables to hold voucher details
    DECLARE 
        v_user_quota INT;
        v_expiration_date DATE;
        v_already_use INT;

    -- Fetch voucher details
    SELECT 
        V.userquota,
        TVP.expirationdate,
        COALESCE(TVP.alreadyuse, 0) AS alreadyuse
    INTO 
        v_user_quota,
        v_expiration_date,
        v_already_use
    FROM VOUCHER V
    LEFT JOIN TR_VOUCHER_PAYMENT TVP 
        ON V.code = TVP.voucherid
    WHERE V.code = NEW.voucherid;

    -- Check if the voucher has expired
    IF CURRENT_DATE > v_expiration_date THEN
        RAISE EXCEPTION 'Error: The voucher has expired.';
    END IF;

    -- Check if the voucher usage limit has been exceeded
    IF v_already_use >= v_user_quota THEN
        RAISE EXCEPTION 'Error: The voucher usage limit has been exceeded.';
    END IF;

    -- If all validations pass, allow the insertion
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Bind the trigger to the TR_SERVICE_ORDER table
CREATE TRIGGER validate_voucher_trigger
BEFORE INSERT ON TR_SERVICE_ORDER
FOR EACH ROW
EXECUTE FUNCTION validate_voucher();
