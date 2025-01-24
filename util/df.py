from pandas import DataFrame


def detect_df_na(df: DataFrame):
    return df.isna().all().all()


def detect_dtype(df):
    """判断df列值类型"""
    dtype_dict = {}
    for column in df.columns:
        uniq_values = df[column].drop_duplicates()
        if uniq_values.dtypes == object:
            dtype_dict[column] = 'string'
        else:
            dtype_dict[column] = 'number'
    return dtype_dict
