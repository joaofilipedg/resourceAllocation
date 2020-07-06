from logging.config import dictConfig

"""
Based on: https://github.com/tenable/flask-logging-demo
"""


class LogSetup(object):
    def __init__(self, app=None, **kwargs):
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app):
        log_type = app.config["LOG_TYPE"]
        logging_level = app.config["LOG_LEVEL"]
        
        try:
            log_directory = app.config["LOG_DIR"]
            app_log_file_name = app.config["APP_LOG_NAME"]
            access_log_file_name = app.config["WWW_LOG_NAME"]
        except KeyError as e:
            exit(code="{} is a required parameter for log_type '{}'".format(e, log_type))
        app_log = "/".join([log_directory, app_log_file_name])
        www_log = "/".join([log_directory, access_log_file_name])

        log_max_bytes = app.config["LOG_MAX_BYTES"]
        log_copies = app.config["LOG_COPIES"]
        logging_policy = "logging.handlers.RotatingFileHandler"

        std_format = {
            "formatters": {
                "default": {
                    "format": "[%(asctime)s.%(msecs)03d] %(levelname)s %(name)s:%(funcName)s: %(message)s",
                    "datefmt": "%d/%b/%Y:%H:%M:%S",
                },
                "sqlite": {
                    "format": "[%(asctime)s.%(msecs)03d] %(levelname)s %(funcName)s: %(message)s",
                    "datefmt": "%d/%b/%Y:%H:%M:%S",
                },
                "access": {"format": "%(message)s"},
            }
        }
        std_logger = {
            "loggers": {
                "": {
                    "level": logging_level,
                    "handlers": ["default"], 
                    "propagate": True
                    },
                "app.access": {
                    "level": logging_level,
                    "handlers": ["access_logs"],
                    "propagate": False,
                },
                "app.sqlite": {
                    "level": logging_level,
                    "handlers": ["sqlite_logs"],
                    "propagate": False,
                },
                "root": {
                    "level": logging_level,
                    "handlers": ["default"]
                },
            }
        }
        logging_handler = {
            "handlers": {
                "default": {
                    "level": logging_level,
                    "class": logging_policy,
                    "filename": app_log,
                    "backupCount": log_copies,
                    "maxBytes": log_max_bytes,
                    "formatter": "default",
                    "delay": True,
                },
                "sqlite_logs": {
                    "level": logging_level,
                    "class": logging_policy,
                    "filename": app_log,
                    "backupCount": log_copies,
                    "maxBytes": log_max_bytes,
                    "formatter": "sqlite",
                    "delay": True,
                },
                "access_logs": {
                    "level": logging_level,
                    "class": logging_policy,
                    "filename": www_log,
                    "backupCount": log_copies,
                    "maxBytes": log_max_bytes,
                    "formatter": "access",
                    "delay": True,
                },
            }
        }

        log_config = {
            "version": 1,
            "formatters": std_format["formatters"],
            "loggers": std_logger["loggers"],
            "handlers": logging_handler["handlers"],
        }
        dictConfig(log_config)