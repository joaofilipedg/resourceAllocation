# resourceAllocation

## Requirements

- anaconda3
    - python3 (validated with 3.7)
    - flask (validated with v1.1.2)
    - gunicorn (validated with v20.0.4)
    - apscheduler (validated with v3.6.3)
    - flask-apscheduler (validated with v1.11.0)
    - SQLAlchemy (validated with v1.3.17)
- sqlite3 
- nginx (validated with v1:1.16.1-1.el7)

## Configuration steps

### Configure conda env
```bash
conda create -n resalloc_env python=3.7
conda activate resalloc_env
conda install flask gunicorn apscheduler flask-apscheduler SQLAlchemy
```

### Test gunicorn and flask

```bash
gunicorn --bind 0.0.0.0:65010  wsgi:app --workers 1
```