from datetime import datetime
import os
import json
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors
from datetime import datetime


class Postgres:

    _conn = None
    _cursor = None
    _config = None


    error_messages = {"rp_exists" : "A recurring payment already exists for that destination" }
    payment_status = {"0" : None , "1" : "PENDING", "2": "FAILED"}

    def __init__(self):    
        with open("config.json") as json_data_file:
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
        if desc is None :
            return []        
        column_names = [col[0] for col in desc]
        data = [dict(zip(column_names, row)) 
        for row in cursor]   

        if len(data) == 1 and as_array == True:
            data = data[0]

        return data

    def select_rate_limiter(self) :
        query =  (  """SELECT now() - most_recent_update from                     
                    (SELECT max(t1.datetime_updated) as most_recent_update FROM   
                    (SELECT datetime_updated FROM rate_limiter                    
                    WHERE id = %s                                                
                    UNION ALL                                                     
                    SELECT datetime_updated FROM rate_limiter                     
                    WHERE id = %s ) as t1 ) as t2                      
                    WHERE t2.most_recent_update > NOW() - INTERVAL '8 hours'      """ )
                    #{'nano_address': nano_address, 'ip_address' : ip_address})
        
        return query
    
    def upsert_rate_limiter(self) :
        #ip, type, created_by       
        query =  (  """INSERT INTO rate_limiter 
                    (id, type, counter_updated, created_by, datetime_created, datetime_updated) 
                    VALUES
                    (%s, %s,1,%s,now(),now())
                    ON CONFLICT (id) DO UPDATE SET 
                    counter_updated=rate_limiter.counter_updated + 1, datetime_updated= now()""")
                    #{'id': args[1], 'type' : args[2], 'created_by' : args[3]})
        
        return query
    
    def insert_payout_stats(self) :
        #ip, type, created_by       
        query =   ("""INSERT INTO payout_stats 
                    (nano_address, ip, payout_amount, payout_currency, created_by, datetime_created, datetime_updated) 
                    VALUES
                    (%s, %s,%s,%s,%s,now(),now())""")
                    #(%(nano_address)s, %(ip)s,%(payout_amount)s,%(payout_currency)s,%(created_by)s,now(),now())""",
                    #{'nano_address': args[1], 'ip' : args[2], 'payout_amount' : args[3],'payout_currency' : args[4], 'created_by' : args[5]})
                  
        
        return query

    def insert_account_stats(self) :
        #ip, type, created_by       
        query =    ("""INSERT INTO account_stats
                    (nano_address, ip,account_balance, account_currency, account_action, action_params, created_by, datetime_created, datetime_updated) 
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,now(),now() )""")        
        #           (%(nano_address)s, %(ip)s,%(account_balance)s,%(account_currency)s,%(account_action)s,%(action_params)s,%(created_by)s,now(),now());
               
        return query
    

    def select_payout_stats(self):
        return """ SELECT nano_address, 
                          sum(payout_amount) as payout_amount, 
                          count(*) as payout_count , 
                          sum(payout_amount) / count(*) as avg_payout,
                          max(datetime_updated) as last_payout
                FROM payout_stats 
                WHERE created_by = 'nano_rp'
                GROUP BY nano_address
                HAVING count(*) > 1 AND sum(payout_amount) > 1337
                order by payout_amount DESC
                """
    
    def select_account_stats(self):
        return """SELECT 
                    CASE WHEN account_action = 'init' THEN 'new accounts'
                         WHEN account_action = 'landing' THEN 'returning users'
                         WHEN account_action = 'mooore' THEN 'faucet payouts'
                         WHEN account_action = 'send' THEN 'user send transactions'
                         WHEN account_action = 'donate' THEN 'user donations' END as account_action,
                         count(*), 
                         date_trunc('day', datetime_created) as "Day"
               FROM account_stats 
               GROUP BY account_action , 3
               ORDER BY account_action, 3 ASC
               """


    def select_recurring_payment_all(self):        

        return  self.select_recurring_payment().format("")   

    def select_recurring_payment_one(self):        

        return self.select_recurring_payment().format("AND seed_index = %s")        
        
    
    def select_recurring_payment(self) : 
        return """SELECT 
                    source_address as source,
                    destination_address as destination,
                    CONCAT(payment_interval, ' ', payment_period) as frequency,
                    payment_interval as interval,
                    payment_period as period,
                    cast(payment_amount as double precision) as amount,
                    payment_currency as currency,
                    to_char(first_pay_date, 'YYYY-MM-DD HH24:MI:SS') as first_pay_date,
                    to_char(next_pay_date, 'YYYY-MM-DD HH24:MI:SS') as next_pay_date,
                    to_char(last_paid_date, 'YYYY-MM-DD HH24:MI:SS') as last_paid_date,  
                    ((DATE_PART('day', next_pay_date - now()) * 24 + 
                      DATE_PART('hour', next_pay_date - now())) * 60 +
                      DATE_PART('minute', next_pay_date - now())) * 60 +
                      DATE_PART('second', next_pay_date - now()) as seconds_till_next_payment,                 
                    is_enabled
                  FROM recurring_payments
                  WHERE seed_hash = %s {} 
                  AND is_deleted = false
               """ 

    def select_recurring_payment_by_destination(self):        

        return """SELECT 
                    source_address as source,
                    destination_address as destination,
                    CONCAT(payment_interval, ' ', payment_period) as frequency,
                    cast(payment_amount as double precision) as amount,
                    payment_currency,
                    to_char(first_pay_date, 'YYYY-MM-DD HH24:MI:SS') as first_pay_date,
                    to_char(next_pay_date, 'YYYY-MM-DD HH24:MI:SS') as next_pay_date,
                    to_char(last_paid_date, 'YYYY-MM-DD HH24:MI:SS') as last_paid_date,
                    is_enabled
                  FROM recurring_payments
                  WHERE seed_hash = %s AND destination_address = %s 
                  AND is_deleted = false
               """ 

    def insert_recurring_payment(self) :           
        query =    ("""INSERT INTO recurring_payments
                    (seed_hash,
                     seed_enc                           , 
                     seed_index                         ,
                     source_address                     ,
                     destination_address                ,
                     payment_interval                   ,
                     payment_period                     ,
                     payment_amount                     ,
                     payment_currency                   ,
                     first_pay_date                     ,
                     next_pay_date                      ,                     
                     is_deleted                         ,
                     is_enabled                         ,
                     created_by                         ,
                     datetime_created                   ,
                     datetime_updated                   ,
                     rp_end_date                        )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(), '0001-01-01' )""")        
                   # (%s,%s,%s,%s,%s,%s,%s,%s,%s,to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS'),to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS'),%s,%s,%s,now(),now(), '0001-01-01' )""")        
                 
        return query

    def update_recurring_payment(self) : #possible to reenable          
        query =    """UPDATE recurring_payments
                     SET                     
                     source_address    = %s                                        ,
                     payment_interval  = %s                                        ,
                     payment_period    = %s                                        ,
                     payment_amount    = %s                                        ,                      
                     payment_currency  = %s                                        ,
                     first_pay_date    = %s                                        ,
                     next_pay_date     = %s                                        ,              
                     is_deleted        = %s                                        ,
                     is_enabled        = %s                                        ,
                     created_by        = %s                                        ,
                     datetime_updated  = now()                                     ,
                     rp_end_date       = '0001-01-01'
                     WHERE seed_hash = %s 
                     AND seed_index = %s
                     AND destination_address = %s
                     AND is_deleted = false """
                    
        return query

    def disable_recurring_payment(self) :   
           
        query =    """UPDATE recurring_payments
                       SET is_enabled = false           
                       WHERE seed_hash = %s 
                       AND seed_index = %s  
                       AND destination_address = %s 
                       AND is_deleted = false"""   
        return query
    
    def enable_recurring_payment(self) :   
           
        query =    """UPDATE recurring_payments
                       SET is_enabled = true           
                       WHERE seed_hash = %s 
                       AND seed_index = %s  
                       AND destination_address = %s
                       AND is_deleted = false """   
        return query
    
    def delete_recurring_payment(self) :
           
        query =    """UPDATE recurring_payments
                       SET is_deleted = true, 
                           is_enabled = false ,
                           rp_end_date = now()         
                       WHERE seed_hash = %s 
                       AND seed_index = %s  
                       AND destination_address = %s
                       AND is_deleted = false """ 
        return query
    
    def exists_deleted(self) :
           
        query =    """SELECT true from recurring_payments                               
                       WHERE seed_hash = %s 
                       AND seed_index = %s  
                       AND destination_address = %s
                       AND is_deleted = true """ 
        return query

    
    def update_payment_is_due(self):
        q = """ 
            UPDATE recurring_payments
            SET
            last_paid_date = next_pay_date,
            next_pay_date = next_pay_date + CONCAT(payment_interval, ' ', payment_period )::INTERVAL,
            status_e = %s -- PENDING
            WHERE next_pay_date < now()
            AND (status_e is null OR status_e = 'CONFIRMED')
            AND rp_end_date = '0001-01-01'
            AND is_enabled = true
            AND is_deleted = false  
            """
        return q
    
    






