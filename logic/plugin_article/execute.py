import re
from typing import List

import unicodedata
from lxml.html import fromstring

from service.aet.util import remove_noise_node, normalize_node
from service.aet.extracotr.author import AuthorExtractor
from service.aet.extracotr.meta import MetaExtractor
from service.aet.extracotr.title import TitleExtractor
from service.aet.extracotr.publish_time import PublishTimeExtractor
from service.aet.extracotr.content import ContentExtractor


def extract_from_html(
        html: str,
        title_xpath: str = "",
        author_xpath: str = "",
        publish_time_xpath: str = "",
        body_xpath: str = '//body',
        noise_node_list: List = None,
        normalize: bool = False,
        skip_unvisiable: bool = False
):
    """

    Preprocessing HTML can potentially disrupt the original structure of the HTML,
    which could make XPath queries based on the original HTML ineffective.
    Therefore, if title_xpath/author_xpath/publish_time_xpath are specified, they should be extracted first before preprocessing.

    :param html: html of article page
    :param title_xpath: specify title xpath. default None
    :param author_xpath: specify author xpath. default None
    :param noise_node_list: specify title xpath. default None
    :param publish_time_xpath: specify title xpath. default None
    :param body_xpath: specify body xpath. default `//body`
    :param normalize: normalize html
    :param skip_unvisiable: unvisiable element will be skipped

    :return:
    """

    # In some cases, websites may have non-standard HTML,
    # such as the </html> tag appearing in the middle of the source code.
    # it is necessary to correct or repair the HTML.
    new_html = html.replace('</html>', '')
    new_html = f"{new_html}</html>"
    # Normalize HTML to standard, convert special characters into standard characters
    normalize_html = unicodedata.normalize('NFKC', new_html) if normalize else new_html

    # do, extract specify options
    html = re.sub('</?br.*?>', '', normalize_html)
    element = fromstring(html)

    meta = MetaExtractor().extract_meta(element)
    title = TitleExtractor().extract_title(element, title_xpath=title_xpath)
    author = AuthorExtractor().extract_author(element, author_xpath=author_xpath)
    publish_time = PublishTimeExtractor().extract_publish_time(element, publish_time_xpath=publish_time_xpath)
    element = normalize_node(element)
    remove_noise_node(element, noise_node_list)
    contents = ContentExtractor().extract_content(
        element,
        body_xpath=body_xpath,
        use_visiable_info=skip_unvisiable,
    )
    # for content in contents:
    #     print(content)
    if not contents: raise Exception('无法提取正文！')
    result = {
        "title": title,
        "author": author,
        "publish_time": publish_time,
        "content": contents[0][1]["text"],
        "images": contents[0][1]["images"],
        "meta": meta
    }

    return result



