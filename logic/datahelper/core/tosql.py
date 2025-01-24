import copy
from typing import Union

from models.llm.spark import Spark
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from prompt.g_dh_c3 import c2_prompt_generator_zh
from models.vector.template_col_meta import template
from logic.datahelper.source.milvus import VectorParser
from util.op_thirdparty.dh_db import dh_tid_exist_templateinfo
from util.str import normalize_sql_transfrom, replace_keyword


async def generate_sql(llm: Union[Spark, DeepSeekCode, DeepSeekChat], tableinfo: str, question: str, TableExample: str) -> str:
    """
    生成SQL

    :params llm：用于通信的大模型
    :params tableinfo：表字段信息
    :params question：问题

    :return: 生成的SQL
    """
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(c2_prompt_generator_zh),
        input_keys=[
            {"keyword": "TableAttr", "text": tableinfo},
            {"keyword": "TableExample", "text": TableExample},
            {"keyword": "Question", "text": question},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    _tc_2_ans = normalize_sql_transfrom(_tc_1_ans)
    return _tc_2_ans


async def dynamic_template(session, query: str) -> str:
    """
    RAG实现模块，通过query检索最相关的场景
    :param session: 数据库Session
    :param query: 问题
    :return: 如下

    ## Example 1
    ### SQLite表和其属性
    #### 终端库存数据('品牌', '车型', '省份', '城市', '库存日期', '库存量')
    ### 问题: 本月H6国潮版国内终端库存量是多少
    ### SQL: SELECT SUM(库存量) FROM 终端库存数据 WHERE 车型 = 'H6国潮版' AND strftime('%Y-%m', 库存日期) = date('now','start of month');
    """

    vobj = VectorParser(template)
    res = vobj.queryVec(
        query=query,
        anns_field="query_vec",
        limit=1,
        search_params={
            "metric_type": "IP",
            "params": {"nprobe": 10}
        },
        outputs=["table_id", "query", "sql"]
    )

    example_count = 1
    example_str = ""
    for hits in res:
        for hit in hits:
            table_id = hit.entity.get("table_id")
            table_id_list = str(table_id).split("-")

            dy = ""
            sql = hit.entity.get("sql")
            q = hit.entity.get('query')
            for table_id in table_id_list:
                tres = await dh_tid_exist_templateinfo(session, int(table_id))
                table_name = tres[0].TableName.strip('\r\n')
                dy += f"#### {table_name}" + tres[0].TableCols.strip("\r\n") + "\n"

            example_str += f"\n## Example {example_count}\n" \
                           f"### SQLite表和其属性\n" \
                           f"{dy}" \
                           f"### 问题: {q}\n" \
                           f"### SQL: {sql}\n"

            example_count += 1
    return example_str





