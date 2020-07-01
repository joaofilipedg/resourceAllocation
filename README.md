# resourceAllocation

## Requirements

- anaconda3
    - python3 (validated with 3.7)
    - flask (validated with v1.1.2)
    - gunicorn (validated with v20.0.4)
    - apscheduler (validated with v3.6.3)
    - flask-apscheduler (validated with v1.11.0)
    - SQLAlchemy (validated with v1.3.17)
    - python-ldap (validated with v3.2.0)
    - flask-wtf (validated with v0.14.3)
    - flask-sqlalchemy (validated with v2.4.1)
    - flask-login (validated with v0.5.0)
    - sqlalchemy-utls (validated with v.0.36.5)
- sqlite3 
- nginx (validated with v1:1.16.1-1.el7)

## Configuration steps

### Configure conda env
```bash
conda create -n resalloc_env python=3.7
conda activate resalloc_env
conda install flask gunicorn apscheduler flask-apscheduler SQLAlchemy
conda install -c conda-forge python-ldap 
conda install sqlalchemy-utils
```

### Test gunicorn and flask

```bash
gunicorn --bind 0.0.0.0:65010  wsgi:app --workers 1
```