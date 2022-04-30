from project.server.config import AppConfig
from project.server.api.nano_rpc import Api
from project.server.api.db import Postgres
from project.server.helpers import hash_seed, encrypt_seed
import logging
from project.server.run_server import create_app
from datetime import datetime, timedelta
# from collections import OrderedDict
import traceback
from dateutil import parser

api = Api()
debug = AppConfig.DEBUG
p = Postgres()


def rpm_seed(seed, curl_method, json = None):  
    try:
        if curl_method in ['GET']:  
            seed_hash = hash_seed(seed)
            
            try:
                p._cursor.execute(p.select_recurring_payment_all(), (seed_hash, ))
                res = p.format_sql_response(p._cursor)
            except Exception as e:
                traceback.print_exc()
                res = p.format_sql_exception(e)
        if curl_method in ['DELETE']:
            #TODOD: Delete all recurring payments for that seed
            pass
    except :
        traceback.print_exc()
        return ({"success" : False , "message": "Please try again later :-)"}), 400
    return res, 202

def rpm_seed_index(seed, index, curl_method, json_msg = None):
    seed_enc = encrypt_seed(seed)
    seed_hash = hash_seed(seed)
    
    if curl_method == 'GET':
        payload = { "seed_hash" : seed_hash, "index" : int(index) }
    elif curl_method == 'DELETE':
        payload = json_msg
        payload["seed_hash"] = seed_hash
        payload["index"] = int(index)
        payload["source"] = api.get_account_data(seed, index)
    else:
        payload = json_msg
        payload["seed"] = seed
        payload["index"] = int(index)
        payload["source"] = api.get_account_data(seed, index)
        payload["seed_enc"] = seed_enc
        payload["seed_hash"] = seed_hash
        if "is_enable" not in payload : payload["is_enabled"] = True

    try :
        if curl_method == 'GET':            
                #return 1 recuring payment only for the index
                try:    
                    p._cursor.execute(p.select_recurring_payment_one(), (payload["seed_hash"], payload["index"]))                
                    res = p.format_sql_response(p._cursor)
                except Exception as e:
                    traceback.print_exc()
                    res = p.format_sql_exception(e)
        elif curl_method == "POST":
            is_valid = is_payload_valid(payload, "POST") 
            if is_valid["success"] == False : 
                return (is_valid), 400
            if is_valid["success"]:               
                try:
                    p._cursor.execute(p.insert_recurring_payment(), (payload["seed_hash"], 
                                                                    payload["seed_enc"], 
                                                                    payload["index"], 
                                                                    payload["source"]["account"],
                                                                    payload["destination"], 
                                                                    payload["interval"],      
                                                                    payload["period"],                                                               
                                                                    payload["amount"],
                                                                    payload["currency"],
                                                                    payload["first_pay_date"],
                                                                    payload["first_pay_date"],                                                                                                                                
                                                                    False,
                                                                    payload["is_enabled"],
                                                                    "nano_rp" )) 
                    
                    p._cursor.execute(p.select_recurring_payment_by_destination(), (payload["seed_hash"], payload["destination"]))                
                    sql_query = p.format_sql_response(p._cursor)
                    res = {"success" : True,  "recurring_payment" : sql_query }
                except Exception as e:
                    traceback.print_exc()
                    res = p.format_sql_exception(e)
                
                #Alternatively, find an address with a positive balance
        elif curl_method == "PUT":             
             is_valid = is_payload_valid(payload, "PUT") 
             if is_valid["success"] == False : 
                return (is_valid), 400 
             if is_valid["success"]:               
                try: 
                    if "is_deleted" not in payload : payload["is_deleted"] = False
                    p._cursor.execute(p.update_recurring_payment(), (payload["source"]["account"],                                                                    
                                                                    payload["interval"],      
                                                                    payload["period"],                                                                 
                                                                    payload["amount"],
                                                                    payload["currency"],
                                                                    payload["first_pay_date"],
                                                                    payload["first_pay_date"],                                                                                                                                
                                                                    payload["is_deleted"],
                                                                    payload["is_enabled"],
                                                                    "nano_rp",
                                                                    payload["seed_hash"],                                                                    
                                                                    payload["index"],
                                                                    payload["destination"]  ))                     
                    p._cursor.execute(p.select_recurring_payment_by_destination(), (payload["seed_hash"], payload["destination"])) 
                    sql_query = p.format_sql_response(p._cursor)
                    res = {"success" : True, "updated_rows":  p._cursor.rowcount, "recurring_payment" : sql_query }
                except Exception as e:
                    traceback.print_exc()
                    res = p.format_sql_exception(e)
        elif curl_method == "DELETE":
            is_valid = is_payload_valid(payload, "DELETE") 
            if is_valid["success"] == False : 
                return (is_valid), 400 
            if is_valid["success"]: 
                try:
                    p._cursor.execute(p.delete_recurring_payment() , (payload["seed_hash"], payload["index"],payload["destination"]))  
                    res = {"succes" : True}
                except Exception as e:
                    traceback.print_exc()
                    res = p.format_sql_exception(e)    
    except :
        traceback.print_exc()
        res = ({"success" : False , "message": "Please try again later :-)"})
        res["account"] = payload["source"]["account"]
        return ({"success" : False , "message": "Please try again later :-)"}), 400
        
    return res, 202

