import re
from lxml.html import HtmlElement

from ..core.meta import DATETIME_PATTERN, PUBLISH_TIME_META


class PublishTimeExtractor:

    def _extract_pt_by_xpath(self, element: HtmlElement, publish_time_xpath: str) -> str:
        """
        Find element by xpath

        :param element: HtmlElement object
        :param publish_time_xpath: specify publish time xpath, default None

        :return:
            `str`, publish time
        """
        if not publish_time_xpath: return ""
        publish_time = "".join(element.xpath(publish_time_xpath))
        return publish_time

    def _extract_pt_by_meta(self, element: HtmlElement) -> str:
        """
        In some ruled news website, they like write the publish time in `meta` lable,
        so we gonne check `meta` in first priority.

        :param element: HtmlElement object

        :return:
            `str`, publish time
        """
        for xpath in PUBLISH_TIME_META:
            publish_time = element.xpath(xpath)
            if publish_time:
                return "".join(publish_time)
        return ""

    def _extract_pt_by_text(self, element: HtmlElement) -> str:
        """
        Find publish time by text

        :param element: HtmlElement object

        :return:
            `str`, publish time
        """
        text = "".join(element.xpath('.//text()'))
        for dt in DATETIME_PATTERN:
            dt_obj = re.search(dt, text)
            if dt_obj: return dt_obj.group(1)
        return ""

    def extract_publish_time(self, element: HtmlElement, publish_time_xpath: str = "") -> str:
        """
        extract publish time

        :param element: HtmlElement object
        :param publish_time_xpath: specify publish time xpath, default None

        :return:
            `str`, publish time
        """
        return (
                self._extract_pt_by_xpath(element, publish_time_xpath) or
                self._extract_pt_by_meta(element) or
                self._extract_pt_by_text(element)
        )