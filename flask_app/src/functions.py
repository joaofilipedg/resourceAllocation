import csv

def read_csv(file, delimiter):
    with open("{}".format(file)) as csv_file:
        data = csv.reader(csv_file, delimiter=delimiter)
        values = []
        for row in data:
            values.append(row)
    return values