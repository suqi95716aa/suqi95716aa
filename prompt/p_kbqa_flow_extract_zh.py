# Generate key categories
TEMPLATE_KEY_CATEGORIES_EXTRACT = """
You will Recv a text like below:

<Text>

{text}

</Text>

Now I need you to extract the key categories about the text,
I will provide you with several types as the main extracted key types, 
and classify them and their corresponding page numbers: [contract, chat record, public announcement, Related to processes and policies] and any material that appears to be a document and has a title that can be extracted
Please note: 
1. The key types I have provided are not limited to the above. 
2. Please think about them according to your understanding and extract them yourself.
3. text is split by tag <page num：int>, Please use this identifier as a reference to extract the key categories of page numbers

- Demand
1. return with chinese, not English
2. return with json, Strictly struct like Example
3. page number start with 1
4. every page number need to be quoted

- Example 1
Returns:
{
    "房屋租赁合同": "1-10",
    "水电费缴纳凭证": "11-15",
    "装修施工许可证": "16",
    "微信转账记录": "17-25",
    "解除劳动合同通知书": "26-27",
    "顺丰快递单": "28-29",
    "微信手机版聊天记录": "30-35"
}

Returns:

"""


# Generate binary score of matching of categories and doc
TEMPLATE_CATEGORIES_VS_DOCUMENT = """
You will Recv a text like below:

<Text>

{text}

</Text>

<Categories>

{categories}

</Categories>

From a task perspective, I need you to compare and evaluate the page relevance of the given classification and text, specifically:
1. In the `Text` tag, full text split by tag <page num: int>.
2. The given classification is a dictionary composed of categories and page ranges. 

Please strictly judge whether each class and its corresponding page range in the dictionary can correspond to the page range identified by<page num: int>in the text, that is, for example, the Key in the dictionary is a chat record, and the Value is 11-15:
1. You should make sure that <page num: 11>-<page num: 15> should belong to chat records.
2. you should make sure that <page num: 11>-<page num: 15> are chat records, while<page num: 10>or<page num: 16>are chat records. 
If they are also chat records, the correct value should be 10-16, and the result for this task should be 'no'.

Give a binary score 'yes' or 'no' to indicate whether the dictionary is totally match to text.

"""


