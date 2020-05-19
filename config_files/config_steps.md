# Steps to configure ``supervisor`` (systemd alternative) and ``nginx``
(https://medium.com/analytics-vidhya/part-1-deploy-flask-app-anaconda-gunicorn-nginx-on-ubuntu-4524014451b)
(https://medium.com/ymedialabs-innovation/deploy-flask-app-with-nginx-using-gunicorn-and-supervisor-d7a93aa07c18)
## 1. Supervisor

Make the appropriate changes to the ``supervisor.conf`` file:
  * ``directory`` needs to be the PATH to the ``wsgi.py`` file;
  * ``command`` needs to know the location of the ``gunicorn`` tool (could be inside a contained environment)

Put ``supervisor.conf`` in ``/etc/supervisor/conf.d/``:
```bash
sudo cp config_files/supervisor.conf /etc/supervisor/conf.d/gunicorn_res_alloc.conf
```
Stop and start the service:
```bash
sudo service supervisor stop
sudo service supervisor start
```
Confirm if the service is running:
```bash
sudo supervisorctl status
```

## 2. Nginx

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
Webapp should now be accessible at http://hostname.
