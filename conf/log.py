import os
import sys
import time

import logging
from loguru import logger
from pprint import pformat


LOG_DIR = os.path.abspath(os.path.join("/logs", f'aiagent-service-{time.strftime("%Y-%m-%d")}.log'))
LOG_FORMAT = '<level>{level: <8}</level>  <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>'

LOG_FILE_PATH = '/logs'
OGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s %(levelprefix)s %(message)s",  # 这里日志格式加了时间显示
                "use_colors": False,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                # 这里日志格式加了时间显示
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr"
            },
            "access": {
                "formatter": "access",
                "class": "logging.handlers.TimedRotatingFileHandler",  # 这里用了nb_log的彩色控制台handler。
                'filename': '{}/uvicorn_access.log'.format(LOG_FILE_PATH)
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_record(record: dict) -> str:
    format_string = LOG_FORMAT

    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


def setupBackendLogger():
    logging.getLogger().handlers = [InterceptHandler()]
    logger.configure(
        handlers=[{"sink": sys.stdout, "level": logging.INFO, "format": format_record}])
    logger.debug('日志系统已加载')
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    # backend_log_path = os.path.abspath(os.path.join("/logs", "datahelper_service.log"))
    logger.add(LOG_DIR, rotation="50 MB", retention=14, enqueue=True)
