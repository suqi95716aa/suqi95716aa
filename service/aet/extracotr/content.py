import re
import json
from typing import List, Union, Dict

from ..util import iter_node
from ..core.meta import HIGH_WEIGHT_ARRT_KEYWORD

import numpy as np
from lxml.html import HtmlElement
from lxml.html import etree

PUNCTUATION = set('''！，。？、；：“”‘’《》%（）,.?:;'"!%()''')
HIGH_WEIGHT_KEYWORD_PATTERN = re.compile('|'.join(HIGH_WEIGHT_ARRT_KEYWORD), flags=re.I)


class ContentExtractor:
    def __init__(self, content_tag: str = "p"):
        """
        :param content_tag: Where is the main content of the article located within the tags?
        """
        self.node_info = dict()
        self.element_text_cache = {}
        self.content_tag = content_tag

    def get_all_text_of_element(self, elements: Union[List[HtmlElement], HtmlElement]) -> List:
        """
        get all text of the element (include sub element)

        :param elements: list of HtmlElement

        :return:
            `list`, list of text from one node
        """
        if not isinstance(elements, list):
            elements = [elements]

        text_list = list()
        for element in elements:
            element_flag = element.getroottree().getpath(element)
            if element_flag in self.element_text_cache:
                text_list.extend(self.element_text_cache[element_flag])
            else:
                element_text_list = list()
                all_nodes = element.xpath(".//* | .//text()[normalize-space()]")
                for node in all_nodes:
                    if isinstance(node, etree._Element):
                        if node.tag == "img" and node.get('src'):
                            element_text_list.append(f"<img src='{node.get('src')}'>" + "</img>")
                    else:
                        # When `len(parent)` == 0, it means text included in tag,
                        # otherwise, it's text only
                        parent = node.getparent()
                        text = f"<{parent.tag}>{str(node).strip()}</{parent.tag}>" if \
                               str(node) and parent.text and len(parent) == 0 and parent.text.strip() == str(node).strip() else \
                               node.strip()
                        clear_text = re.sub(' +', ' ', text, flags=re.S)
                        element_text_list.append(clear_text.replace('\n', ''))

                self.element_text_cache[element_flag] = element_text_list
                text_list.extend(element_text_list)

        return text_list

    def _calc_text_density(self, element: HtmlElement) -> Dict:
        """
        Formula：

               Ti - LTi
        TDi = -----------
              TGi - LTGi

        Ti: The word count of the string (at node i)
        LTi: The word count of the string with links (at node i)
        TGi: The number of tags (at node i)
        LTGi: The number of tags with links (at node i)

        :return:
            `Dict`
        """

        def _increase_tag_weight(ti: int, element: HtmlElement) -> int:
            tag_class = element.get("class", "")
            if HIGH_WEIGHT_KEYWORD_PATTERN.search(tag_class):
                return 2 * ti
            return ti

        def need_skip_ltgi(Ti, Lti):
            """
            Sometimes, some tag will be added in main text, like WIKI:
            <div>I'm <a>Wiki</a href=""></div>

            In this situation, tgi = ltgi = 2, The denominator of the formula is 0.
            In order to link this situation with the entire list page Distinguish the situation, so make a judgment.
            Check the quantity of text in the hyperlinks of all a tags under the node and compare it with the current node
            The ratio of all text quantities below. If the proportion of text in hyperlinks is very small,
            then LTGI should ignore it at this time

            :param Ti: The word count of the string (at node i)
            :param Lti: The word count of the string with links (at node i)

            :return:
                `bool`
            """
            if Lti == 0:
                return False
            return Ti // Lti > 10  # The number of characters in the main text is more than ten times the number of link characters

        ti_text = "\n".join(self.get_all_text_of_element(element))
        ti = len(ti_text)
        ti = _increase_tag_weight(ti, element)

        a_tag_list = element.xpath(".//a")
        lti = len(''.join(self.get_all_text_of_element(a_tag_list)))
        tgi = len(element.xpath('.//*'))
        ltgi = len(a_tag_list)
        if (tgi - ltgi) == 0:
            if not need_skip_ltgi(ti, lti):
                return {'density': 0, 'ti_text': ti_text, 'ti': ti, 'lti': lti, 'tgi': tgi, 'ltgi': ltgi}
            else:
                ltgi = 0
        density = (ti - lti) / (tgi - ltgi)
        return {'density': density, 'ti_text': ti_text, 'ti': ti, 'lti': lti, 'tgi': tgi, 'ltgi': ltgi}

    def count_text_tag(self, element: HtmlElement, tag: str = "p") -> int:
        """
        get total length of `p` tag and `text()`

        :param element: HtmlElement
        :param tag: default `p`

        :return:
        """
        tag_num = len(element.xpath(f'.//{tag}'))
        direct_text = len(element.xpath('text()'))
        return tag_num + direct_text

    def calc_sbdi(
            self,
            text: str,
            ti: Union[int, float],
            lti: Union[int, float]
    ) -> Union[int, float]:
        """
                Ti - LTi
        SbDi = --------------
                 Sbi + 1

        SbDi: symbol density
        Sbi：symbol count

        :param text: text of node
        :param Ti: The word count of the string (at node i)
        :param LTi: The word count of the string with links (at node i)

        :return:
            `Union[int, float]`, sbdi
        """
        count = 0
        for char in text:
            if char in PUNCTUATION:
                count += 1

        sbi = count
        sbdi = (ti - lti) / (sbi + 1)
        return sbdi or 1  # if 0, log() will led to error

    def calc_new_score(self):
        """
        Formula:
            score = 1 * ndi * log10(text_tag_count + 2) * log(sbdi)

        In pager, we use log (std) here, but each density is multiplied by the same logarithm,
        and their relative sizes do not change, so we don't need to calculate them

        :return:
        """
        for node_hash, node_info in self.node_info.items():
            score = node_info['density'] * np.log10(node_info['text_tag_count'] + 2) * np.log(
                node_info['sbdi'])
            self.node_info[node_hash]['score'] = score

    def extract_content(
            self,
            element: HtmlElement,
            body_xpath: str = "//body",
            use_visiable_info: bool = False
    ):
        """

        :param element: HtmlElement object
        :param body_xpath: specify body xpath, default `//body`
        :param use_visiable_info: continue when element unvisiable

        :return:
        """
        body = element.xpath(body_xpath)[0]
        for node in iter_node(body):
            if use_visiable_info:
                if not node.attrib.get("is_visiable", True):
                    continue
                coordinate_json = node.attrib.get("coordinate", "{}")
                coordinate = json.loads(coordinate_json)
                if coordinate.get("height", 0) < 150:
                    continue
            node_hash = hash(node)
            density_info = self._calc_text_density(node)
            text_density = density_info['density']
            ti_text = density_info['ti_text']
            text_tag_count = self.count_text_tag(node, tag='p')
            sbdi = self.calc_sbdi(ti_text, density_info['ti'], density_info['lti'])
            images_list = node.xpath('.//img/@src')
            node_info = {
                'ti': density_info['ti'],
                'lti': density_info['lti'],
                'tgi': density_info['tgi'],
                'ltgi': density_info['ltgi'],
                'node': node,
                'density': text_density,
                'text': ti_text,
                'images': images_list,
                'text_tag_count': text_tag_count,
                'sbdi': sbdi
            }

            if use_visiable_info:
                node_info['is_visiable'] = node.attrib['is_visiable']
                node_info['coordinate'] = node.attrib.get('coordinate', '')
            self.node_info[node_hash] = node_info
        self.calc_new_score()
        result = sorted(self.node_info.items(), key=lambda x: x[1]['score'], reverse=True)
        return result

