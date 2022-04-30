# Nano recurring payments



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
