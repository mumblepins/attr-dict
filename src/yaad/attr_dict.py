# -*- coding: utf-8 -*-
import itertools
from collections.abc import Mapping, MutableMapping
from typing import Tuple


class AttrDict(MutableMapping):
    """A dictionary wrapper with recursive attribute access.

    Args:
        *args: args to pass to dict constructor
        wrapper_type: optional class to wrap all returned values in.
        _parent_key: private attribute to store the key of the parent dict.
        **kwargs: kwargs to pass to dict constructor

    Examples:
        >>> d = AttrDict(a=1, b={'c': 2})
        >>> d.b.c
        2
        >>> d.d = 3
        >>> d
        AttrDict({'a': 1, 'b': {'c': 2}, 'd': 3})



    """

    def __init__(self, *args, wrapper_type=None, _parent_key=None, **kwargs):
        super().__init__()
        self._parent_key = _parent_key
        self._wrapper_type = wrapper_type
        self._d = dict(*args, **kwargs)

    # attributes that are included in the iteration (generally used for a property of a subclass)
    _special_attributes: Tuple[str, ...] = ()

    def __setitem__(self, k, v):
        self._d[k] = v

    def __delitem__(self, v) -> None:
        del self._d[v]

    def __delattr__(self, item):
        if item.startswith("_"):
            super().__delattr__(item)
        else:
            del self[item]

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self):
        if self._special_attributes:
            return itertools.chain(self._d.__iter__(), self._special_attributes)
        return self._d.__iter__()

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def __getattr__(self, k):
        if not k.startswith("_") and k in self._d:
            return self.__getitem__(k)
        return getattr(super(), k)

    def _get_item_no_wrapper(self, k):
        if k in self._special_attributes:
            v = getattr(self, k)
        else:
            v = self._d[k]
        return v

    def __getitem__(self, k):
        v = self._get_item_no_wrapper(k)
        if isinstance(v, Mapping):
            return self.__class__(v, wrapper_type=self._wrapper_type)
        return self._maybe_wrap(v)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._d})"

    def items(self, flat_key=False):
        for k in self:
            v = self._get_item_no_wrapper(k)
            if flat_key and self._parent_key is not None:
                k = f"{self._parent_key}.{k}"
            if isinstance(v, Mapping):
                yield k, self.__class__(v)
            else:
                yield k, self._maybe_wrap(v)

    def _maybe_wrap(self, v):
        if self._wrapper_type is None:
            return v
        if isinstance(v, self._wrapper_type):
            return v
        return self._wrapper_type(v)

    def items_flat(self):
        for k, v in self.items(flat_key=True):
            if isinstance(v, Mapping):
                yield from self.__class__(v, _parent_key=k, wrapper_type=self._wrapper_type).items_flat()
            else:
                yield k, self._maybe_wrap(v)
