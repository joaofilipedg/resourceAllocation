import csv

# IF DEBUG_MODE == True, DISABLE LOGGING TO FILE
DEBUG_MODE = False 

def read_csv(file, delimiter):
    with open("{}".format(file)) as csv_file:
        data = csv.reader(csv_file, delimiter=delimiter)
        values = []
        for row in data:
            values.append(row)
    return values

def dict_to_str(dict_aux):
    str_aux = ""
    for key in dict_aux.keys():
        if str_aux != "":
            str_aux += ", "
        str_aux += "{}:{}".format(key, dict_aux[key])
    return str_aux
# def safeFunctionCall()