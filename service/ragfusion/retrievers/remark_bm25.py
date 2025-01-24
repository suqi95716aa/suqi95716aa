import os
import math
from typing import Optional, List, Dict, Union, Tuple

import jieba

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.runnables.sync import run_in_executor


class BM25Params:
    """
    BM25` params

    This class is an intermediate product, designed for batch tokenization and statistical analysis of Documents,
    which will subsequently be used for term frequency similarity calculations and the preservation of relevant
    metadata.
    """

    def __init__(
            self,
            f: Optional[List[Dict]],
            df: Optional[Dict],
            idf: Optional[Dict],
            length: Optional[Union[int, float]],
            avg_doc_length: Optional[Union[int, float]],
            docs: Optional[List[Document]],
            doc_token_count: List[int],
            k1: Optional[Union[int, float]] = 1,
            k2: Optional[Union[int, float]] = 1.0,
            b: Optional[Union[int, float]] = 0.5
    ):
        """
        Args:
            f (Optional[List[Dict]]):
                Term frequency, where each element in the List represents the term frequency of a Document.
            df (Optional[Dict]):
                The frequency of occurrence of each word across all documents.
            idf (Optional[Dict]):
                The term represents the Inverse Document Frequency (IDF), which is used to measure the
                importance of a word in the context of the entire document collection.
                The formula for IDF is:
                IDF = log((total number of documents - number of documents containing the word + 0.5) / (number of documents containing the word + 0.5)).
            length (Optional[int]):
                The number of documents.
            avg_doc_length (Optional[int]):
                The average length of all texts. Default None.
            docs (List[Documents]):
                Origin docs object list.
            doc_token_count (List[int]):
                The word count after tokenization for each document.
            k1 (Optional[int]):
                k1 adjusts TF saturation. A smaller k1 boosts high-frequency words' impact on ranking,
                while a larger k1 diminishes it. Common k1 values are between 1.2 and 2.0. Default None
            k2 (Optional[float]):
                k2 regulates the impact of document length normalization on TF.
                With k2 at 0, document length doesn't affect TF.
                At k2 = 1, document length influences TF, favoring higher scores for shorter documents.
                k2 typically ranges from 0 to 1.
            b (Optional[int]):
                `b` governs the effect of document length on document score.
                At b = 0, length has no impact on score.
                At b = 1, length influences score, boosting shorter documents. b usually ranges from 0 to 1.

            BM25 focuses more on word matching rather than the integrity of sentences. The advancements of BM25 over traditional TF-IDF include:
            While matching, it also reduces the importance of word frequency across all documents to mitigate the weight (idf) caused by excessive occurrences of a term;
            In calculating the score, it balances the relationship between the average word count and the average document length;
            Incorporates k1, k2, and b to control the formula, where b is a parameter that adjusts the impact of document length on TF.
            1. The k1 parameter is mainly used to control the saturation of TF (Term Frequency).
            The saturation of TF refers to the rapid increase of TF values when a term appears many times in a document,
            which may lead to BM25 scores favoring shorter documents because the word frequency is usually higher in shorter documents.
            By increasing the value of k1, the growth of TF values can be slowed down, thereby balancing the impact of document length and word frequency on the score to some extent;
            2. k2 controls the impact of document length on the TF part. When k2 is large, the contribution of document length to TF will be greater,
            meaning that BM25 will favor shorter documents more, as the word frequency is usually higher in shorter documents.
            When k2 is small, the contribution of document length to TF will be smaller, meaning that BM25 will favor longer documents more, as the word frequency is usually lower in longer documents.
            The value of k2 typically ranges from 0 to 1.

        """
        self.f = f
        self.df = df
        self.idf = idf
        self.length = length
        self.avg_doc_length = avg_doc_length
        self.docs = docs
        self.doc_token_count = doc_token_count
        self.k1 = k1
        self.k2 = k2
        self.b = b

    def __str__(self):
        return f"k1:{self.k1}, k2:{self.k2}, b:{self.b}"


