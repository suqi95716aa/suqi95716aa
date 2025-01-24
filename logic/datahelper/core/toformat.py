"""
该模块主要用于生成数据洞察相关的信息

"""
import copy
import json
import random
from typing import Union, Dict

from models.llm.spark import Spark
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
# from prompt.g_dh_c3 import spss_intent_detector_zh
from util.str import replace_keyword

from pandas import DataFrame


async def generate_insight_report(llm: Union[Spark, DeepSeekCode, DeepSeekChat], df: DataFrame) -> str:

    """
    生成洞察报告

    :params llm：用于通信的大模型
    :params df：dataframe

    :return: 洞察报告描述
    """
    dfFormatStr = generate_df_format(df)

    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(spss_intent_detector_zh),
        input_keys=[
            {"keyword": "insight_tip_format", "text": dfFormatStr},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    return _tc_1_ans


def generate_df_format(df: DataFrame) -> str:
    result = dict()
    num_columns = df.select_dtypes(include=["number"]).columns
    str_columns = df.select_dtypes(exclude=["number"]).columns

    # 数值列处理
    for col in num_columns:
        col_result = {}
        metrics = ["最大值", "最小值", "中位数", "标准差", "方差"]
        weights = [0.2, 0.2, 0.2, 0.15, 0.1]
        selected_metrics = random.choices(metrics, weights, k=2)

        for metric in selected_metrics:
            if metric == "最大值":
                max_value = df[col].max()
                max_row = df[df[col] == max_value].iloc[0].to_dict()
                col_result["最大值"] = int(max_value)
            elif metric == "最小值":
                min_value = df[col].min()
                min_row = df[df[col] == min_value].iloc[0].to_dict()
                col_result["最小值"] = int(min_value)
            elif metric == "中位数":
                median_value = df[col].median()
                col_result["中位数"] = int(median_value)
            # elif metric == "众数":
            #     mode_value = df[col].mode().iloc[0]
            #     col_result["众数"] = mode_value
            elif metric == "方差":
                variance_value = df[col].var()
                col_result["方差"] = int(variance_value)
            elif metric == "标准差":
                std_dev_value = df[col].std()
                col_result["标准差"] = int(std_dev_value)

        result[col] = col_result

    # 字符串列处理
    for col in str_columns:
        result[col] = {"类型": str(df[col].dtype)}

    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    import pandas as pd
    import asyncio

    file_path = r'C:\Users\zqsu3\Desktop\excel表格数据源\扁平结构数据样例.xlsx'  # 替换为你的Excel文件路径
    df = pd.read_excel(file_path)
    # formatted_df = generate_df_format(df)
    # print(formatted_df)
    llm = Spark()
    # llm = DeepSeekChat()
    ans = asyncio.run(generate_insight_report(llm, df))
    print(ans)





