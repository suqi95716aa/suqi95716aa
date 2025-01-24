from __future__ import annotations

from typing import Any, List

from service.ragfusion.splitter import TextSplitter
from service.ragfusion.core.document.document import Document


class NLTKTextSplitter(TextSplitter):
    """Using NLTK package to split text"""

    def __init__(
            self,
            separator: str = "\n\n",
            language: str = "english",
            **kwargs: Any
    ) -> None:
        """Initialize the NLTK splitter"""

        super().__init__(**kwargs)
        self._separator = separator
        self._language = language

    def split_text(self, text: str) -> List[Document]:
        try:
            import nltk.tokenize
        except ImportError as e:
            raise ImportError("NLTK package is missing. Install it using `pip install nltk`.") from e

        splits = nltk.tokenize.sent_tokenize(text, language=self._language)
        print(len(splits))
        return self._merge_splits(splits, self._separator)

if __name__ == "__main__":

    s = "William Henry Gates III (born October 28, 1955) is an American businessman and philanthropist best known for his roles at Microsoft Corporation. He co-founded the software company with his childhood friend Paul Allen and later held the positions of chairman, chief executive officer (CEO), president, and chief software architect. He was also being its largest individual shareholder until May 2014.[a] He was a pioneer of the microcomputer revolution of the 1970s and 1980s.Gates was born and raised in Seattle, Washington. In 1975, he and Allen founded Microsoft in Albuquerque, New Mexico. Gates led the company as its chairman and chief executive officer until stepping down as CEO in January 2000, succeeded by Steve Ballmer, but he remained chairman of the board of directors and became chief software architect. During the late 1990s, he was criticized for his business tactics, which were considered anti-competitive."

    s = """
    
    威廉·亨利·盖茨三世（William Henry Gates III，1955 年 10 月 28 日出生）是一位美国商人和慈善家，因其在微软公司 的职务而闻名。他与儿时好友保罗·艾伦 (Paul Allen)共同创立了这家软件公司，后来担任董事长、首席执行官 (CEO)、总裁和首席软件架构师等职务。直到 2014 年 5 月，他还是该公司最大的个人股东。 [ a ]他是20 世纪 70 年代和 1980 年代 微型计算机革命的先驱。

盖茨在华盛顿州西雅图出生并长大。 1975年，他和艾伦在新墨西哥州阿尔伯克基创立了微软。盖茨以董事长兼首席执行官的身份领导公司，直到 2000 年 1 月辞去首席执行官职务，由史蒂夫·鲍尔默 (Steve Ballmer)继任，但他仍然担任董事会主席并成为首席软件架构师。 20 世纪 90 年代末，他的商业策略受到批评，被认为是反竞争的。

2008 年 6 月，盖茨转而在微软兼职，并在比尔及梅琳达盖茨基金会全职工作，该基金会是他和当时的妻子梅琳达于 2000 年创立的私人慈善基金会。他辞去了该基金会主席的职务。微软于2014年2月进入董事会并担任技术顾问的角色，以支持新任命的首席执行官萨蒂亚·纳德拉(Satya Nadella)。 2020 年 3 月，盖茨辞去了微软和伯克希尔哈撒韦公司的董事会职务，专注于气候变化、全球健康与发展以及教育方面的慈善事业。

自1987年起，盖茨就被列入福布斯 全球亿万富豪榜。从1995年到2017年，除了2008年和2010年到2013年，他每年都获得世界首富的称号。1999年，他的净资产短暂超过1000亿美元，成为有史以来第一个千亿富翁。自 2008 年离开微软日常运营以来，盖茨开始从事其他商业和慈善事业。

他是多家公司的创始人和董事长，包括BEN、Cascade Investment、TerraPower、Gates Ventures和Breakthrough Energy。他通过比尔及梅琳达盖茨基金会向各种慈善组织和科学研究项目捐款，据报道该基金会是世界上最大的私人慈善机构。通过该基金会，他领导了 21 世纪初的疫苗接种运动，为根除非洲野生脊髓灰质炎病毒做出了重大贡献。 2010年，盖茨和沃伦·巴菲特创立了“捐赠誓言”他们和其他亿万富翁承诺将至少一半的财富用于慈善事业。
    
    """

    n = NLTKTextSplitter()
    docs = n.split_text(text=s)
    print(docs)

