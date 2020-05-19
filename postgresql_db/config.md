
## 1. Install PostgreSQL

Install using package manager:
```bash
sudo apt install postgresql postgresql-contrib
```
Launch service:
```bash
sudo service postgresql start
```
## 2. Create HPCAS role

Create new role:
```bash
sudo -u postgres createuser --interactive
Enter name of role to add: hpcas_admin
Shall the new role be a superuser? (y/n) y
```

## 3. Create new DB

```bash
createdb res_alloc
psql -d res_alloc