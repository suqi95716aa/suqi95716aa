from typing import Tuple, Union

from functools import reduce

from util.df import detect_df_na
from models.llm.spark import Spark
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from models.base.source import SourceNativeConfig
from logic.datahelper.core.spss import spss
from logic.datahelper.core.tosql import generate_sql
from logic.datahelper.source.excel import ExcelSourceExecutor
from logic.datahelper.core.correction import fix_grammar, fix_col_val_map

from pandas import DataFrame
from loguru import logger

llm_code = DeepSeekCode()
llm_chat = DeepSeekChat()
llm_code = Spark()


async def executeNativeQA(session, query: str, source: ExcelSourceExecutor) -> Tuple[DataFrame, Union[str, None], Union[None, str]]:
    logger.info(f"当前提问的问题是:{query}")
    cols_recall_res = source.getRecall(query)
    formattedTable = source.getTableMap(cols_recall_res)
    formattedStr = '\n'.join(
        [f"# {table_name}({', '.join([col for col in info['cols']])})"
         for item in formattedTable for table_name, info in item.items()]
    )

    # dynamicTemplates = await dynamic_template(session, query)
    # print(f"当前的dynamicTemplates是：{dynamicTemplates}")
    sql = await generate_sql(llm=llm_code, tableinfo=formattedStr, question=query, TableExample="")
    sql_fix_col_val = await fix_col_val_map(llm=llm_code, origin_question=query, col_val_map=cols_recall_res, sql=sql)

    # 生成列表对应的df结构
    df_map = source.getDFMap(cols_recall_res)
    sqls = [reduce(lambda sql, item: sql.replace(item['table_name'], item['data_name']), df_map, sql) for sql in [sql, sql_fix_col_val]]
    for sheetItem in df_map: exec(f'{sheetItem["data_name"]} = sheetItem["data"]')
    for ind in range(len(sqls) * 2):
        if ind > len(sqls)-1: return DataFrame(), None, None
        try:
            logger.info(f"执行的SQL是：{sqls[ind]}")
            res = source.execute()(sqls[ind])
            if not detect_df_na(res):
                # spss_reasoning = await spss(llm_chat, res)
                res.fillna('null', inplace=True)    # 将空值填充
                return res, sqls[ind], None
        except Exception as error:
            logger.info(f"执行失败，错误是：{error}")
            sql = await fix_grammar(llm=llm_code, tableName=formattedStr, origin_question=query, sql=sql, error=str(error))
            sql = await fix_col_val_map(llm=llm_code, origin_question=query, col_val_map=cols_recall_res, sql=sql)
            sqls.append(sql)

    return DataFrame(), None, None


if __name__ == "__main__":
    llm = Spark()
    # 对本地数据源进行查找
    print(
        executeNativeQA(
            "帮我查询风险等级{是}{高}的{客户}数量，并以基础饼图展示",
            SourceNativeConfig("Excel", [r"C:\Users\zqsu3\Desktop\working\aiagent\storage\iflytek\扁平结构数据样例.xlsx"])
        )
    )
