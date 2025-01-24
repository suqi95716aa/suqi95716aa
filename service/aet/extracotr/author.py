import re
from lxml.html import HtmlElement

from ..core.meta import AUTHOR_PATTERN


class AuthorExtractor:
    def extract_author(self, element: HtmlElement, author_xpath: str = "") -> str:
        """
        Find publish time by text

        :param element: HtmlElement object
        :param author_xpath: specify author xpath, default None

        :return:
            `str`, author
        """
        if author_xpath:
            author = "".join(element.xpath(author_xpath))
            return author

        text = "".join(element.xpath('.//text()'))
        for pattern in AUTHOR_PATTERN:
            author_obj = re.search(pattern, text)
            if author_obj:
                return author_obj.group(1)

        return ""
