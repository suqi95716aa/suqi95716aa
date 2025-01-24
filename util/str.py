import re
import os
import time
from typing import List


def normalize_sql_transfrom(inputs):
    """
    专门用于SQL输出的清洗
    """
    matches_1 = re.findall(r"```sql\n(.*?)\n```", inputs)
    matches_2 = re.findall(r'```sql\s*(.*?)\s*```', inputs, re.DOTALL)
    matches = max(matches_1, matches_2, key=lambda x: sum([len(i) for i in x]))
    if not matches: matches = [inputs]
    sql = matches[0].replace("\n", " ")
    if not sql.strip().startswith("SELECT"): sql = "SELECT " + sql
    sql = sql.replace("SELECT SELECT", "SELECT")
    sql = sql.replace("SELECT  SELECT", "SELECT")
    sql = sql.replace("SELECT   SELECT", "SELECT")
    sql = sql.replace("`", "")
    sql = sql.replace("\n", " ")
    sql = sql.replace("  ", " ")
    sql = sql.replace("，", ",")
    sql = sql.replace("；", ";")
    return sql


def replace_keyword(prompts: List, input_keys: List) -> List:
    """
    批量替换关键词
    :param input_keys: [{"keyword": "question", "text": "Your replace keyword"}]
    :param prompts: Template will be replaced

    :return {"role": "System", "content": "问题是：{本月H6国潮版在全国各地的经销商库存总量是多少?}"}
    """
    for input_key in input_keys:
        for ind, prompt in enumerate(prompts):
            replace_keyword = "{" + f"{input_key['keyword']}" + "}"
            if replace_keyword in prompt["content"]:
                prompts[ind]["content"] = prompt["content"].replace(replace_keyword, input_key["text"])

    return prompts


def get_fs_path(path: str, *args) -> str:
    """
    Get file system path

    :param path: get bucket root path
    :param args: sub path will append

    :return
         full storage path(unix system)
    """
    _path = os.path.join(path, *args)
    _unix_path = _path.replace("\\", "/")
    return _unix_path


def rename(filename: str) -> str:
    """
    To address the issue of duplicate names, we generate new filenames using the last three digits of the timestamp.

    :param filename: real file name

    :return
        fake file name
    """
    return f"{os.path.splitext(filename)[0]}_{str(time.time())[-3:]}{os.path.splitext(filename)[1]}"


def recovery(fake_file_name: str) -> str:
    """
    To revert the filenames (we generate new filenames using the last three digits of the timestamp).

    :param fake_file_name: fake file name

    :return
        real file name
    """
    return fake_file_name.rsplit('_', 1)[0] + "." + fake_file_name.rsplit('.', 1)[-1]


def build_col_name(characters: List) -> str:
    """
    build up col name by character name

    :param characters: List type

    :return
        str
    """
    return "_".join(characters)

