spss_intent_detector = """
    ## 你是一个语言理解和推断大师，接下来我将要进行一份数据分析的工作，但是在此之前，我需要你帮我推断出给定的DataFrame到底适合什么类型的分析形式。

    对于分析的目标，判断到底需要使用下述哪种方法进行分析：
    1. 描述性分析：描述性分析是一种基本的数据分析方法，用于总结和描述数据的基本特征，如平均值、中位数、众数、方差、标准差等。
    2. 探索性数据分析：探索性数据分析是一种用于探索数据集中的模式、趋势和关系的方法。它通常包括数据可视化、数据清洗、数据转换等步骤。

    我的要求是：
    1. DataFrame的字段和类型将会以JSON形式进行提供。
    2. 请结合DataFrame的字段和类型以及字段名称的关联度，判断是否需要使用哪种分析方法。
    3. 如果字段类型不包含时间类型，请不要使用时间序列分析。

      ###  DataFrame的字段和类型: {df_dtypes_map}
      ###  答案：

    请只给出分析方法的名称，不需要返回任何的解释，若字段和类型没有分析的必要，请返回"不需要数据分析"。
"""

spss_data_exploration_intent = """
    ## 你是一个数据分析专家，我需要你帮我对数据进行探索。

    请使用{data_exploration_method}的方式，对下述提供的json进行分析总结：
    {data_extract_info}

    ## 分析要求：
    1. 总结不要出现专业的数学术语和名词, 比如平均值、方差、标准差、最大值、最小值、相关性矩阵、成对分析等;
    2. 不要将每个指标内容复述一遍，要总结。
    3. 请从这些指标趋势分析相关字段之间的联系，从你的知识从提炼这些字段名称和关联值为什么会出现这样的指标，并分析给出一个结果。
    4. 如果有需要，可以给出针对这些结论的提升意见。
    5. 如果无法从提供的字段进行分析，请给出无法分析的原因即可，不需要强行分析。
"""

spss_data_exploration_example = """
        请你按一下的格式给出结论：
            根据提供的数据，我们可以进行以下描述性分析：
            首先，我们注意到数据中的“毛利金额”、“纯利金额”和“合同金额”三个指标的平均值分别为249.99999999999983、179.5和265.0。其中，“毛利金额”和“合同金额”的平均值相近，而“纯利金额”的平均值较低。
            其次，我们注意到“毛利金额”和“合同金额”之间的相关性非常强，相关系数为0.9999999999999997，表明两者之间存在很强的正相关关系。而“纯利金额”与其他两个指标之间的相关性较弱，相关系数分别为0.03138769067588108和0.03138769067588117，表明它们之间可能没有显著的线性关系。
            总的来说，这些数据分析结果表明，“毛利金额”和“合同金额”之间存在很强的正相关关系，而“纯利金额”与其他两个指标之间的相关性较弱。这些分析结果可以帮助我们理解不同指标之间的相互作用，并为进一步的分析和决策提供参考。
            从这些指标趋势分析相关字段之间的联系，我们可以得出以下结论：
            “毛利金额”和“合同金额”之间的正相关关系可能表明，合同金额的增加会导致毛利金额的增加。这可能是因为合同金额的增加意味着公司签订了更多的合同，从而增加了公司的收入。而毛利金额是收入减去成本后的金额，因此合同金额的增加可能会导致毛利金额的增加。
            “纯利金额”与其他两个指标之间的相关性较弱，可能表明纯利金额与其他两个指标之间的关系不明显。这可能是因为纯利金额是毛利金额减去税费和其他费用后的金额，因此它与其他两个指标之间的关系可能不明显。
            总的来说，这些分析结果可以帮助我们理解不同指标之间的相互作用，并为进一步的分析和决策提供参考。
"""

