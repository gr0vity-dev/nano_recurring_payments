import os
import json
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors


class Postgres:

    _conn = None
    _cursor = None
    _config = None


    error_messages = {"rp_exists" : "A recurring payment already exists for that destination" }
    payment_status = [ None, "INITIATED","CONFIRMED", "RECEIVABLE", "FAILED" ]

    def __init__(self):    
        with open("./cron_config.json") as json_data_file:
            self._config = json.load(json_data_file)

        self._conn = self.new_conn(isolation_level=0)
        self._conn.set_session(autocommit=True)
        self._cursor = self._conn.cursor()
        # postgresql_cursor.execute(create_account_stats)

    def get_cursor(self) :
        return self._conn.cursor()
    
    def new_conn(self, isolation_level=1):
        postgresql_config = self._config["postgresql"]["connection"]
        conn = psycopg2.connect(
            "host={} port={} dbname={} user={} password={}".format(
                postgresql_config["host"],
                postgresql_config["port"],
                postgresql_config["dbname"],
                postgresql_config["user"],
                postgresql_config["password"],
            )
        )
        conn.set_isolation_level(isolation_level)
        return conn
    

    def format_sql_exception(self, err):
        # print the pgcode and pgerror exceptions
        msg = "An error occured"
        if err.pgerror.count("duplicate key value violates unique constraint") > 0:
            msg = self.error_messages["rp_exists"]

        return { "success" : False,
                 "error_message" : msg,
                 "sql_error_code": err.pgcode    }

    def format_sql_response(self, cursor, as_array = False):
        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = [dict(zip(column_names, row))  
        for row in cursor] 

        if len(data) == 1 and as_array == True:
            data = data[0]

        return data
       
    def update_payment_is_due(self):
        q = """ 
            UPDATE recurring_payments
            SET
            datetime_updated  = now() ,
            last_paid_date = next_pay_date,
            next_pay_date = next_pay_date + CONCAT(payment_interval, ' ', payment_period )::INTERVAL,
            status_e = 'INITIATED'
            WHERE next_pay_date < now()
            AND (status_e is null OR status_e = 'CONFIRMED')
            AND rp_end_date = '0001-01-01'
            AND is_enabled = true
            AND is_deleted = false  
            """
        return q
    
    def select_active_payments_by_state(self):
        q = """
            SELECT seed_hash                           ,
                    seed_enc                           ,
                    seed_index                         ,
                    source_address                     ,
                    destination_address                ,
                    payment_interval                   ,
                    payment_period                     ,
                    payment_amount                     ,
                    payment_currency                   ,
                    last_tx_hash                       ,
                    first_pay_date                     ,
                    next_pay_date                      ,
                    is_deleted                         ,
                    is_enabled                         ,
                    created_by                         ,
                    datetime_created                   ,
                    datetime_updated                   ,
                    rp_end_date                        
            FROM recurring_payments 
            WHERE status_e = %s
            AND rp_end_date = '0001-01-01'
            AND is_enabled = true
            AND is_deleted = false        
        """
        return q
    
    def update_payment_status_by_source_destination(self, hash = False):  
        set_hash = "" 
        if hash == True : set_hash = f"last_tx_hash = %s,"  
        q = f"""
            UPDATE recurring_payments
            SET 
            {set_hash}
            datetime_updated  = now() ,            
            status_e = %s            
            WHERE source_address = %s
            AND destination_address = %s
            AND rp_end_date = '0001-01-01'
            AND is_enabled = true
            AND is_deleted = false       
        """
        return q
    
    def insert_payout(self):
        q = """
            INSERT INTO recurring_payouts
            (seed_hash,seed_index,source_address,destination_address,tx_hash,
             payment_amount_raw,payment_amount,payment_currency,created_by,
             datetime_created,datetime_updated)
            VALUES
            (%s,%s,%s,%s,%s,
             %s,%s,%s,%s, 
             now(), now())
        """
        return q

    
    
