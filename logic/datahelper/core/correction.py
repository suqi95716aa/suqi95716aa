import copy
import json
from typing import List

from util.str import normalize_sql_transfrom, replace_keyword
from prompt.g_dh_c3 import c3_prompt_correction_generator_zh, c3_prompt_col_val_generator_zh


async def fix_grammar(
        llm,
        tableName: str = None,
        origin_question: str = None,
        sql: str = None,
        error: str = None
) -> str:
    """
    generate SQL

    :param llm： 用于通信的模型
    :param tableName: 表格信息
    :param origin_question: 原始的问题（清洗之后）
    :param sql：生成错误的sql
    :param error：具体的sql执行错误原因

    :return: 自动修正过后的SQL
    """
    # 提示词清洗
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(c3_prompt_correction_generator_zh),
        input_keys=[
            {"keyword": "TableName", "text": tableName},
            {"keyword": "Question", "text": origin_question},
            {"keyword": "Sql", "text": sql},
            {"keyword": "Error", "text": error},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    _tc_2_ans = normalize_sql_transfrom(_tc_1_ans)
    return _tc_2_ans


async def fix_col_val_map(
        llm,
        origin_question: str = None,
        col_val_map: List = None,
        sql: str = None,
) -> str:
    where_clause = sql.split("FROM ", 1)[-1]
    used_cols = {
        col_info["column_name"]: col_val
        for db_info in col_val_map
        for table_info in db_info["db_schema"]
        for col_info in table_info["column_map"]
        for col_val in col_info["column_contents"]
        if str(col_val) in origin_question
    }

    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(c3_prompt_col_val_generator_zh),
        input_keys=[
            {"keyword": "Question", "text": origin_question},
            {"keyword": "Col_Value_Map", "text": json.dumps(used_cols, ensure_ascii=False)},
            {"keyword": "Sql", "text": sql},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    _tc_2_ans = normalize_sql_transfrom(_tc_1_ans)
    return _tc_2_ans


