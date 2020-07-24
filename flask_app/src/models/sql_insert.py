from flask_app.app import db
from flask_app.src.models import Host

from flask_app.src.models.sql_update import update_hostComponents
# from flask_app.src.global_stuff import DEBUG_MODE, dict_to_str
from flask_app.src.custom_logs import write_log, write_log_exception

# Main insert function (the others should use this one)
def insert_newEntry(Table, args_dict, log_args={}):
    try:
        new_entry = Table(args_dict)
        # if not DEBUG_MODE:
        #     if log_args != {}:
        #         log_args["app"].logger.infosql("username:'{user}', INSERT: {{table:'{table}', values='{values}'}}".format(user=log_args["user"], table=Table.__table__.name, values=dict_to_str(args_dict)))

        # if entering new host need to check if it needs to assign any component
        if Table == Host:
            new_entry, _ = update_hostComponents(new_entry, args_dict["gpu"], args_dict["fpga"], log_args=log_args)

        log_args["values"] = args_dict
        
        db.session.add(new_entry)
        db.session.commit()

        # new_entry id is only available after the commit
        log_args["values"]["id"] = new_entry.id

        write_log(log_args, "INSERT", Table.__table__.name)

    except Exception as e:
        db.session.rollback()
        write_log_exception(e)
        
    return new_entry
