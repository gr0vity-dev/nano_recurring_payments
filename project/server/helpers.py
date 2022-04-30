from project.server.config import AppConfig
import requests
import json
from datetime import datetime
from cryptography.fernet import Fernet
from hashlib import sha256


debug = AppConfig.DEBUG

def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

def hash_seed(seed):
    input_ = seed + AppConfig.ENCRYPTION
    return sha256(input_.encode('utf-8')).hexdigest()

def encrypt_seed(seed):
    return Fernet(AppConfig.ENCRYPTION).encrypt(seed.encode("utf-8")).decode("utf-8") #yields a string that neds to be encoded back

def decrypt_seed(seed_enc):
    return Fernet(AppConfig.ENCRYPTION).decrypt(seed_enc.encode("utf-8")).decode("utf-8")


def hacky_number_shifter(value, shift_by, do="multiply"): 
    value = float(value)   
    if shift_by > 20 :
        remaning_shift = shift_by - 20
        shift_by = 20
    if do == "multiply" :
        for i in range(shift_by):
            value = value * 10
        value = value * (10 ** remaning_shift)
    if do == "divide" :
        for i in range(shift_by):
            value = value / 10
        value = value / (10 ** remaning_shift)
    return value

def multidict_to_json(multi_dict):
    req_dic = {}
    for key, value in multi_dict.items():        
        if key in ["amount", "interval"] and value is not None and value != "":        
            value = float(value.replace(",", ".")) 
   
      # checking for any nested dictionary
        l = key.split(".")
        
        # if nested dictionary is present
        if len(l) > 1: 
            i = l[0]
            j = l[1]
            if req_dic.get(i) is None:
                req_dic[i] = {}
                req_dic[i][j] = []
                req_dic[i][j].append(value)
            else:
                if req_dic[i].get(j) is None:
                    req_dic[i][j] = []
                    req_dic[i][j].append(value)
                else:
                    req_dic[i][j].append(value)
    
        else:  # if single dictionary is there
            if req_dic.get(l[0]) is None:                
                req_dic[l[0]] = value
            else:
                req_dic[l[0]] = value
    return req_dic