class BM25Retriever(object):
    """
    BM25` model which implements algorithm for BM25.

    BM25 refers to: https://www.jianshu.com/p/fd66f74fed70
    It only supports chinese cut off by jieba and implements similarity search by term similarity.

    """

    _stop_words_file = "stop_words.txt"
    whitespace_characters = [" ", "\n", "\t"]

    def __init__(self, docs: List[Document]):
        self.docs = docs
        self.param: BM25Params = self._load_param()

    def _load_param(self):

        def _load_stop_words(self) -> List:
            _stop_words_path = os.path.join(os.path.dirname(__file__), self._stop_words_file)
            if not os.path.exists(_stop_words_path):
                raise Exception(f"system stop words: {_stop_words_path} not found")
            with open(_stop_words_path, 'r', encoding='utf8') as reader:
                return [line.strip() for line in reader]

        self._stop_words = _load_stop_words(self)
        if not self.docs: raise Exception("Missing docs to parse.")
        param = self._build_param()
        return param

    def _build_param(self) -> BM25Params:
        """
        Refer to BM25Params relative params

        Returns:
            `BM25Params`
        """
        f = list()  # 每个文档的词频率，每一项记录该文档中每个词出现的次数
        df = dict() # 每个文档的词频率，从所有文档中每个词出现的次数
        idf = dict()    # 每个文档的逆文档频率，从所有文档中每个词出现的次数
        docs = list()
        doc_token_count = list()
        pure_doc = [doc for doc in self.docs if doc.page_content not in self.whitespace_characters and doc.page_content.strip()]
        length = len(pure_doc)

        # To build other params(Refers to BM25Params)
        for doc in pure_doc:
            words = [word for word in jieba.lcut(doc.page_content) if word and word not in self._stop_words and word not in self.whitespace_characters]
            doc_token_count.append(len(words))
            docs.append(doc)
            tmp_dict = {}
            for word in words:
                tmp_dict[word] = tmp_dict.get(word, 0) + 1
            f.append(tmp_dict)
            for word in tmp_dict.keys():
                df[word] = df.get(word, 0) + 1

        # To build idf params
        for word, num in df.items():
            idf[word] = math.log(length + 1) - math.log(num + 0.5)

        return BM25Params(
            f=f,
            df=df,
            idf=idf,
            length=length,
            docs=docs,
            doc_token_count=doc_token_count,
            avg_doc_length=sum(doc_token_count) / length if length > 0 else 0,
        )

    def _cal_similarity(self, words: List[str], index: int) -> Union[float, int]:
        score = 0
        for word in words:
            if word not in self.param.f[index]:
                continue
            molecular = self.param.idf[word] * self.param.f[index][word] * (self.param.k1 + 1)
            denominator = self.param.f[index][word] + self.param.k1 * (1 - self.param.b + self.param.b * self.param.doc_token_count[index] / self.param.avg_doc_length)
            score += molecular / denominator
        return max(score, 0)

    def get_relevant_documents(self, query: str, topK: int = 2, **kwargs) -> List[Document]:
        """
        Cal similarity with bm25.

        Args:
            query: Query for waiting for match
            topK: topK similarity score to return

        Returns:
            Most similar of documents (List[Tuple[Document, float]])
        """
        words = [word for word in jieba.lcut(query) if word and word not in self._stop_words and word not in self.whitespace_characters]
        score_list = list()
        for index in range(self.param.length):
            score = self._cal_similarity(words, index)
            self.param.docs[index].metadata.update({"score": score})
            score_list.append(self.param.docs[index])
        sorted_data = sorted(score_list, key=lambda x: x.metadata.get("score"), reverse=True)
        return sorted_data[:topK]

    async def aget_relevant_documents(self, query: str, topK: int = 2, **kwargs) -> List[Document]:
        return await run_in_executor(
            None,
            self.get_relevant_documents,
            query=query,
            topK=topK,
            **kwargs
        )




