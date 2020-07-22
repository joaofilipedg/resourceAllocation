import csv

def read_csv(file, delimiter):
    with open("{}".format(file)) as csv_file:
        data = csv.reader(csv_file, delimiter=delimiter)
        values = []
        for row in data:
            values.append(row)
    return values


def fill_defaults(db, Host, Component, Reservation_type):
    # Hosts
    if Host.query.all() == []:
        def_file = read_csv("sqlite/defaults/def_hosts.csv", ";")

        for row in def_file:
            h = Host(hostname=row[0], ip=int(row[1]), enabled=1, cpu=0)
            db.session.add(h)
        db.session.commit()

    # Components (CPUs, GPUs, FPGAs)
    if Component.query.all() == []:
        c = Component(id=0, type=0, name="default", generation="",manufacturer="")
        db.session.add(c)
        db.session.commit()

        files = ["cpus", "gpus", "fpgas"]
        for i, f in enumerate(files):
            def_file = read_csv("sqlite/defaults/def_{}.csv".format(f), ";")

            for row in def_file:
                c = Component(type=i, name=row[1], generation=row[2],manufacturer=row[0])
                db.session.add(c)
        db.session.commit()

    # Reservation Types
    if Reservation_type.query.all() == []:
        def_file = read_csv("sqlite/defaults/def_reservation_types.csv", ";")
        
        for row in def_file:
            r = Reservation_type(id=int(row[0]), name=row[1], description=row[2])
            db.session.add(r)
        db.session.commit()
