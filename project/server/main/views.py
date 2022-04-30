# project/server/main/views.py

from flask import render_template, Blueprint, request, redirect, url_for, send_from_directory
from project.server.config import AppConfig
from project.server.run_server import create_app
from project.server.helpers import encrypt_seed, hash_seed, multidict_to_json
from project.server.api.nano_rpc import Api
from project.server.api.db_access import rpm_seed_index, rpm_enable_disable_delete
from project.server.api.db import Postgres
# from flask_cors import CORS
import json
import os
# import redis
import requests
import logging
import secrets

           

main_blueprint = Blueprint("main", __name__,)
app = create_app()
p = Postgres()
debug = AppConfig.DEBUG
api = Api()  


@main_blueprint.route("/", methods=["GET"])
def home():
    return {"message" : "use /new to generate a new seed"}
    # return render_template("main/home.html", active_rps = [])


@main_blueprint.route('/favicon.ico') 
def favicon(): 
    return send_from_directory('/usr/src/app/project/client/static',
        'favicon.ico',mimetype='image/vnd.microsoft.icon')



@main_blueprint.route("/new")
def new_seed():
    seed = secrets.token_hex(32)    
    return redirect(url_for('main.rp_handler', seed=seed, index=0, action="get"))    

# @ main_blueprint.route("/seed/<seed>/<index>")
# def existing_seed(seed, index, message = None): 
    
#     account_data = api.get_account_data(seed,index)
#     p._cursor.execute(p.select_recurring_payment_one(), (hash_seed(seed), index))
#     active_rps = p.format_sql_response(p._cursor)
    
#     return render_template("main/home.html", account_data=account_data, active_rps=active_rps, message=message)    


@ main_blueprint.route("/rp//<seed>/<index>", methods=["GET", "POST"])
def rp_handler(seed,index, message = None):     
    account_data = api.get_account_data_detailed(seed,index)    
    res = None
    action = request.args.get('a')
    if request.method == "POST":
        form = request.form
        print(request.base_url)
        json_msg = multidict_to_json(form)
       
        # url = "http://localhost:5003/api/rpm/{}/{}".format(seed,index)
        # headers = {"Content-type": "application/json", "Accept": "text/plain"}  
        

        if action == "rp_add": 
            res = rpm_seed_index(seed,index, "POST", json_msg )                    
            #res = requests.post(url, json=json_msg, headers=headers)
        elif action in["rp_enable", "rp_disable", "rp_delete"]:           
            res = rpm_enable_disable_delete(action,seed,index,json_msg["destination"] )     
            # res = requests.put(url, json=json_msg, headers=headers)             
        elif action == "rp_update":
            res = rpm_seed_index(seed,index, "PUT", json_msg )   
            # res = requests.put(url, json=json_msg, headers=headers)       
        if res is not None:
            message = res[0]       
    
    p._cursor.execute(p.select_recurring_payment_one(), (hash_seed(seed), index))
    active_rps = p.format_sql_response(p._cursor)
    return render_template("main/home.html", account_data=account_data, active_rps=active_rps, message=message)  



