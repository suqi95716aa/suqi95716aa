# # 假设 Document 类和 document 对象的定义如下
# class Document:
#     def __init__(self, metadata):
#         self.metadata = metadata
#
#     def __repr__(self):
#         return f"Document(metadata={self.metadata})"
#
# # 创建一些示例 document 对象
# documents = [
#     Document({"page_num": 3, "title": "Document 1"}),
#     Document({"page_num": 5, "title": "Document 2"}),
#     Document({"page_num": 7, "title": "Document 3"}),
#     Document({"page_num": 5, "title": "Document 4"}),
# ]
#
# # 使用 filter 和 lambda 表达式筛选出 page_num 等于 5 的 document 对象
# filtered_documents = list(filter(lambda doc: doc.metadata.get("page_num") == 5, documents))
#
# # 打印筛选结果
# print(filtered_documents)


def merge_dicts_by_name(dict_list):
    merged_dict = {}

    for d in dict_list:
        name = d['name']
        desc = d['desc']

        if name in merged_dict:
            merged_dict[name]['desc'] += '<SEP>' + desc
        else:
            merged_dict[name] = {'name': name, 'desc': desc}

    # 将合并后的字典转换为列表
    merged_list = list(merged_dict.values())
    return merged_list


# 示例列表
dict_list = [
    {'name': 'Alice', 'desc': 'Engineer'},
    {'name': 'Bob', 'desc': 'Designer'},
    {'name': 'Alice', 'desc': 'Developer'},
    {'name': 'Charlie', 'desc': 'Manager'},
    {'name': 'Bob', 'desc': 'Artist'},
]

# 合并后的列表
merged_list = merge_dicts_by_name(dict_list)

# 输出结果
for item in merged_list:
    print(item)


a = "1"+"<SEP>"+"2"
print(a)



