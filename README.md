# Nano recurring payments

If you want to give it a try, simply claim some free nyano at https://nyanowallet.cc and setup a recurring payment afterards.


### Quick Start

Spin up the containers:

```sh
$ docker-compose up -d --build
```

Open your browser to [http://localhost:5003](http://localhost:5003)

It is recommended to run your own instance of the nano node.
Config file is located in project -> server -> config.py


To setup the cronjon do, setup a virtual python environment (venv)
```sh
cd /path/to/nano_recurring_payments/ 
virtualenv nano_rp_venv
source nano_rp_venv/bin/activate
```
```
crontab -e 
```
Add the following line to run the script every minute (modify your path)
```
* * * * * cd /path/to/nano_recurring_payments/ /usr/bin/flock -n /tmp/cron_rp.lockfile && /path/to/nano_recurring_payments/nano_rp_venv/bin/python cron_rpm.py
```




```
tips to fund the https://nyanowallet.cc faucet are welcome :-)
nano_1nyano1gy9khpmwcfazh3hxxxposu3yj71yow9d8c9d19567oom316getmsg```