# "postgresql":{
#         "client": "postgresql",
#     "connection": {
#       "host": "localhost",
#       "user": "root",
#       "password": "rootpw",
#       "dbname": "nanodb",
#       "port":"5432"
#     } 
#   }


# UPDATE totals 
#    SET total = total + 1
# WHERE name = 'bill';

# SELECT (NOW() + interval '8 hours') AS next_payout;


# DROP TABLE accounts;
# CREATE TABLE accounts (
#     account character varying(65) DEFAULT NULL::character varying,
#     frontier character varying(64) DEFAULT NULL::character varying,
#     open_block character varying(64) DEFAULT NULL::character varying,
#     representative_block character varying(64) DEFAULT NULL::character varying,
#     balance numeric(39) DEFAULT NULL::numeric,
#     modified_timestamp integer DEFAULT NULL::integer,
#     block_count integer DEFAULT NULL::integer,
#     confirmation_height integer DEFAULT NULL::integer,
#     confirmation_height_frontier character varying(64) DEFAULT NULL::character varying,
#     representative character varying(65) DEFAULT NULL::character varying,
#     weight numeric(39) DEFAULT NULL::numeric ,
#     pending character varying(39) DEFAULT NULL::character varying,
#     key character varying(64) DEFAULT NULL::character varying
# );

