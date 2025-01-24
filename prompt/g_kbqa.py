from prompt.p_kbqa_flow_query_zh import *
from prompt.p_kbqa_flow_extract_zh import *

kbqa_prompt_intent_generator_zh = [
    {"role": "user", "content": kbqa_intent_dispatch},
    {"role": "user", "content": kbqa_intent_demand},
    {"role": "user", "content": kbqa_intent_example},
    {"role": "user", "content": kbqa_intent_return},
]

kbqa_prompt_answer_generator_zh = [
    {"role": "user", "content": kbqa_answer_generate},
]


kbqa_sub_prompt_generator_zh = [
    {"role": "user", "content": TEMPLATE_QUERY_ANALYSER_IN_SUB},
]

kbqa_grade_doc_zh = [
    {"role": "user", "content": TEMPLATE_GRADE_DOC},
]

kbqa_generate_zh = [
    {"role": "user", "content": TEMPLATE_GENERATE},
]

kbqa_generate_v_docs = [
    {"role": "user", "content": TEMPLATE_GENERATE_V_DOCS},
]

kbqa_generate_v_query = [
    {"role": "user", "content": TEMPLATE_GENERATE_V_QUERY},
]

kbqa_hyde = [
    {"role": "user", "content": TEMPLATE_HYDE},
]

kbqa_key_categories = [
    {"role": "user", "content": TEMPLATE_KEY_CATEGORIES_EXTRACT},
]

kbqa_categories_v_doc = [
    {"role": "user", "content": TEMPLATE_CATEGORIES_VS_DOCUMENT},
]

kbqa_entity_abstract = [
    {"role": "user", "content": TEMPLATE_ENTITY_ABSTRACT},
]
