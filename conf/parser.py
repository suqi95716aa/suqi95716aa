import os
import toml


def conf2Dict():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    if os.path.exists(path):
        with open(path, "r", encoding='utf8') as f:
            to_dict = toml.load(f)
            return to_dict
    else:
        raise FileNotFoundError


# MINIO
MINIO_CONFIG = conf2Dict()['MINIO_CONFIG']
BUCKET_NAMES = MINIO_CONFIG["BUCKET_NAMES"]
os.environ["USER_FILE_BUCKET"] = BUCKET_NAMES.get("USER_FILE_BUCKET")

# MILVUS
MILVUS_CONFIG = conf2Dict()['MILVUS_CONFIG']
BASE = MILVUS_CONFIG["BASE"]
INDEX = MILVUS_CONFIG["INDEX"]
CONN = MILVUS_CONFIG["CONNECTION"]
COL = MILVUS_CONFIG["COLLECTIONS"]

# UMI_OCR
UMI_OCR = conf2Dict()['UMI_OCR']
os.environ["UMI_OCR_URL"] = UMI_OCR["UMI_OCR_URL"]

# SPARK
SPARK_CONF = conf2Dict()['SPARK_OFFICIAL']
os.environ["SPARK_APPID"] = SPARK_CONF["SPARK_APPID"]
os.environ["SPARK_API_KEY"] = SPARK_CONF["SPARK_API_KEY"]
os.environ["SPARK_API_SECRET"] = SPARK_CONF["SPARK_API_SECRET"]
os.environ["SPARK_URL"] = SPARK_CONF["SPARK_URL"]

# GPT
GPT_CONF = conf2Dict()['GPT4_OFFICIAL']
os.environ["GPT_URL"] = GPT_CONF['GPT_URL']
os.environ["GPT_API_KEY"] = GPT_CONF['GPT_API_KEY']

# NEO4J
NEO4J_CONF = conf2Dict()['NEO4J_CONFIG']
NEO4J_BASE = NEO4J_CONF['BASE']
os.environ["NEO4J_URI"] = NEO4J_BASE["URL"]
os.environ["NEO4J_USERNAME"] = NEO4J_BASE["ACCOUNT"]
os.environ["NEO4J_PASSWORD"] = NEO4J_BASE["PASSWORD"]

