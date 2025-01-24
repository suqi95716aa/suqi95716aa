
# MinIO is a high-performance, S3-compatible object storage service that is designed for private cloud infrastructure.
# It is open-source and can be used to build applications that require reliable and scalable storage for any amount of data,
# from a single server to a large cluster. MinIO offers an S3-compatible API,
# making it easy to switch existing applications that use Amazon S3 to use MinIO
# without any code changes. It is ideal for applications that require high-performance,
# distributed storage, data encryption, and easy integration with other AWS services.

# Minio official documentation: https://www.minio.org.cn/

from conf.parser import conf2Dict

from minio import Minio

MINIO_CONF = conf2Dict()['MINIO_CONFIG']
MINIO_CONF_BASE = MINIO_CONF["BASE"]
MINIO_CONF_KEY = MINIO_CONF["KEY"]


minio_client = Minio(
    endpoint=MINIO_CONF_BASE.get("URL"),
    access_key=MINIO_CONF_KEY.get("ACCESS_KEY"),
    secret_key=MINIO_CONF_KEY.get("SECRET_KEY"),
    secure=MINIO_CONF_KEY.get("SECURE")
)
