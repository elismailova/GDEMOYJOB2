"""
Мокаем sentence_transformers до импорта nlp-модулей,
чтобы не скачивать модель (~400 МБ) в CI.
"""
import sys
from unittest.mock import MagicMock

import numpy as np

_mock_model = MagicMock()
_mock_model.encode.return_value = np.zeros((1, 384))

_mock_st = MagicMock()
_mock_st.SentenceTransformer.return_value = _mock_model
sys.modules["sentence_transformers"] = _mock_st
