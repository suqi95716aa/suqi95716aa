kbqa_intent_dispatch = """
    # 作为一个CHATGPT语义大模型的提示生成器，你将扮演一个文本意图区分专家的角色。接下来我将说明我的需求，你会根据我的
    需求和提示模板，并按照我的要求返回一个最合适的答案。
"""

kbqa_intent_demand = """
    # 对问题进行类别区分，你的任务是对输入的问题进行类别区分，类别和类别说明如下：
    1. 单跳问答：指的是那些可以直接从文本中找到答案的问题。这类问题通常只需要对文本进行一次简单的检索或理解，就能找到确切的答案。
    2. 多跳问答：要求理解并整合文本中的多个信息片段，才能得出答案。例如问题中带有明显的不同实例的对比的意图，或明显的需要多次推理和信息跳跃转换，最终组成答案的。
    3. 段落问答：段落问答是指在给定的段落或文本片段中寻找答案的问答任务。这种任务要求系统能够理解段落的内容，并从中提取出与问题相关的信息。
"""

kbqa_intent_example = """
    # 示例1
    ## 问题：爱因斯坦是什么学家？
    ## 答案：1
    ## 原因：爱因斯坦是物理学家，只需要在文中检索一次即可得到答案，因此可能是单跳问答。

    # 示例2
    ## 问题：爱因斯坦的理论如何影响了我们对时间和空间的看法？
    ## 答案：2
    ## 原理：本文可能在不同的片段同时提到“爱因斯坦提出了相对论”和“相对论改变了我们对时间和空间的理解”，因此可能是多跳问答。

    # 示例3
    ## 问题：总结第三大段落的内容
    ## 答案：3
    ## 原理：文中明确提到需要对段落内容进行理解，所以是段落问答。
"""

kbqa_intent_return = """
    只需要返回答案（一个范围从1~3的数字）即可，不需要解释他的内容

    ## 问题：{Question}
    ## 答案：
"""

kbqa_answer_generate = """
====== 背景 =======
    你是一个专业的语言理解专家，我需要你协助我完成从知识片段抽取对应的知识点协助我完成问题的解答。

====== 要求 =======
    请仅依据以下信息回答用户的问题。遵循以下要求：
    1. 我将在下方向你提供多个知识片段。
    2. 仅使用提供的知识片段来回答问题；
    3. 不允许调用知识片段以外的知识回答问答，只允许在知识片段里寻找答案。；
    4. 请使用Markdown格式返回。

====== 资源 =======
{Chunks}

====== 问题 =======
问题：{Question}

"""




###### quert router
TEMPLATE_QUERY_ROUTER = """
You are an expert at routing a user question to a vectorstore or web search.
The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
Use the vectorstore for questions on these topics. Otherwise, use web-search.

My question is: {question}

Only return one of binary score: vectorstore or search。
"""


# Complex problem analysis
TEMPLATE_QUERY_ANALYSER_IN_SUB = """
You are an expert in analyzing language complexity for RAG task.

I need you to analyze the given problem, 
determine how many simple sub problems are needed to reach the solution, 
and return the decomposed sub problems in a list format.
Please break down the sub questions into indivisible forms with clear query meaning.

# Demo-1
Query: "《坚如磐石》中饰演黎志田的演员在《三体》中饰演什么角色？"
Return: ["《坚如磐石》中饰演黎志田的演员是谁?", "这个演员在《三体》中饰演什么角色？"]
Analysis: The sub problems are split correctly, 
and each sub problem is pushed forward and solved, 
ultimately obtaining the solution to the original problem. And each sub problem is indivisible.

# Demo-2
Query: "王者荣耀什么时候出来的？"
Return: ["王者荣耀于2015年11月26日正式上线?"]
Analysis: The sub problems are split correctly, 
and each sub problem is pushed forward and solved, 
ultimately obtaining the solution to the original problem. And each sub problem is indivisible.

# Demo-3
Query: "如何选择有监督和无监督?"
Return: ["有监督学习和无监督学习的定义是什么？", "有监督学习和无监督学习的应用场景有哪些？", "如何根据任务需求选择有监督学习或无监督学习？"]
Analysis: Sub problem splitting error, 
sub problem 1 "有监督学习和无监督学习的定义是什么?" 
can be further split into ["有监督学习的定义是什么?", "无监督学习的定义是什么?"]

Query: {query}
Return: 
"""

# Grade doc
TEMPLATE_GRADE_DOC = """
You are a grader assessing relevance of a retrieved document to a user question. \n 
Here is the retrieved document: \n\n {context} \n\n
Here is the user question: {query} \n
If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.
"""


# Generate answer
TEMPLATE_GENERATE = """
You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question, And extract the main meaning.
If you don't know the answer, just say that you don't know. Use ten sentences maximum and keep the answer concise.

Question: \n{query} 
Previous context(if not empty, please use as context): \n{pre_context}
Entities: \n{entities}
Relationships: \n{relationships}
Context: \n{context} 
Answer:
"""


# Generate vs docs
TEMPLATE_GENERATE_V_DOCS = """
You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
Here are the facts:
\n ------- \n
{documents} 
\n ------- \n
Here is the answer: {generation}
Give a binary score 'yes' or 'no' to indicate whether the answer is grounded in / supported by a set of facts.
"""


# Generate vs Query
TEMPLATE_GENERATE_V_QUERY = """
You are a grader assessing whether an answer is useful to resolve a question. \n 
Here is the answer:
\n ------- \n
{generation} 
\n ------- \n
Here is the query: {query}
Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question.
"""


# (Hyde) Generate fake answer with llm
TEMPLATE_HYDE = """
Please  write a short introductory passage to anwser the question
Query: {query}
Passage:
"""

#








