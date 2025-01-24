
from sanic import Blueprint

from conf.parser import conf2Dict


aet = Blueprint('article_extracor')

SYSTEMD_KBID = "systemd"
MINIO_CONFIG = conf2Dict()['MINIO_CONFIG']
BUCKET_NAMES = MINIO_CONFIG["BUCKET_NAMES"]
USER_FILE_BUCKET = BUCKET_NAMES.get("USER_FILE_BUCKET")
