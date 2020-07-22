import logging
import json

from flask_app.app import db
from flask_app.src.models import Host

from flask_app.src.models.sql_update import update_hostComponents
from flask_app.src.global_stuff import DEBUG_MODE, dict_to_str


# Main insert function (the others should use this one)
def insert_newEntry(Table, args_dict, log_args={}):
    try:

        new_entry = Table(args_dict)

        # if get_return_id:
        #     db.session,refresh(new_entry)
        #     return new_entry.id

        if not DEBUG_MODE:
            if log_args != {}:
                print("1")
                print(log_args["user"])
                print("2")
                print(Table.__table__.name)
                print("3")
                print(json.dumps(args_dict))
                log_args["app"].logger.infosql("username:'{user}', INSERT: {{table:'{table}', values='{values}'}}".format(user=log_args["user"], table=Table.__table__.name, values=dict_to_str(args_dict)))

        if Table == Host:
            if "gpu" in args_dict.keys() or "fpga" in args_dict.keys():
                new_entry = update_hostComponents(new_entry, args_dict, log_args=log_args)
        db.session.add(new_entry)
        db.session.commit()

    except Exception as e:
        if not DEBUG_MODE:
            logging.critical("Something awful happened", exc_info=True)
        print(e)
        return -1
    return new_entry
