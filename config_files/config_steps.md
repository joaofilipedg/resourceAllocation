# Steps to configure ``supervisor`` (systemd alternative) and ``nginx``
(https://medium.com/analytics-vidhya/part-1-deploy-flask-app-anaconda-gunicorn-nginx-on-ubuntu-4524014451b)
(https://medium.com/ymedialabs-innovation/deploy-flask-app-with-nginx-using-gunicorn-and-supervisor-d7a93aa07c18)
## 1. Configure Supervisor

### 1.1 Install
(following steps given in https://stackoverflow.com/a/57162682/13228620)
Install supervisor
```bash
sudo yum install python-setuptools
sudo easy_install supervisor
```

Create directory for supervisor logs
```bash
mkdir /var/log/supervisor
```

Create directory for supervisor configs
```bash
mkdir -p /etc/supervisor/conf.d
```

Create config directory for supervisor
```bash
cat <<EOT >> /etc/supervisor/supervisord.conf
; supervisor config file

[supervisord]
logfile=/var/log/supervisor/supervisord.log ; (main log file;default $CWD/supervisord.log)
pidfile=/var/run/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/log/supervisor            ; ('AUTO' child log dir, default $TEMP)

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock ; use a unix:// URL  for a unix socket

[include]
files = /etc/supervisor/conf.d/*.conf
EOT
```

Create systemctl service script
```bash
cat <<EOT >> /lib/systemd/system/supervisord.service
[Unit]
Description=Supervisor process control system for UNIX
Documentation=http://supervisord.org
After=network.target

[Service]
ExecStart=/usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
ExecStop=/usr/bin/supervisorctl $OPTIONS shutdown
ExecReload=/usr/bin/supervisorctl -c /etc/supervisor/supervisord.conf $OPTIONS reload
KillMode=process
Restart=on-failure
RestartSec=50s

[Install]
WantedBy=multi-user.target
EOT
```

Enable on startup
```bash
sudo systemctl enable supervisord
```

### 1.2 Configuration

Make the appropriate changes to the ``supervisor.conf`` file:
  * ``directory`` needs to be the PATH to the ``wsgi.py`` file;
  * ``command`` needs to know the location of the ``gunicorn`` tool (could be inside a contained environment)

Put ``supervisor.conf`` in ``/etc/supervisor/conf.d/``:
```bash
sudo cp config_files/supervisor.conf /etc/supervisor/conf.d/gunicorn_res_alloc.conf
```
Reload daemon:
```bash
sudo systemctl daemon-reload
```
Stop and start the service:
```bash
sudo service supervisord stop
sudo service supervisord start
```
<!-- Confirm if the service is running:
```bash
sudo supervisorctl status
``` -->

## 2. Configure Nginx

### 2.1 Create Certificates

Create folder
```bash
cd config_files
mkdir certs
```

Create certificates/key for ssl connection:
```bash
$openssl req -x509 -newkey rsa:4096 -nodes -out certs/resalloc_cert.pem -keyout certs/resalloc_key.pem -days 365
-----
Country Name (2 letter code) [AU]:PT
State or Province Name (full name) [Some-State]:Lisbon
Locality Name (eg, city) []:Lisbon
Organization Name (eg, company) [Internet Widgits Pty Ltd]:INESC-ID
Organizational Unit Name (eg, section) []:HPCAS
Common Name (e.g. server FQDN or YOUR name) []:
Email Address []:sysadmin@googlegroups.com

$openssl dhparam -out certs/resalloc_dhparam.pem 4096
```

### 2.2 Nginx configuration

#### 2.2.1 (only in centos):
If there is no folder `/etc/nginx/sites-available`:
```bash
sudo mkdir /etc/nginx/sites-available
sudo mkdir /etc/nginx/sites-enabled
```
Add the following line to the `http` block inside `/etc/nginx/nginx.conf`:
```
include /etc/nginx/sites-enabled/*;
```

#### 2.2.2

(``nginx.conf`` follows the reccomendations by Mozilla at https://wiki.mozilla.org/Security/Server_Side_TLS)
(also useful: https://raymii.org/s/tutorials/Strong_SSL_Security_On_nginx.html)
Put ``nginx.conf`` in ``/etc/nginx/sites-available/``:
```bash
sudo cp config_files/nginx.conf /etc/nginx/sites-available/res_alloc
```
Create symlink:
```bash
sudo ln -s /etc/nginx/sites-available/res_alloc /etc/nginx/sites-enabled
```
Confirm nginx.conf syntax:
```bash
sudo nginx -t
```
Test application:
```bash
sudo service nginx stop
sudo service nginx start
```

## 3. Final configuration

### 3.1 Firewall

Make necessary adjustments
```bash
firewall-cmd --add-service=http --permanent
firewall-cmd --add-service=https --permanent
firewall-cmd --reload
firewall-cmd --list-all
semanage permissive -a httpd_t
```

### 3.2 Create socket folder
Note: don't user /tmp/socket.sock
https://stackoverflow.com/a/26257466/13228620
https://serverfault.com/a/464025

```bash
mkdir socket
```

### 3.3 Test

```bash
systemctl start supervisord
service nginx start
```

Webapp should now be accessible at http://hostname.


### Permission

nginx must have proper permissions to access the website static files.

example:
```bash
sudo chgrp -R nginx flask_app/templates
sudo chmod -R 750 flask_app/templates
sudo chmod -R g+s flask_app/templates

sudo chgrp -R nginx /homelocal/resalloc_bot/
sudo chmod -R 750 /homelocal/resalloc_bot/
sudo chmod -R g+s /homelocal/resalloc_bot/
```