--4294967295  max Nano index

DROP TABLE IF EXISTS recurring_payments ;
CREATE TABLE recurring_payments (
    seed_enc            character varying(256) DEFAULT NULL::character varying, 
    seed_hash           character varying(65) DEFAULT NULL::character varying, 
    seed_index          numeric(10) DEFAULT 0, 
    source_address      character varying(65) DEFAULT NULL::character varying, 
    destination_address character varying(65) DEFAULT NULL::character varying, 
    payment_interval    smallint DEFAULT 1,
    payment_period      character varying(6) check (payment_period in ('day','week','month', 'year', 'hour')),
    payment_amount      numeric(39, 6) DEFAULT NULL::numeric ,
    payment_currency    character varying(12) DEFAULT NULL::character varying,
    first_pay_date      TIMESTAMPTZ,
    next_pay_date       TIMESTAMPTZ, 
    last_paid_date      TIMESTAMPTZ,
    last_tx_hash        character varying(65) DEFAULT NULL::character varying,
    rp_end_date         TIMESTAMPTZ,
    is_deleted          boolean NOT NULL DEFAULT FALSE,
    is_enabled          boolean NOT NULL DEFAULT TRUE,
    status_e            character varying(12) DEFAULT NULL::character varying, 
    payment_count       numeric(10) DEFAULT 0,
    created_by          character varying(12) DEFAULT NULL::character varying, 
    datetime_created    TIMESTAMPTZ,
    datetime_updated    TIMESTAMPTZ,
    PRIMARY KEY (seed_hash, seed_index, source_address, destination_address, rp_end_date) --rp_end_date is used so that a new rp can be created after it has been disabled
);
CREATE INDEX recurring_payments_seed_enc ON recurring_payments USING btree(seed_enc);
CREATE INDEX recurring_payments_source_address ON recurring_payments USING btree(source_address);
CREATE INDEX recurring_payments_destination_address ON recurring_payments USING btree(destination_address);
CREATE INDEX recurring_payments_is_enabled ON recurring_payments USING btree(is_enabled);
CREATE INDEX recurring_payments_is_deleted ON recurring_payments USING btree(is_deleted);
CREATE INDEX recurring_payments_next_pay_date ON recurring_payments USING btree(next_pay_date);
CREATE INDEX recurring_payments_last_paid_date ON recurring_payments USING btree(last_paid_date);
CREATE INDEX recurring_payments_status_e ON recurring_payments USING btree(status_e);
CREATE INDEX recurring_payments_last_tx_hash ON recurring_payments USING btree(last_tx_hash);




DROP TABLE IF EXISTS recurring_payouts ;
CREATE TABLE recurring_payouts (
    --seed_enc            character varying(256) DEFAULT NULL::character varying, 
    seed_hash           character varying(65) DEFAULT NULL::character varying, 
    seed_index          numeric(10) DEFAULT 0, 
    source_address      character varying(65) DEFAULT NULL::character varying, 
    destination_address character varying(65) DEFAULT NULL::character varying, 
    tx_hash             character varying(65) DEFAULT NULL::character varying, 
    payment_amount_raw  numeric(39, 6) DEFAULT NULL::numeric ,
    payment_amount      numeric(39, 6) DEFAULT NULL::numeric ,    
    currency            character varying(12) DEFAULT NULL::character varying, 
    created_by          character varying(12) DEFAULT NULL::character varying, 
    datetime_created    TIMESTAMPTZ,
    datetime_updated    TIMESTAMPTZ
);
CREATE INDEX recurring_payouts_seed_hash ON recurring_payouts USING btree(seed_hash);
CREATE INDEX recurring_payouts_source_address ON recurring_payouts USING btree(source_address);
CREATE INDEX recurring_payouts_destination_address ON recurring_payouts USING btree(destination_address);
CREATE INDEX recurring_payouts_tx_hash ON recurring_payouts USING btree(tx_hash);
CREATE INDEX recurring_payouts_currency ON recurring_payouts USING btree(currency);



CREATE USER nano_rp WITH ENCRYPTED PASSWORD 'password';
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public 
TO nano_rp