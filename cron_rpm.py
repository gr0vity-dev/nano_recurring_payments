from cron_db import Postgres
from project.server.api.nano_rpc import Api
from project.server.helpers import decrypt_seed
import traceback
import logging


logging.basicConfig(filename="./cron_rpm.out",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.debug("started")
p = Postgres()
nano_rpc = Api()


try: 
    p._cursor.execute(p.update_payment_is_due())
    p._cursor.execute(p.select_active_payments_by_state(), ('INITIATED',))
    initiated_payments = p.format_sql_response(p._cursor)
    logging.debug("CRON RPM initiated_payments count : {}".format(len(initiated_payments)))

    for row in initiated_payments:
        try:
            conn = p.new_conn(isolation_level=1)
            send_block = nano_rpc.create_send_block_seed(decrypt_seed(row["seed_enc"]),
                                                    int(row["seed_index"]),
                                                    row["destination_address"],
                                                    nano_rpc.amount_to_raw(row["payment_amount"],row["payment_currency"]),
                                                    broadcast = 0)
            conn.cursor().execute(p.update_payment_status_by_source_destination(True), ( send_block["hash"],
                                                                                         'RECEIVABLE',
                                                                                          row["source_address"], 
                                                                                          row["destination_address"]))
            conn.cursor().execute(p.insert_payout(), (row["seed_hash"],
                                                    row["seed_index"],
                                                    row["source_address"],
                                                    row["destination_address"],
                                                    send_block["hash"],
                                                    send_block["amount_raw"],
                                                    row["payment_amount"],
                                                    row["payment_currency"],
                                                    "cron_rpm" ))    
            conn.commit()        
            conn.close()
            try : 
                nano_rpc.publish_block(send_block["block"])
                logging.debug("CRON RPM published hash: {}".format(send_block["hash"]))		        
            except Exception as e:
                logging.error("CRON RPM PUBLISH ERROR on initiated_payments")
                p._cursor.execute(p.update_payment_status_by_source_destination(), ('FAILED_PUB', 
                                                                                        row["source_address"], 
                                                                                        row["destination_address"]))
        except Exception as e:
            logging.error("CRON RPM ROW ERROR on initiated_payments")
            traceback.print_exc()




    p._cursor.execute(p.select_active_payments_by_state(), ('RECEIVABLE',))
    receivable_payments = p.format_sql_response(p._cursor)
    logging.debug("CRON RPM receivable_payments count : {}".format(len(receivable_payments)))

    for row in receivable_payments:
        query = nano_rpc.get_block_info(row["last_tx_hash"])
        if query["success"] == True:
            if query["block_info"]["confirmed"] == 'true' :
                p._cursor.execute(p.update_payment_status_by_source_destination(), ('CONFIRMED', row["source_address"], row["destination_address"]))
except:
    logging.error("CRON RPM GLOBAL EXCEPTION")
    traceback.print_exc()

logging.debug("ended")
