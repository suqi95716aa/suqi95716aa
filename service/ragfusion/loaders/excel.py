import os
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterator, Optional, Sequence, Union

import pandas as pd

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.loader.loader import BaseLoader


class ExcelLoader(BaseLoader):
    """Load Microsoft Excel files using `pandas`.

    Like other as Excel loader
    Pandas(ExcelLoader) loaders can be used in split xlsx、xls file type
    and only with row as unit.
    And primary output columns is page_content and metadata with every
    single line.

    Examples
    --------
    from loaders import ExcelLoader

    loader = UnstructuredExcelLoader("stanley-cups.xlsx", mode="elements")
    docs = loader.load()
    """

    def __init__(
        self,
        file_or_buffer: Union[str, Path, BytesIO],
        source_column: Optional[str] = None,
        excel_args: Optional[Dict] = None,
        metadata_columns: Sequence[str] = (),
    ):
        """

        Args:
            file_or_buffer: The path to the Excel file or BytesIO
            source_column: The name of the column in the Excel file to use as the source.
              Optional. Defaults to None.
            excel_args: A dictionary of arguments to pass to the pandas.read_excel().
              Optional. Defaults to None.
            metadata_columns: A sequence of column names to use as metadata. Optional.
        """
        self.file_or_buffer = file_or_buffer
        self.source_column = source_column
        self.excel_args = excel_args or {}
        self.metadata_columns = metadata_columns

    def lazy_load(self) -> Iterator[Document]:
        try:
            # 打开文件并处理
            df = pd.read_excel(self.file_or_buffer, **self.excel_args)
            yield from self.__read_file(df)
        except Exception as e:
            raise RuntimeError(f"Error loading {self.file_or_buffer}") from e

    def __read_file(self, df: pd.DataFrame) -> Iterator[Document]:
            for ind, row in df.iterrows():
                try:
                    sources = {
                        "source": row[self.source_column]
                        if self.source_column is not None
                        else os.path.basename(str(self.file_or_buffer)),
                        "prefix_type": os.path.basename(str(self.file_or_buffer)).split(".")[1]
                        if self.file_or_buffer and "." in str(self.file_or_buffer)
                        else "Unknow File Type"
                    }
                except KeyError:
                    raise ValueError(
                        f"Source column '{self.source_column}' not found in Excel file."
                    )

                metadata = {**sources, "row": ind}
                for col in self.metadata_columns:
                    try:
                        metadata[col] = row[col]
                    except KeyError:
                        raise ValueError(f"Metadata column '{col}' not found in Excel file.")

                content = "\n".join(
                    f"{str(k).strip() if not pd.isna(k) and k is not None else ''}: {str(v).strip() if v is not None and not pd.isna(v) else ''}"
                    for k, v in row.items()
                    if k not in self.metadata_columns
                )

                import warnings
                warnings.warn(f"The reason for the missing values may be attributed to the presence of merged cells within the file.")

                yield Document(page_content=content, metadata=metadata)




