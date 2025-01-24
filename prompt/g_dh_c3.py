from prompt.p_dh_c3_zh import *
from prompt.spss_zh import *


c1_prompt_generator_zh = [
    {"role": "user", "content": c1_explain_start_zh},
    {"role": "assistant", "content": c1_explain_end_zh},
    {"role": "user", "content": c1_explain_tip1_zh},
    {"role": "user", "content": c1_explain_question_zh}
]

c2_prompt_generator_zh = [
    {"role": "user", "content": c2_2sql_start_zh},
    {"role": "assistant", "content": c2_2sql_start_ans_zh},
    {"role": "user", "content": c2_2sql_tip1_zh},
    {"role": "assistant", "content": c2_2sql_tip_ans_zh},
    {"role": "user", "content": c2_2sql_tip2_zh},
    {"role": "assistant", "content": c2_2sql_tip_ans_zh},
    {"role": "user", "content": c2_2sql_example_zh},
    {"role": "user", "content": c2_2sql_question_zh},
]

c3_prompt_correction_generator_zh = [
    {"role": "user", "content": c3_correction_start_zh},
    {"role": "assistant", "content": c3_correction_start_ans_zh},
    {"role": "user", "content": c3_correction_tip1_zh},
    {"role": "user", "content": c3_correction_question_zh}
]

c3_prompt_col_val_generator_zh = [
    {"role": "user", "content": c3_col_val_start_zh},
    {"role": "user", "content": c3_col_val_tip1_zh},
    {"role": "user", "content": c3_col_val_exp_zh},
    {"role": "user", "content": c3_col_val_qa_zh}
]

spss_intent_detector_zh = [
    {"role": "user", "content": spss_intent_detector},
]

spss_data_exploration_zh = [
    {"role": "user", "content": spss_data_exploration_example},
    {"role": "user", "content": spss_data_exploration_intent},
]