def rpm_enable_disable_delete(action, seed,index,destination):
    try:
        print(action)
        if action == "rp_disable":            
            p._cursor.execute(p.disable_recurring_payment(), (hash_seed(seed),index,destination ))
            res = {"success" : True, "updated_rows":  p._cursor.rowcount }
        elif action == "rp_enable":
            p._cursor.execute(p.enable_recurring_payment(), (hash_seed(seed),index,destination ))
            res = {"success" : True, "updated_rows":  p._cursor.rowcount }
        elif action == "rp_delete":
            p._cursor.execute(p.delete_recurring_payment(), (hash_seed(seed),index,destination ))
            res = {"success" : True, "updated_rows":  p._cursor.rowcount }
        else :
           res = {"success" : False, "error_msg":  "actio [{}] unknown".format(action) } 
        
    except Exception as e:
        traceback.print_exc()
        res = p.format_sql_exception(e)   
   
    return res, 200
    



def rpm_insert(payload):
    is_valid = is_payload_valid(payload, "POST")
    if is_valid["success"] == False:
        return is_valid
    
 
def is_payload_valid(payload, curl_method):
    response = {"success" : False,
                "error_message" : ''}   
    

    if curl_method in ["POST", "PUT"]:
        if "first_pay_date" not in payload :
            response["error_message"] = "{first_pay_date} must be set"
            return response 
              

        try:
            payload["first_pay_date"] = parser.parse(payload["first_pay_date"])                
        except:
            response["error_message"] = "Wrong format for {first_pay_date}: Use 'YYYY-MM-DD hh:mm:ss'"
            return response       
       
        if payload["first_pay_date"] < (datetime.now() + timedelta(minutes=59)) :
            response["error_message"] = "Date must be greater than " + (datetime.now() + timedelta(hours=1)).strftime('"%Y-%m-%d %H:%M"') + " UTC"
            return response     
        if "index" not in payload :
            response["error_message"] = "{index} must be set"
            return response
        
        if payload["index"] < 0 or payload["index"] > 4294967295 :
            response["error_message"] = "{index} must be between 0 and 4294967295"
            return response
        if not api.validate_seed(payload["seed"]):
            response["error_message"] = "The provided seed is not valid"
            return response
        if "interval" not in payload:
            response["error_message"] = "{interval} must be set"
            return response
        if "period" not in payload:
            response["error_message"] = "{period} must be set"  
            return response   
        if payload["period"] not in ["day", "week" , "month" , "year", "hour"]:
            response["error_message"] = "{period} must be one of the following: [day; week; month; year; hour]"
            return response           
        if "amount" not in payload:
            response["error_message"] = "{amount} must be set"
            return response
        if "currency" not in payload:
            response["error_message"] = "{currency} must be set: [nano; nyano]"
            return response   
        if "destination" not in payload :
            response["error_message"] = "{destination} must be set"
            return response    
         
        if api.validate_account_number(payload["destination"])["success"] == False:
            response["error_message"] = "The provided {destination} is not valid"
            return response   

        source_balance = api.check_balance(payload["source"]["account"], payload["currency"])        
        if source_balance["balance"] < payload["amount"]:
            response["error_message"] = """Please make sure your account balance [{0} {2}] 
                                           is bigger than the payment amount [{1} {2}]""".format(source_balance["balance"],
                                                                                                 payload["amount"],
                                                                                                 payload["currency"]   )
            return response
        
        if payload["amount"] <= 0 :
            response["error_message"] = "The amount must be greather than 0"
            return response
        
        if payload["currency"] == "nyano" and payload["amount"] < 100 :
            response["error_message"] = "Minimal amount for recurring payments is 100 nyano"
            return response
        if payload["currency"] == "nano" and payload["amount"] < 0.000100 :
            response["error_message"] = "Minimal amount for recurring payments is 0.000100 nano"
            return response
        if payload["currency"] != "nano" and payload["currency"] != "nyano"  :
            response["error_message"] = "currency must be on of the following : [nano, nyano]"
            return response
        if not type(payload["is_enabled"]) == bool :
            response["error_message"] = "is_enabled must be a boolean"
            return response
        # if not type(payload["is_deleted"]) == bool :
        #     response["error_message"] = "is_deleted must be a boolean"
        #     return response
 
       
    if curl_method == "PATCH":
        if "period" in payload and payload["period"] not in ["D", "M" , "W" , "Y", "h"]:
            response["error_message"] = "{period} must be one of the following: [D; W; M; Y; h]"
            return response
        if "destination" in payload and not api.validate_account_number(payload["destination"]):
            response["error_message"] = "The provided {destination} is not a valid account"
            return response    

    if curl_method == "DELETE":
        if "destination" not in payload :
            response["error_message"] = "{destination} must be set"
            return response    
    
    response["success"] = True
    return response
