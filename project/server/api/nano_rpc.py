import requests
import json
import secrets
import math
import time
import logging
# import redis
import os
from project.server.config import AppConfig
from project.server.helpers import hacky_number_shifter
# from decimal import *


def to_nano(account):
    return account.replace("nyano_", "nano_").replace("xrb_", "nano_")

def to_nyano(account):
    return account.replace("nano_", "nyano_").replace("xrb_", "nyano_")



class Api:

    debug = None
      
    def __init__(self):       
        self.debug = AppConfig.LOG_DEBUG
        
    
    def post_with_auth(self, content):
        
        url = AppConfig.RPC_URL #"https://nanowallet.cc:9951/nanocurrency/rpc"    
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        try:
            if AppConfig.RPC_AUTH :
                r = requests.post(url, auth=(AppConfig.RPC_USER , AppConfig.RPC_PASSWORD), json=content, headers=headers)
            else:
                r = requests.post(url, json=content, headers=headers)
            logging.info({"request": content["action"]})
            return json.loads(r.text)
        except : 
            if self.debug : print("{} Retrys left for post_with_auth : {}".format(max_retry, content["action"]))
            max_retry = max_retry - 1   
            if max_retry >= 0 : 
                time.sleep(0.1)  #100ms
                self.post_with_auth(content,max_retry)
        

    def amount_to_raw(self, amount,currency):   
        if currency.lower() == "nano" :
            return hacky_number_shifter(amount, 30)
        if currency.lower() == "nyano" :
            return hacky_number_shifter(amount, 24)
    
    def amount_from_raw(self, raw,currency):   
        if currency.lower() == "nano" :
            return hacky_number_shifter(raw, 30, "divide")
        if currency.lower() == "nyano" :
            return hacky_number_shifter(raw, 24, "divide")

    def nyano_to_raw(self, amount):
        #hacky solution allows for 3 decimal places  
        return int(amount * 1000) * int(10**21)
    
    def raw_to_nyano(self,amount):        
        return int(int(amount) / int(10**22)) / 100

    def nyano_to_nano_address(self,address):        
        return address.replace("nyano_", "nano_").replace("xrb_", "nano_")

    def nano_to_nyano_address(self,address):        
        return address.replace("nano_", "nyano_").replace("xrb_", "nyano_")
    
    

    def generate_seed(self):
        return secrets.token_hex(32)

    def generate_new_seed(self):
        return {'success': True,
                'seed': self.generate_seed(),
                'error_message': ''}

    def validate_seed(self, seed):
        result = {
            'seed': seed,
            'success': False,
            'error_message': ''
        }
        if len(seed) == 64:
            try:
                int(seed, 16)
                result['success'] = True

            except Exception:
                result['error_message'] = 'Wrong seed format'
        else:
            result['error_message'] = 'Wrong seed length'

        return result
    def get_account_data(self, seed):
        payload = self.generate_account(seed, 0)
        payload["success"] = True
        payload["error_message"] = ''
        
        return payload
    
    def get_account_data_detailed(self, seed, index):
        payload = self.generate_account(seed, index)
        balance_data = self.check_balance(payload["account"], "nano")  
        payload["balance_currency"] = balance_data["currency"]        
        payload["balance"] = balance_data["balance"]       
        payload["receivable"] = balance_data["receivable"]
        payload["success"] = True
        payload["error_message"] = ''
        
        return payload

    def get_account_data(self, seed, index):
        payload = self.generate_account(seed, index)
        payload["success"] = True
        payload["error_message"] = ''
        
        return payload

    def generate_account(self, seed, index):
        
        req_deterministic_key = {
            "action": "deterministic_key",
            "seed": seed,
            "index": index,
        }
        print(req_deterministic_key)
        account_data = self.post_with_auth(req_deterministic_key)
        print(account_data)
        
        account_data = {
            "seed": seed,
            "index": index,
            "private": account_data["private"],
            "public": account_data["public"],
            "account": account_data["account"],
            "nano_prefix": account_data["account"][0:11],
            "nano_center": account_data["account"][11:59],
            "nano_suffix": account_data["account"][len(account_data["account"]) - 6:]
        }
        return account_data

    def validate_account_number(self, account):
        account = to_nano(account)
        response = {"success" : False}
        req_validate_account_number = {
            "action": "validate_account_number",
            "account": account,
        }
        data = self.post_with_auth(req_validate_account_number)          
        if data["valid"] == "1" :
            response["success"] = True            
        return response


    def check_balance(self, account, currency):       

        req_account_balance = {
            "action": "account_balance",
            "account": to_nano(account),
        }
        data = self.post_with_auth(req_account_balance)
       
        response = {}
        if currency == "nyano" :
            response["account"] = to_nyano(account)
        if currency == "nyano" :
            response["account"] = account 

        response["currency"] = currency
        response["balance"] = self.amount_from_raw(data["balance"], currency)
        response["receivable"] = self.amount_from_raw(data["receivable"], currency)
        response["total"] = response["balance"] + response["receivable"]

        return response

    def check_balances(self, seed):
        # check if there is any balance for account 0 to 50 accounts
        # {'index' : '' , 'account': '', 'balance': '', 'pending': ''}  ; spendable, total  Balance : 100 Nano . ! 95 Nano are currently not spendable. Your action is required.
        result = []
        for index in range(0, 51):
            nano_account = self.generate_account(seed, index)
            result.append(self.check_balance(nano_account["account"]))
  
    def get_block_info(self, hash):
        response = { "success" : True,
                     "error_message" : "" }
        
        req_block_info = {"action": "block_info",
                         "json_block": "true",
                         "hash": hash 
        }
        block_info = self.post_with_auth(req_block_info)
        
        if "error" in block_info:
            response["success"] = False
            response["error_message"] = block_info["error"]
        
        response["block_info"] = block_info
        return response


    def get_pending_blocks(
        self,
        nano_account,
        threshold,
        number_of_blocks
    ) :

        response = {"account" : to_nano(nano_account),
                    "blocks" : None,
                    "success" : True,
                    "error_message" : "" }

        req_accounts_pending = {
            "action": "accounts_pending",
            "accounts": [nano_account],
            "threshold" : str(threshold),
            "sorting" : "true",
            "count": str(number_of_blocks)
        }               
        accounts_pending = self.post_with_auth(req_accounts_pending)
        

        if "error" in accounts_pending:
            response["success"] = False
            response["error_message"] = accounts_pending["error"]
        elif accounts_pending["blocks"] == "" :
        # elif accounts_pending["blocks"][nano_account] == "" :        
            response["success"] = False
            response["error_message"] = "no pending blocks"
        else :
            response["blocks"] = accounts_pending["blocks"][nano_account]
        
        return response
  
       


    def publish_block(self, block_create_response) :
            req_process = {
                "action": "process",
                "json_block": "true",
                "subtype": block_create_response["subtype"],
                "block": block_create_response["block"],
            }
            return self.post_with_auth(req_process)      
 
    def create_receive_block_seed(
        self,
        open_seed,
        open_index,
        amount_per_chunk_raw,
        rep_account,
        send_block_hash,
        broadcast = 1
    ):
        if self.debug : t1 = time.time() 
        req_source_account = {
            "action": "deterministic_key",
            "seed": open_seed,
            "index": str(open_index),
        }
        if self.debug : logging.info("req_source_account : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 
        source_account_data = self.post_with_auth(req_source_account)     

        return self.create_receive_block(  source_account_data["account"],
                                        source_account_data["private"],
                                        amount_per_chunk_raw,
                                        rep_account,
                                        send_block_hash,
                                        broadcast
                                        )

    def create_receive_block(
        self,
        destination_account,
        open_private_key,
        amount_per_chunk_raw,
        random_rep,
        send_block_hash,
        broadcast = 1
    ):

        req_account_info = {
            "action": "account_info",
            "account": to_nano(destination_account),
            "representative": "true",
            "receivable": "true",
            "include_confirmed": "true"
        }
        account_info = self.post_with_auth(req_account_info)
        

        if "error" in account_info:
            subtype = "open"
            previous = "0000000000000000000000000000000000000000000000000000000000000000"
            balance = str(amount_per_chunk_raw)
        else:
            subtype = "receive"
            previous = account_info["frontier"]
            balance = str(
                int(account_info["confirmed_balance"]) + int(amount_per_chunk_raw))

        random_rep = "nano_3msc38fyn67pgio16dj586pdrceahtn75qgnx7fy19wscixrc8dbb3abhbw6"
        # prepare open/receive block
        req_block_create = {
            "action": "block_create",
            "json_block": "true",
            "type": "state",
            "balance": balance,
            "key": open_private_key,
            "representative": random_rep,
            "link": send_block_hash,
            "previous": previous
            # ,"difficulty": difficulty,
        }

        block = self.post_with_auth(req_block_create)        
        next_hash = block["hash"]
        block["subtype"] = subtype

        if broadcast == 1 :
            self.publish_block(block)            


        return {"success" : True,
                "account" : destination_account, 
                "balance_raw": balance,
                "balance": self.amount_from_raw(balance, "nano"), 
                "balance_nyano": self.amount_from_raw(balance, "nyano"), 
                "hash": next_hash,
                "amount_raw": amount_per_chunk_raw,
                "amount": self.amount_from_raw(amount_per_chunk_raw, "nano"),
                "amount_nyano" : self.amount_from_raw(amount_per_chunk_raw, "nyano"),
                "block" : block}
   
    def create_send_block_seed(
        self,
        source_seed,
        source_index,
        destination_account,
        amount_per_chunk_raw,
        broadcast = 1
    ):
        if self.debug : t1 = time.time() 
        req_source_account = {
            "action": "deterministic_key",
            "seed": source_seed,
            "index": source_index,
        }
        source_account_data = self.post_with_auth(req_source_account)      
        if self.debug : logging.info("req_source_account : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 

        return self.create_send_block(  source_account_data["account"],
                                        source_account_data["private"],
                                        destination_account,
                                        amount_per_chunk_raw,
                                        broadcast)

    def create_send_block(
        self,
        source_account,
        source_private_key,
        destination_account,
        amount_per_chunk_raw,
        broadcast = 1
    ):
        if self.debug : t1 = time.time()    

        req_account_info = {
            "action": "account_info",
            "account": source_account,
            "representative": "true",
            "pending": "true",
            "include_confirmed": "true"
        }
        account_info = self.post_with_auth(req_account_info)
        
        
        if "error" in account_info:     
                if self.debug : print("error in create_send_block\n source_account : {} \naccount_info response: {}".format(source_account,account_info))          
        else :
            source_previous = account_info["frontier"]
            source_balance = account_info["balance"]
            current_rep = account_info["representative"]
        
        if self.debug : logging.info("post_with_auth : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 

        
        req_destination_key = {"action": "account_key",
                                "account": destination_account}
        destination_link = self.post_with_auth(req_destination_key)["key"]
        
        if self.debug : logging.info("req_destination_key : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 

        # prepare send block
        block_balance = str(int(source_balance) - int(amount_per_chunk_raw))
        req_block_create = {
            "action": "block_create",
            "json_block": "true",
            "type": "state",
            "balance": str(block_balance),
            "key": source_private_key,
            "representative": current_rep,
            "link": destination_link,
            "link_as_account": destination_account,
            "previous": source_previous
            # ,"difficulty": difficulty,
        }

        send_block =  self.post_with_auth(req_block_create)
        send_block["subtype"] = "send"

        if broadcast == 1 :
            self.publish_block(send_block)
            # return send_block
              
        return {"success" : True,
                "account" : source_account, 
                "balance_raw": block_balance,
                "balance": self.amount_from_raw(block_balance, "nano"), 
                "balance_nyano": self.amount_from_raw(block_balance, "nyano"), 
                "hash": send_block["hash"],
                "amount_raw": amount_per_chunk_raw,
                "amount": self.amount_from_raw(amount_per_chunk_raw, "nano"),
                "amount_nyano" : self.amount_from_raw(amount_per_chunk_raw, "nyano"),
                "block" : send_block}

        

    def create_change_block_seed(
        self,
        source_seed,
        source_index,
        new_rep,
        broadcast = 1

    ):          
        if self.debug : t1 = time.time()  
        req_source_account = {
            "action": "deterministic_key",
            "seed": source_seed,
            "index": source_index,
        }
        source_account_data = self.post_with_auth(req_source_account)
        if self.debug : logging.info("req_source_account : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 

        
        source_account_data = {
            "seed": source_seed,
            "index": source_index,
            "private": source_account_data["private"],
            "public": source_account_data["public"],
            "account": source_account_data["account"],
        }

        req_account_info = {
            "action": "account_info",
            "account": source_account_data["account"],
            "representative": "true",
            "pending": "true",
            "include_confirmed": "true"
        }
        account_info = self.post_with_auth(req_account_info)
        
        if self.debug : logging.info("post_with_auth : {}".format(time.time() - t1))
        if self.debug : t1 = time.time() 

        source_previous = account_info["frontier"]
        source_balance = account_info["balance"]
        current_rep = account_info["representative"]

        # if random_reps != None :
        #     new_rep = random.choice(random_reps)
        #     while new_rep == current_rep: #make sure to set a new rep each time
        #         new_rep = random.choice(random_reps)
        
        if new_rep is None : new_rep = "nano_3msc38fyn67pgio16dj586pdrceahtn75qgnx7fy19wscixrc8dbb3abhbw6"
        # prepare change block
        req_block_create = {
            "action": "block_create",
            "json_block": "true",
            "type": "state",
            "balance": str(source_balance),
            "key": source_account_data["private"],
            "representative": new_rep,
            "link": "0000000000000000000000000000000000000000000000000000000000000000",
            "link_as_account": "nano_1111111111111111111111111111111111111111111111111111hifc8npp",
            "previous": source_previous,
        }        

        create_block_response =  self.post_with_auth(req_block_create)
        create_block_response["subtype"] = "change"

        if broadcast == 1 :
            self.publish_block(create_block_response)  
            return create_block_response      
        
        return create_block_response     