# DROP TABLE IF EXISTS rate_limiter
# CREATE TABLE rate_limiter (
#     id character varying(65) DEFAULT NULL::character varying, 
#     type character varying(12) DEFAULT NULL::character varying,
#     counter_updated numeric(10) DEFAULT NULL::numeric,
#     created_by character varying(12) DEFAULT NULL::character varying,
#     datetime_created TIMESTAMPTZ,
#     datetime_updated TIMESTAMPTZ
# );
# CREATE INDEX rate_limiter_type ON rate_limiter USING btree(type);
# CREATE INDEX rate_limiter_created_by ON rate_limiter USING btree(created_by);
# CREATE INDEX rate_limiter_datetime_updated ON rate_limiter USING btree(datetime_updated);
# ALTER TABLE rate_limiter ADD PRIMARY KEY (id);

# DROP TABLE IF EXISTS payout_stats
# CREATE TABLE payout_stats (
#     nano_address character varying(65) DEFAULT NULL::character varying, 
#     ip character varying(16) DEFAULT NULL::character varying,
#     payout_amount numeric(39, 6) DEFAULT NULL::numeric ,
#     payout_currency character varying(12) DEFAULT NULL::character varying,
#     created_by character varying(12) DEFAULT NULL::character varying, 
#     datetime_created TIMESTAMPTZ,
#     datetime_updated TIMESTAMPTZ
# );
# CREATE INDEX payout_stats_nano_address ON payout_stats USING btree(nano_address);
# CREATE INDEX payout_stats_ip ON payout_stats USING btree(ip);
# CREATE INDEX payout_stats_payout_amount ON payout_stats USING btree(payout_amount);
# CREATE INDEX payout_stats_payout_currency ON payout_stats USING btree(payout_currency);
# CREATE INDEX payout_stats_created_by ON payout_stats USING btree(created_by);
# CREATE INDEX payout_stats_datetime_updated ON payout_stats USING btree(datetime_updated);


# insert into rate_limiter id{nano_address, ip} ,last_access_time = {now} ON CONFLICT UPDATE

# ON CONFLICT (id) DO UPDATE SET counter_updated=counter_updated + 1, balance=excluded.balance, height=excluded.height,"
#     "account=excluded.account, previous=excluded.previous, representative=excluded.representative, link=excluded.link,"
#     "link_as_account=excluded.link_as_account, signature=excluded.signature, work=excluded.work, subtype=excluded.subtype


# CREATE INDEX accounts_account ON accounts USING btree(account);
# CREATE INDEX accounts_balance ON accounts USING btree(balance);
# CREATE INDEX accounts_representative ON accounts USING btree(representative);
# CREATE INDEX accounts_pending ON accounts USING btree(pending);
# CREATE INDEX accounts_modified_timestamp ON accounts USING btree(modified_timestamp);
# ALTER TABLE accounts ADD PRIMARY KEY (account);



# --
# --
# DROP TABLE blocks;
# CREATE TABLE blocks (
#     hash character varying(65) DEFAULT NULL::character varying,
#     amount numeric(39) DEFAULT NULL::numeric,
#     balance numeric(39) DEFAULT NULL::numeric,
#     height integer DEFAULT NULL::integer,
#     local_timestamp integer  DEFAULT NULL::integer ,
#     confirmed integer DEFAULT NULL::integer,
#     type integer DEFAULT NULL::integer,
#     account character varying(65) DEFAULT NULL::character varying,
#     previous character varying(65) DEFAULT NULL::character varying,
#     representative character varying(65) DEFAULT NULL::character varying,
#     link character varying(65) DEFAULT NULL::character varying,
#     link_as_account character varying(65) DEFAULT NULL::character varying,
#     signature character varying(128) DEFAULT NULL::character varying,
#     work character varying(16) DEFAULT NULL::character varying,
#     subtype integer DEFAULT NULL::integer 
# );

# CREATE INDEX blocks_account ON blocks USING btree(account);
# CREATE INDEX blocks_type ON blocks USING btree(type);
# CREATE INDEX blocks_subtype ON blocks USING btree(subtype);
# CREATE INDEX blocks_amount ON blocks USING btree(amount);
# CREATE INDEX blocks_balance ON blocks USING btree(balance);
# CREATE INDEX blocks_representative ON blocks USING btree(representative);
# CREATE INDEX blocks_local_timestamp ON blocks USING btree(local_timestamp);
# ALTER TABLE blocks ADD PRIMARY KEY (hash);