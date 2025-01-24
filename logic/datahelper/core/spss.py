"""
This part is to build spss process

"""
import json
import copy
from typing import Union

from util.str import replace_keyword
from models.llm.spark import Spark
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from prompt.g_dh_c3 import spss_intent_detector_zh, spss_data_exploration_zh

import pandas as pd
import numpy as np
from pandas import DataFrame
from scipy.stats import pearsonr, chi2_contingency

spss_methods = {
    "描述性分析": "描述性分析是一种基本的数据分析方法，用于总结和描述数据的基本特征，如平均值、中位数、众数、方差、标准差等。",
    "探索性数据分析": "探索性数据分析是一种用于探索数据集中的模式、趋势和关系的方法。",
    # "时间序列分析": "时间序列分析是一种用于分析随时间变化的数据的方法。它通常用于预测未来趋势、季节性变化等。"
}


async def spss(llm: Union[Spark, DeepSeekCode, DeepSeekChat], df: DataFrame) -> Union[None, str]:
    """
    进行数据分析方法

    :params llm：用于通信的大模型
    :params DataFrame：所用到的df

    :return: 数据分析方法结论
    """

    def keep_columns(df):
        count = 3

        numerical_columns = df.select_dtypes(include=[np.number]).columns
        num_numerical_columns = len(numerical_columns)

        if num_numerical_columns <= count:
            return df
        else:
            correlation_matrix = df[numerical_columns].corr(method='pearson').abs()

            sorted_correlations = correlation_matrix.unstack().sort_values(ascending=False, kind="quicksort")
            unique_sorted_correlations = sorted_correlations.drop_duplicates().reset_index()
            unique_sorted_correlations.columns = ['col1', 'col2', 'correlation']

            selected_columns = set()
            for index, row in unique_sorted_correlations.iterrows():
                if len(selected_columns) < count:
                    selected_columns.add(row['col1'])
                    selected_columns.add(row['col2'])
                else:
                    break

            if len(selected_columns) < count:
                non_numerical_columns = df.select_dtypes(exclude=[np.number]).columns
                remaining_columns = count - len(selected_columns)
                selected_columns.update(non_numerical_columns[:remaining_columns])

            return df[list(selected_columns)]

    # 1、确定所选的数据分析方法
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(spss_intent_detector_zh),
        input_keys=[
            {"keyword": "df_dtypes_map", "text": json.dumps({col: str(dtype) for col, dtype in df.dtypes.items()}, ensure_ascii=False)},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    spss_method = next((method for method in spss_methods if method in _tc_1_ans), None)
    if not spss_method: spss_method = list(spss_methods.keys())[0]

    # 2、信息相关片段抽取
    df = keep_columns(df)
    if spss_method == "描述性分析":
        spss_info = descriptive_analysis(df)
    elif spss_method == "探索性数据分析":
        spss_info = exploration_analysis(df)
    else:
        return None

    # 3、对知识进行总结
    _tc_2_input = replace_keyword(
        prompts=copy.deepcopy(spss_data_exploration_zh),
        input_keys=[
            {"keyword": "data_exploration_method", "text": spss_method},
            {"keyword": "data_extract_info", "text": spss_info},

        ]
    )
    _tc_2_ans = await llm._call(prompt=_tc_2_input, temperature=0.2)
    return _tc_2_ans


def descriptive_analysis(df: pd.DataFrame) -> str:
    """
    描述性分析中，将df中每个字段进行抽取

    :param df:
    :return:
    """
    def default_convert(obj):
        if isinstance(obj, np.int64):
            return int(obj)
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")

    # 初始化结果字典
    result = {}

    # 遍历数据框的每个字段
    for column in df.columns:
        # 如果字段是数值类型
        if pd.api.types.is_numeric_dtype(df[column]):
            # 计算最大值、最小值、中位数、众数、方差和标准差
            max_value = df[column].max()
            min_value = df[column].min()
            median_value = df[column].median()
            mode_value = df[column].mode().iloc[0]  # 取众数的第一个值
            variance_value = df[column].var()
            std_dev_value = df[column].std()

            # 获取最大值和最小值所在的行
            max_value_row = df[df[column] == max_value].iloc[0]
            min_value_row = df[df[column] == min_value].iloc[0]

            # 将结果存储到字典中，并将int64类型转换为str
            result[column] = {
                "最大值": {
                    "数值内容": str(max_value),
                    "最大值关联的字段": max_value_row.to_dict()
                },
                "最小值": {
                    "数值内容": str(min_value),
                    "最小值关联的字段": min_value_row.to_dict()
                },
                "中位数": median_value,
                "众数": mode_value if not isinstance(mode_value, pd._libs.tslibs.timestamps.Timestamp) else str(mode_value),
                "方差": variance_value,
                "标准差": std_dev_value
            }
        else:
            # 如果字段是非数值和非时间类型，统计重复值占比前三名
            value_counts = df[column].value_counts(normalize=True)
            top_three_values = value_counts.head(3)
            result[column] = {
                "重复值占比前三名": top_three_values.to_dict()
            }

    # 将结果字典转换为JSON字符串，确保所有值都是JSON可序列化的类型
    return json.dumps(result, ensure_ascii=False, default=default_convert)


def exploration_analysis(df: pd.DataFrame) -> str:
    """
    数据探索分析中，将df中每个字段进行相关性总结

    :param df:
    :return:
    """
    # 使用数值型列的均值填充缺失值
    numerical_columns = df.select_dtypes(include=['number']).columns
    df.loc[:, numerical_columns] = df[numerical_columns].fillna(df[numerical_columns].mean())

    # 使用非数值型列的众数填充缺失值（如果存在）
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        mode = df[col].mode()
        if not mode.empty:
            df[col] = df[col].fillna(mode.iloc[0])

    # 仅对数值型列进行描述性统计
    descriptive_stats = df[numerical_columns].describe(include='all')
    # 计算数值型列的相关系数矩阵
    correlation_matrix = df[numerical_columns].corr()

    # 准备JSON数据
    json_data = {
        "Descriptive Statistics": descriptive_stats.to_dict(),
        "Correlation Matrix": correlation_matrix.to_dict(),
        "Pairwise Analysis": {}
    }

    # 双变量分析
    for col1 in df.columns:
        for col2 in df.columns:
            if col1 != col2:
                # 检查两个列是否都是数值型
                if df[col1].dtype in ['float64', 'int64'] and df[col2].dtype in ['float64', 'int64']:
                    # 计算数值型变量之间的皮尔逊相关系数
                    corr, _ = pearsonr(df[col1], df[col2])
                    json_data["Pairwise Analysis"][f"{col1} vs {col2} (Pearson Correlation)"] = corr
                # 对于分类型变量的卡方检验，我们需要单独处理
                elif df[col1].dtype == 'object' and df[col2].dtype == 'object':
                    # 计算分类型变量之间的卡方检验结果
                    chi2, p, dof, expected = chi2_contingency(pd.crosstab(df[col1], df[col2]))
                    json_data["Pairwise Analysis"][f"{col1} vs {col2} (Chi-Square Test)"] = {
                        "Chi-Square": chi2,
                        "P-value": p,
                        "Degrees of Freedom": dof,
                        "Expected Frequencies": expected.tolist()
                    }

    # 将结果转换为JSON格式
    json_result = json.dumps(json_data, indent=4, ensure_ascii=False)

    return json_result


# if __name__ == "__main__":
#     import asyncio
#     import pandas as pd
#     import json
#
#     llm = DeepSeekChat()
#
#     # 读取CSV文件
#     df = pd.read_excel(r"C:\Users\zqsu3\Desktop\新建XLSX 工作表.xlsx")
#
#     # # 转换字段和字段类型为JSON格式
#     json_dtype = json.dumps({col: str(dtype) for col, dtype in df.dtypes.items()}, ensure_ascii=False)
#     m = asyncio.get_event_loop().run_until_complete(spss(llm, df))
#
#     print(m)




