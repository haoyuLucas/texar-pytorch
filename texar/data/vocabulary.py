# -*- coding: utf-8 -*-
# Copyright 2019 The Texar Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Helper functions and classes for vocabulary processing.
"""
import warnings
from collections import defaultdict
from typing import List, MutableMapping, Sequence, Tuple, Union

import numpy as np

from texar.utils.utils import dict_lookup

__all__ = [
    "SpecialTokens",
    "Vocab"
]


class SpecialTokens(object):
    r"""Special tokens, including :attr:`PAD`, :attr:`BOS`, :attr:`EOS`,
    :attr:`UNK`. These tokens will by default have token ids 0, 1, 2, 3,
    respectively.
    """
    PAD = "<PAD>"
    BOS = "<BOS>"
    EOS = "<EOS>"
    UNK = "<UNK>"


def _make_defaultdict(keys: Sequence[Union[int, str]],
                      values: Sequence[Union[int, str]],
                      default_value: Union[int, str]) -> \
        MutableMapping[Union[int, str], Union[int, str]]:
    r"""Creates a python defaultdict.

    Args:
        keys (list): Keys of the dictionary.
        values (list): Values correspond to keys. The two lists :attr:`keys` and
            :attr:`values` must be of the same length.
        default_value: default value returned when key is missing.

    Returns:
        defaultdict: A python `defaultdict` instance that maps keys to values.
    """
    dict_: MutableMapping[Union[int, str], Union[int, str]] = \
        defaultdict(lambda: default_value)
    for k, v in zip(keys, values):
        dict_[k] = v
    return dict_


class Vocab(object):
    r"""Vocabulary class that loads vocabulary from file, and maintains mapping
    tables between token strings and indexes.

    Each line of the vocab file should contains one vocabulary token, e.g.,::

        vocab_token_1
        vocab token 2
        vocab       token | 3 .
        ...

    Args:
        filename (str): Path to the vocabulary file where each line contains
            one token.
        bos_token (str): A special token that will be added to the beginning of
            sequences.
        eos_token (str): A special token that will be added to the end of
            sequences.
        unk_token (str): A special token that will replace all unknown tokens
            (tokens not included in the vocabulary).
        pad_token (str): A special token that is used to do padding.
    """

    def __init__(self,
                 filename: str,
                 pad_token: str = SpecialTokens.PAD,
                 bos_token: str = SpecialTokens.BOS,
                 eos_token: str = SpecialTokens.EOS,
                 unk_token: str = SpecialTokens.UNK):
        self._filename = filename
        self._pad_token = pad_token
        self._bos_token = bos_token
        self._eos_token = eos_token
        self._unk_token = unk_token

        self._id_to_token_map_py, self._token_to_id_map_py \
            = self.load(self._filename)

    def load(self, filename: str) -> \
            Tuple[MutableMapping[int, str], MutableMapping[str, int]]:
        r"""Loads the vocabulary from the file.

        Args:
            filename (str): Path to the vocabulary file.

        Returns:
            A tuple of mapping tables between word string and
            index, (:attr:`id_to_token_map_py`, :attr:`token_to_id_map_py`),
            where and :attr:`token_to_id_map_py` are python `defaultdict`
            instances.
        """
        with open(filename, "r") as vocab_file:
            vocab = list(line.strip() for line in vocab_file)

        warnings.simplefilter("ignore", UnicodeWarning)

        if self._bos_token in vocab:
            raise ValueError("Special begin-of-seq token already exists in the "
                             "vocabulary: '%s'" % self._bos_token)
        if self._eos_token in vocab:
            raise ValueError("Special end-of-seq token already exists in the "
                             "vocabulary: '%s'" % self._eos_token)
        if self._unk_token in vocab:
            raise ValueError("Special UNK token already exists in the "
                             "vocabulary: '%s'" % self._unk_token)
        if self._pad_token in vocab:
            raise ValueError("Special padding token already exists in the "
                             "vocabulary: '%s'" % self._pad_token)

        warnings.simplefilter("default", UnicodeWarning)

        # Places _pad_token at the beginning to make sure it take index 0.
        vocab = [self._pad_token, self._bos_token, self._eos_token,
                 self._unk_token] + vocab
        # Must make sure this is consistent with the above line
        unk_token_idx = 3
        vocab_size = len(vocab)
        vocab_idx = np.arange(vocab_size)

        # Creates python maps to interface with python code
        id_to_token_map_py = _make_defaultdict(vocab_idx, vocab,
                                               self._unk_token)
        token_to_id_map_py = _make_defaultdict(vocab, vocab_idx,
                                               unk_token_idx)

        return id_to_token_map_py, token_to_id_map_py  # type: ignore

    def map_ids_to_tokens_py(self, ids: np.ndarray) -> np.ndarray:
        r"""Maps ids into text tokens.

        The input :attr:`ids` and returned tokens are both python
        arrays or list.

        Args:
            ids: An `int` numpy array or (possibly nested) list of token ids.

        Returns:
            A numpy array of text tokens of the same shape as :attr:`ids`.
        """
        return dict_lookup(self.id_to_token_map_py, ids, self.unk_token)

    def map_tokens_to_ids_py(self, tokens: List[str]) -> np.ndarray:
        r"""Maps text tokens into ids.

        The input :attr:`tokens` and returned ids are both python
        arrays or list.

        Args:
            tokens: A numpy array or (possibly nested) list of text tokens.

        Returns:
            A numpy array of token ids of the same shape as :attr:`tokens`.
        """
        return dict_lookup(self.token_to_id_map_py, tokens, self.unk_token_id)

    @property
    def id_to_token_map_py(self) -> MutableMapping[int, str]:
        r"""The dictionary instance that maps from token index to the string
        form.
        """
        return self._id_to_token_map_py

    @property
    def token_to_id_map_py(self) -> MutableMapping[str, int]:
        r"""The dictionary instance that maps from token string to the index.
        """
        return self._token_to_id_map_py

    @property
    def size(self) -> int:
        r"""The vocabulary size.
        """
        return len(self.token_to_id_map_py)

    @property
    def bos_token(self) -> str:
        r"""A string of the special token indicating the beginning of sequence.
        """
        return self._bos_token

    @property
    def bos_token_id(self) -> int:
        r"""The `int` index of the special token indicating the beginning
        of sequence.
        """
        return self.token_to_id_map_py[self._bos_token]

    @property
    def eos_token(self) -> str:
        r"""A string of the special token indicating the end of sequence.
        """
        return self._eos_token

    @property
    def eos_token_id(self) -> int:
        r"""The `int` index of the special token indicating the end
        of sequence.
        """
        return self.token_to_id_map_py[self._eos_token]

    @property
    def unk_token(self) -> str:
        r"""A string of the special token indicating unknown token.
        """
        return self._unk_token

    @property
    def unk_token_id(self) -> int:
        r"""The `int` index of the special token indicating unknown token.
        """
        return self.token_to_id_map_py[self._unk_token]

    @property
    def pad_token(self) -> str:
        r"""A string of the special token indicating padding token. The
        default padding token is an empty string.
        """
        return self._pad_token

    @property
    def pad_token_id(self) -> int:
        r"""The `int` index of the special token indicating padding token.
        """
        return self.token_to_id_map_py[self._pad_token]

    @property
    def special_tokens(self) -> List[str]:
        r"""The list of special tokens
        [:attr:`pad_token`, :attr:`bos_token`, :attr:`eos_token`,
        :attr:`unk_token`].
        """
        return [self._pad_token, self._bos_token, self._eos_token,
                self._unk_token]
