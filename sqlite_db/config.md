
## 1. Install sqlite3

Install using package manager:
```bash
sudo apt install sqlite3
```

## 2. Create Tables

Open ``sqlite``:
```bash
sqlite3 res_alloc.db
```

Add tables:
```sqlite
CREATE TABLE users (
   id INTEGER PRIMARY KEY,
   username TEXT
   );
CREATE TABLE hosts (
   id INTEGER PRIMARY KEY,
   hostname TEXT,
   has_gpu INTEGER NOT NULL,
   has_fpga INTEGER NOT NULL
   );
CREATE TABLE reservations (
   id INTEGER PRIMARY KEY,
   user_id INTEGER,
   host_id INTEGER,
   begin_date REAL,
   end_date REAL,
   FOREIGN KEY (user_id) REFERENCES users(id),
   FOREIGN KEY (host_id) REFERENCES hosts(id)
   );
```

## 3. Fill Tables

```sqlite
INSERT INTO users VALUES
   (1, "joaoguerreiro"),
   (2, "difs")
   ;
INSERT INTO hosts VALUES
   (1, "saturn", 1, 0),
   (2, "vanessa", 0, 0),
   (3, "adriana", 1, 0),
   (4, "liliana", 0, 1),
   (5, "diana", 1, 0),
   (6, "lagpus", 1, 0),
   (7, "mariana", 1, 1),
   (8, "gisele", 1, 0),
   (9, "fernanda", 1, 0),
   (10, "izabel", 1, 0),
   (11, "flavia", 1, 0),
   (12, "sara", 1, 0),
   (13, "elsa", 0, 1),
   (14, "daniela", 1, 1),
   (15, "jessica", 1, 0),
   (16, "andreia", 0, 0),
   (17, "martha", 0, 1),
   (18, "alessandra", 1, 0),
   (19, "filipa", 1, 0),
   (20, "venus", 0, 0)
   ;
```