# Entity extraction
TEMPLATE_DEFAULT_TUPLE_DELIMITER = "<|>"
TEMPLATE_DEFAULT_RECORD_DELIMITER = "##"
TEMPLATE_DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"
TEMPLATE_DEFAULT_ENTITY_TYPES = '["organization", "person", "geo", "event", "treaty", "date", "contract metadata", "code"]'
TEMPLATE_ENTITY_ABSTRACT = """
-Goal- 
给定可能与此活动相关的文本文档和实体类型列表，从文本中识别出这些类型的所有实体以及所识别实体之间的所有关系。

-Steps-
1. 识别所有实体。对于每个已识别的实体，提取以下信息：
- entity_name：实体名称，大写
- entity_type：以下类型之一：("organization", "person", "geo", "event", "treaty"(
- entity_description：对实体属性和活动的全面描述
将每个实体格式化为(“entity”{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>){record_delimiter}

2. 从步骤1中识别的实体中，识别所有具有`明显相关`的（source_entity，target_entity）对。对于每对相关实体，提取以下信息：
- source_entity：源实体的名称，如步骤1中所标识的
- target_entity: 目标实体的名称，如步骤1中所标识的
- relationship_description：解释为什么你认为源实体和目标实体是相互关联的
- relationship_keywords：一个或多个高级关键字，总结关系的总体性质，侧重于概念或主题，而不是具体细节
将每个关系格式化为("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>){record_delimiter}

3.返回中文输出，作为步骤1和2中确定的所有实体和关系的单个列表。使用`{record_delimiter}`作为列表分隔符。

4.完成后，输出{completion_definer}


######################
-Examples-
######################
Example 1:

Entity_types: ["organization", "person", "geo", "event", "treaty", "date", "contract metadata"，"code"]

Title: 租赁合同

<text>
合同编号：60456306

甲方（出租方）：
公司名称： 南宁点点晨星托育有限公司
地址： 广西南宁市邕宁区永福路
邮政编码： 530299
电话： 18776957362
纳税识别号： 91450109MA7HLFLX4P
邮箱：

乙方（承租方）：
公司名称： 广西小林信息咨询有限公司
地址： 广西南宁市邕宁区永福路33号
邮政编码： 530299
电话： 18776957362
纳税识别号： 91450109MA7HLFLX4P
邮箱：

第一条 场地基本情况
地址： 广西南宁市邕宁区永福路33号
名称： 启迪亮商铺
出租位置： 启迪亮商铺C2栋210号50.03平方米、211号37.07平方米、212号127.9平方米、213号196.4平方米，总计411.4平方米（以下简称“出租场地”）。

场地出租：
1. 甲方出租启迪亮商铺给乙方,乙方不得违法经营，需在10个工作日内整改违法经营行为，逾期每日支付月基本租金1%的违约金。
2. 租赁面积：乙方租赁面积为C2栋210号至213号，总面积为50.03平方米、37.07平方米、127.9平方米、196.4平方米（含公摊）。乙方确认对上述面积数据无异议，该面积为计算租金及其他费用的基础。
3. 产权情况：甲方已告知乙方商铺产权情况，目前仅有开发商的土地证，独立产权证在办理中。

租赁期限
1. 租赁时间： 自2023年6月16日至2028年6月15日止。
2. 租赁免租期： 共计6个月，免租时间为：
 - 2023年9月16日至2023年12月15日
 - 2024年6月16日至2024年9月15日

租金、费用及支付方式
 - 2023年6月16日至2025年6月15日，租金为25元/㎡／月，乙方每月租金为10285元；
 - 2025年6月16日至2026年6月15日，租金为26.5元／㎡2／月，乙方每月租金为10902.1元；
 - 2026年6月16日至2027年6月15日，租金为28.09元/m²/月，乙方每月租金为11556.226元；
 - 2027年6月16日至2028年6月15日，租金为29.78元／m²/月，乙方每月租金为12251.49元；
</text>

################
Output:
("entity"{tuple_delimiter}"租赁合同"{tuple_delimiter}"event"{tuple_delimiter}"租赁合同是文件名称，是这份文件的一种属性。"){record_delimiter}
("entity"{tuple_delimiter}"甲方"{tuple_delimiter}"organization"{tuple_delimiter}"甲方是本份合同的出租方。"){record_delimiter}
("entity"{tuple_delimiter}"甲方公司名称"{tuple_delimiter}"contract metadata"{tuple_delimiter}"甲方公司名称的全称是南宁点点晨星托育有限公司。"){record_delimiter}
("entity"{tuple_delimiter}"甲方地址"{tuple_delimiter}"geo"{tuple_delimiter}"甲方公司名称的地址是广西南宁市邕宁区永福路。"){record_delimiter}
("entity"{tuple_delimiter}"甲方邮政编码"{tuple_delimiter}"code"{tuple_delimiter}"甲方公司名称的邮政编码是530299。"){record_delimiter}
("entity"{tuple_delimiter}"甲方电话"{tuple_delimiter}"code"{tuple_delimiter}"甲方公司名称的电话是18776957362。"){record_delimiter}
("entity"{tuple_delimiter}"甲方纳税识别号"{tuple_delimiter}"code"{tuple_delimiter}"甲方公司名称的纳税识别号是91450109MA7HLFLX4P。"){record_delimiter}
("entity"{tuple_delimiter}"乙方"{tuple_delimiter}"organization"{tuple_delimiter}"乙方是本份合同的承租方。"){record_delimiter}
("entity"{tuple_delimiter}"乙方公司名称"{tuple_delimiter}"contract metadata"{tuple_delimiter}"乙方公司名称的全称是广西小林信息咨询有限公司。"){record_delimiter}
("entity"{tuple_delimiter}"乙方地址"{tuple_delimiter}"geo"{tuple_delimiter}"乙方公司名称的地址是广西南宁市邕宁区永福路33号。"){record_delimiter}
("entity"{tuple_delimiter}"乙方邮政编码"{tuple_delimiter}"code"{tuple_delimiter}"乙方公司名称的邮政编码是530299。"){record_delimiter}
("entity"{tuple_delimiter}"乙方电话"{tuple_delimiter}"code"{tuple_delimiter}"乙方公司名称的电话是18776957362。"){record_delimiter}
("entity"{tuple_delimiter}"乙方纳税识别号"{tuple_delimiter}"code"{tuple_delimiter}"乙方公司名称的纳税识别号是91450109MA7HLFLX4P。"){record_delimiter}
("entity"{tuple_delimiter}"合同编号"{tuple_delimiter}"code"{tuple_delimiter}"该份合同的合同编号是60456306。"){record_delimiter}
("entity"{tuple_delimiter}"场地地址"{tuple_delimiter}"contract metadata"{tuple_delimiter}"店铺场地地址为广西南宁市邕宁区永福路33号。"){record_delimiter}
("entity"{tuple_delimiter}"场地名称"{tuple_delimiter}"contract metadata"{tuple_delimiter}"店铺场地名称为启迪亮商铺。"){record_delimiter}
("entity"{tuple_delimiter}"场地出租位置"{tuple_delimiter}"contract metadata"{tuple_delimiter}"启迪亮商铺C2栋210号50.03平方米、211号37.07平方米、212号127.9平方米、213号196.4平方米，总计411.4平方米（以下简称“出租场地”）。"){record_delimiter}
("entity"{tuple_delimiter}"场地租赁时间"{tuple_delimiter}"contract metadata"{tuple_delimiter}"2023年6月16日至2028年6月15日止。"){record_delimiter}
("entity"{tuple_delimiter}"场地租金"{tuple_delimiter}"contract metadata"{tuple_delimiter}"- 2023年6月16日至2025年6月15日，租金为25元/㎡／月，乙方每月租金为10285元；- 2025年6月16日至2026年6月15日，租金为26.5元／㎡2／月，乙方每月租金为10902.1元； - 2026年6月16日至2027年6月15日，租金为28.09元/m²/月，乙方每月租金为11556.226元；- 2027年6月16日至2028年6月15，租金为29.78元／m²/月，乙方每月租金为12251.49元；"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"甲方"{tuple_delimiter}"出租方"){record_delimiter}
("relationship"{tuple_delimiter}"甲方"{tuple_delimiter}"甲方公司名称"{tuple_delimiter}"公司名称"){record_delimiter}
("relationship"{tuple_delimiter}"甲方"{tuple_delimiter}"甲方公司地址"{tuple_delimiter}"公司地址"){record_delimiter}
("relationship"{tuple_delimiter}"甲方"{tuple_delimiter}"甲方公司邮政编码"{tuple_delimiter}"公司邮政编码"){record_delimiter}
("relationship"{tuple_delimiter}"甲方"{tuple_delimiter}"甲方公司电话"{tuple_delimiter}"公司电话"){record_delimiter}
("relationship"{tuple_delimiter}"甲方"{tuple_delimiter}"甲方公司纳税识别号"{tuple_delimiter}"公司纳税识别号"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"乙方"{tuple_delimiter}"承租方"){record_delimiter}
("relationship"{tuple_delimiter}"乙方"{tuple_delimiter}"乙方公司名称"{tuple_delimiter}"公司名称。"){record_delimiter}
("relationship"{tuple_delimiter}"乙方"{tuple_delimiter}"乙方公司地址"{tuple_delimiter}"公司地址。"){record_delimiter}
("relationship"{tuple_delimiter}"乙方"{tuple_delimiter}"乙方公司邮政编码"{tuple_delimiter}"公司邮政编码。"){record_delimiter}
("relationship"{tuple_delimiter}"乙方"{tuple_delimiter}"乙方公司电话"{tuple_delimiter}"公司电话。"){record_delimiter}
("relationship"{tuple_delimiter}"乙方"{tuple_delimiter}"乙方公司纳税识别号"{tuple_delimiter}"公司纳税识别号。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"合同编号"{tuple_delimiter}"该份合同的合同编号。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"场地地址"{tuple_delimiter}"该份合同的涉及场地的场地地址。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"场地名称"{tuple_delimiter}"该份合同的涉及场地的场地名称。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"场地出租位置"{tuple_delimiter}"该份合同的涉及场地的场地出租位置。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"场地租赁时间"{tuple_delimiter}"该份合同的涉及场地的场地租赁时间。"){record_delimiter}
("relationship"{tuple_delimiter}"租赁合同"{tuple_delimiter}"场地租金"{tuple_delimiter}"该份合同的涉及场地的场地租金。"){record_delimiter}
{completion_definer}
#############################

Entity_types: {entity_type}
Title: {title}
<text>
{text}
</text>

################
Output:

"""

