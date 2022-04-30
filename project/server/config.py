
class AppConfig():
    DEBUG = True
    LOG_DEBUG = False
    TESTING = False
    SECRET_KEY = "secret-flask-key"
    # RPC_AUTH = False
    # RPC_URL = "http://172.17.0.1:7076" #if local dockerized nano_node is used
    # RPC_USER = ""
    # RPC_PASSWORD = ""
    RPC_AUTH = True
    RPC_URL = "https://nanowallet.cc:9951/nanocurrency/rpc"
    RPC_USER = "nano_rp"
    RPC_PASSWORD = "a_password_th4t_actually_w0rks_for_th1s_purpose"
    ENCRYPTION = "ZUMqiZwTj3vx91sosWfGbmhR7AbPVkBncWDQ31cK6Ks="   # key = Fernet.generate_key()
    DEFAULT_REP = "nano_3msc38fyn67pgio16dj586pdrceahtn75qgnx7fy19wscixrc8dbb3abhbw6"   #gr0vity
    JSON_SORT_KEYS = False
 
