"""
Qt table model adapter for Pandas DataFrames.
Compatible with PyQt6.
"""

from typing import Any, Optional

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PandasTableModel(QAbstractTableModel):
    """Read-only QAbstractTableModel backed by a Pandas DataFrame."""

    def __init__(self, df: Optional[pd.DataFrame] = None, parent: Any = None) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame = df if df is not None else pd.DataFrame()

    def set_df(self, df: pd.DataFrame) -> None:
        """Replace the underlying DataFrame and notify attached views."""
        self.beginResetModel()
        self._df = df if df is not None else pd.DataFrame()
        self.endResetModel()

    # QAbstractTableModel interface
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if self._df.empty else len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if self._df.empty else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or self._df.empty:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if self._df.empty:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            return str(section + 1)
        return None
