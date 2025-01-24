import re

from lxml import etree
from lxml.html import HtmlElement

from ..core.meta import TITLE_SPLIT_CHAR_PATTERN, TITLE_HTAG_XPATH
from ..util import longest_common_sub_string


class TitleExtractor:

    def _extract_title_by_xpath(self, element: HtmlElement, title_xpath: str = "") -> str:
        """
        Find element by xpath

        :param element: HtmlElement object
        :param title_xpath: specify title xpath, default None

        :return:
            `str`, title
        """
        if not title_xpath: return ""
        titles = element.xpath(title_xpath)

        if titles and isinstance(titles[0], str):
            return titles[0]
        elif titles and isinstance(titles[0], etree._Element):
            return titles[0].text
        else:
            return ""

    def _extract_title_by_tag(self, element: HtmlElement) -> str:
        """
        Find element by tag `<title>`

        :param element: HtmlElement object

        :return:
            `str`, title
        """
        titles = element.xpath("//title/text()")
        if not titles: return ""

        title = re.split(TITLE_SPLIT_CHAR_PATTERN, titles[0])
        if not title: return ""
        return title[0] if len(title[0]) >= 4 else titles[0]

    def _extract_title_by_htag(self, element: HtmlElement) -> str:
        """
        Find element by tag `<h>`

        :param element: HtmlElement object

        :return:
            `str`, title
        """
        title_list = element.xpath(TITLE_HTAG_XPATH)
        if not title_list: return ''
        return title_list[0]

    def _extract_title_by_htag_and_title(self, element: HtmlElement) -> str:
        """
        Generally, we always consider the news title contained in title, but other words,
        e.g.
        aet becoming the best module of news extractor - 163.com
        Tencent new： aet becoming the best module of news extractor

        Sametime, always contain the new title in some tag `<h>`.

        Therefore, by matching the text in the h tag with the title in both directions,
        the most suitable string can be found as the news title.
        However, it is necessary to consider that the title and the text in the h tag may contain special characters,
        so it is not possible to determine this by directly checking if the text in the h tag is in the title.
        Here, the longest common substring needs to be considered

        :param element: HtmlElement object

        :return:
            `str`, title
        """
        h_tag_texts_list = element.xpath('(//h1//text() | //h2//text() | //h3//text() | //h4//text() | //h5//text())')
        title_text = ''.join(element.xpath('//title/text()'))
        news_title = ''
        for h_tag_text in h_tag_texts_list:
            lcs = longest_common_sub_string(title_text, h_tag_text)
            if len(lcs) > len(news_title):
                news_title = lcs
        return news_title if len(news_title) > 4 else ""

    def extract_title(self, element: HtmlElement, title_xpath: str = "") -> str:
        """
        :param element: HtmlElement object
        :param title_xpath: specify title xpath, default None

        :return:
            `str`, title
        """

        return (
                self._extract_title_by_xpath(element, title_xpath) or
                self._extract_title_by_htag_and_title(element) or
                self._extract_title_by_tag(element) or
                self._extract_title_by_htag(element)
         )
