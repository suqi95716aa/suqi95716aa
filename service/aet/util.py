from typing import List, Optional

from lxml.html import etree
from lxml.html import HtmlElement

from .core.meta import USELESS_TAG, TAGS_CAN_BE_REMOVE_IF_EMPTY, USELESS_ATTR


def longest_common_sub_string(str1: str, str2: str) -> str:
    """
    lcs(longest common sub string) is a algorithm for finding the longest common substring

    :param str1:
    :param str2:

    :return: sub string the longest common
    """
    if not all([str1, str2]):
        return ''
    matrix = [[0] * (len(str2) + 1) for _ in range(len(str1) + 1)]
    max_length = 0
    start_position = 0
    for index_of_str1 in range(1, len(str1) + 1):
        for index_of_str2 in range(1, len(str2) + 1):
            if str1[index_of_str1 - 1] == str2[index_of_str2 - 1]:
                matrix[index_of_str1][index_of_str2] = matrix[index_of_str1 - 1][index_of_str2 - 1] + 1
                if matrix[index_of_str1][index_of_str2] > max_length:
                    max_length = matrix[index_of_str1][index_of_str2]
                    start_position = index_of_str1 - max_length
            else:
                matrix[index_of_str1][index_of_str2] = 0
    return str1[start_position: start_position + max_length]


def iter_node(element: HtmlElement):
    yield element
    for sub_element in element:
        if isinstance(sub_element, HtmlElement):
            yield from iter_node(sub_element)


def remove_node(node: HtmlElement) -> Optional[HtmlElement]:
    """
    this is a in-place operation, not necessary to return
    :param node:
    :return:
    """
    parent = node.getparent()
    if parent is not None:
        parent.remove(node)


def remove_noise_node(element: HtmlElement, noise_xpath_list: List[str]) -> Optional[HtmlElement]:
    if not noise_xpath_list:
        return None
    for noise_xpath in noise_xpath_list:
        nodes = element.xpath(noise_xpath)
        for node in nodes:
            remove_node(node)
    return element


def is_empty_element(node: HtmlElement):
    return not node.getchildren() and not node.text


def drop_tag(node: HtmlElement):
    """
    only delete the tag, but merge its text to parent.
    :param node:
    :return:
    """
    parent = node.getparent()
    if parent is not None:
        node.drop_tag()

def normalize_node(element: HtmlElement):
    etree.strip_elements(element, *USELESS_TAG)
    for node in iter_node(element):
        # inspired by readability.
        if node.tag.lower() in TAGS_CAN_BE_REMOVE_IF_EMPTY and is_empty_element(node):
            remove_node(node)

        # merge text in span or strong to parent p tag
        if node.tag.lower() == 'p':
            etree.strip_tags(node, 'span')
            etree.strip_tags(node, 'strong')

        # if a div tag does not contain any sub node, it could be converted to p node.
        if node.tag.lower() == 'div' and not node.getchildren():
            node.tag = 'p'

        if node.tag.lower() == 'span' and not node.getchildren():
            node.tag = 'p'

        # remove empty p tag
        if node.tag.lower() == 'p' and not node.xpath('.//img'):
            if not (node.text and node.text.strip()):
                drop_tag(node)

        class_name = node.get('class')
        if class_name:
            if class_name in USELESS_ATTR:
                remove_node(node)
                break

    return element