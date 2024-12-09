-- Create or replace the function for voucher validation
CREATE OR REPLACE FUNCTION voucher_validation()
RETURNS TRIGGER AS $$
DECLARE
    voucher_usage INT;
    voucher_limit INT;
    voucher_expiration DATE;
BEGIN
    IF NEW.discountcode IS NOT NULL THEN
        -- Get the voucher usage record for this user and voucher
        SELECT alreadyuse
        INTO voucher_usage
        FROM TR_VOUCHER_PAYMENT
        WHERE customerid = NEW.customerid AND voucherid = NEW.discountcode;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Voucher % not purchased by user.', NEW.discountcode;
        END IF;

        -- Check expiration date
        SELECT expirationdate
        INTO voucher_expiration
        FROM VOUCHER
        WHERE code = NEW.discountcode;

        IF voucher_expiration < CURRENT_DATE THEN
            RAISE EXCEPTION 'Voucher % has expired.', NEW.discountcode;
        END IF;

        -- Get the usage limit from VOUCHER table
        SELECT userquota
        INTO voucher_limit
        FROM VOUCHER
        WHERE code = NEW.discountcode;

        -- If voucher_limit is NOT NULL, check if usage limit exceeded
        IF voucher_limit IS NOT NULL THEN
            IF voucher_usage >= voucher_limit THEN
                RAISE EXCEPTION 'Voucher % usage limit exceeded.', NEW.discountcode;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger for voucher validation
CREATE TRIGGER voucher_validation_trigger
BEFORE INSERT ON TR_SERVICE_ORDER
FOR EACH ROW
EXECUTE FUNCTION voucher_validation();
