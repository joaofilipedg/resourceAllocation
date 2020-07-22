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
    - flask-migrate (validated with v2.4.0)
    - sqlalchemy-utils (validated with v.0.36.5)

- sqlite3 
- nginx (validated with v1:1.16.1-1.el7)

## Configuration steps

### Configure conda env
```bash
conda create -n resalloc_env python=3.7
conda activate resalloc_env
conda install flask gunicorn apscheduler flask-apscheduler SQLAlchemy
conda install -c conda-forge python-ldap 
conda install -c conda-forge flask-migrate 
conda install sqlalchemy-utils
```

### Set environment variables

```bash
python -c 'import os; print(os.urandom(16))'
```

### Test gunicorn and flask

```bash
gunicorn --bind 0.0.0.0:65010  wsgi:app --workers 1
```

### Changes to the Database

* Change the in ```models.py```.
* Use flask-migrate to update the database:

    * Create scripts for migration:   
        ```bash
        sh migrate_db.sh migrate <migration message>
        ```
    * Update the database using the new scripts:
        ```bash
        sh migrate_db.sh upgrade
        ```
    * It is also possible to go back to a previous version of the database using downgrage:
        ```bash
        sh migrate_db.sh downgrade
        ```