from typing import List, Dict, Callable, Union

from models.llm.spark import Spark
from models.llm.deepseek import DeepSeekCode, DeepSeekChat

from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import TransformChain, SequentialChain



class Chain:
    """
    对LangChain的二次封装，主要用于对模板类的封装，便于业务使用。
    """

    def RoleChain(self, llm: Union[Spark, DeepSeekCode, DeepSeekChat], messages: List[Dict], outputKey: str = None) -> LLMChain:
        """
        分角色的预测回答
        :param llm: 用于本轮次的大模型会话
        :param messages: 按正常对话的顺序，对用例进行初始化
        :param outputKey: 定义返回的键名
        :return LLMChain : LLM节点

        Example:
            _tc = RoleChain(
                llm=llm,
                messages=[
                   {"Role": "AI", "Text": "我是AI{text}"},
                   {"Role": "Human", "Text": "我是Human"},
                   {"Role": "System", "Text": "我是System"},
                ],
                outputKey="out"
            )
            print(_tc.run({"text": "请帮我生成一个SQL用例"}))
        """
        if not all("Role" in message and "Text" in message for message in messages):
            raise ValueError(f"Require More Key: Role or Text")
        if not all(message.get("Role") in ["System", "AI", "Human"] for message in messages):
            raise ValueError(f"'Role' Key Value Error: it must contained in System\AI\Human")

        _templates = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(message.get("Text"))
            if message.get("Role") == "System" else
            AIMessagePromptTemplate.from_template(message.get("Text"))
            if message.get("Role") == "AI" else
            HumanMessagePromptTemplate.from_template(message.get("Text"))
            for message in messages
        ])
        print(_templates)
        return LLMChain(llm=llm, prompt=_templates, output_key=outputKey) \
            if outputKey else \
            LLMChain(llm=llm, prompt=_templates)

    def OnePlayChain(self, llm: Union[Spark, DeepSeekCode, DeepSeekChat], template: str, outputKey: str, *args) -> LLMChain:
        """
        单轮次预测回答
        :param llm: 用于本轮次的大模型会话
        :param template: 模板
        :param outputKey: 需要输出的key
        :param args: 需要填充的模板参数

        :return LLMChain : LLM节点

        Example:
            _tc = self.c.OnePlayChain(llm, "text:{text}", "out", "text")
            print(_tc.run({"text": 1}))
        """
        _template = PromptTemplate(
            input_variables=list(args),
            template=template
        )
        return LLMChain(llm=llm, prompt=_template, output_key=outputKey)

    def TransformChain(self, func: Callable, input: List, outputKeys: List) -> TransformChain:
        """
        自定义函数
        :param func: 自定义函数
        :param input: 承接上一流程当中的参数
        :param output: 最终输出的参数

        :return TransformChain: 自定义函数节点

        Example:
            def washSQL(inputs):
                SQLAnalysis = inputs["sqlGeneration"]
                return {"sqlPure": matches}

            self-define-callable = TransformChain(func=testcase, input=["sqlGeneration"], outputKeys=["pure"])
        """
        if not isinstance(func, Callable):
            raise Exception("Func needs type of callable...")

        return TransformChain(
            transform=func,
            input_variables=input,
            output_variables=outputKeys,
        )

    def sequentialChain(self,
                        tasks: List[Union[TransformChain, LLMChain]],
                        inputs: List,
                        outputs: List,
                        verbose: bool = True
                        ) -> SequentialChain:
        """任务节点链
        Params-Input：
            tasks: 任务列表
            inputs: 第一个任务的输入参数
            output: 过程中的输出参数
            verbose:
        Params-Output：
            SequentialChain: 序列参数

        Example:
            Test Case in test.prompt.test_process.TestProcess.test_sequentialChain_run
        """

        return SequentialChain(
            chains=tasks,
            input_variables=inputs,
            output_variables=outputs,
            verbose=verbose
        )


