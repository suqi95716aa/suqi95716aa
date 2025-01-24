
c2_start_en = """
You are a very outstanding SQL writer, and next I will give you some suggestions and examples,
I need you to document these developments and examples, and not make any mistakes.
"""

c2_start_ans_en = """
Of course, I will do my best to help you. Please tell me your suggestions and examples, 
I will take note and ensure that no mistakes are made.
"""

c2_tip1_en = """
Tip 1:
1、When querying keywords such as `count` and `all`, please use SUM().
2、When querying counts within a date and time range, please use strftime().
3、When the query involves the keyword now or today, please use now() or the string "now".
4、Don't return any analysis of the above suggestions, just return the good ones, I remember.
"""

c2_tip2_en = """
Tip 2:
1、 Please do not use keywords such as "IN", "OR", "JOIN" that may result in additional results. Instead, use "INTERSEC" or "EXCEPT" instead,
Please also remember to use "DISTINCT" and "LIMITED" when needed.
2、 Please use the provided column names for SQL generation, and never use non-existent column names for generation.
3、 Please strictly maintain the fields in both Chinese and English in the generated SQL, and do not use English as a substitute for Chinese.
4、 In the generated SQL, please strictly follow the relationship between fields and table names, and make sure not to make incorrect references.
5、 If it involves vocabulary describing time such as this month or today, please search for the corresponding field for the time vocabulary in the provided fields for SQL generation.
Don't return any analysis of the above suggestions, just return OK, Please remember.   
"""

c2_tip_ans_en = """
OK, I remember all above suggestions.
"""

c2_question_en = """
### Only complete MySQL SQL generation without any explanation, and do not select additional columns or non-existent columns that are not explicitly requested in the query

### MySQL tables and their properties:
{TableAttr}

### Question:
# {Question}

SELECT
"""


