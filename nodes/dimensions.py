import hashlib
import typing
from typing import List, OrderedDict
import polars as pl

from pydantic import BaseModel, Field, PrivateAttr

from common.i18n import I18nString, TranslatedString
from common.types import Identifier

if typing.TYPE_CHECKING:
    import pandas as pd


class DimensionCategory(BaseModel):
    id: Identifier
    label: I18nString | None
    aliases: List[str] = Field(default_factory=list)

    def all_labels(self) -> set[str]:
        labels = set()
        if isinstance(self.label, TranslatedString):
            labels.update(self.label.all())
        elif isinstance(self.label, str):
            labels.add(self.label)
        if self.aliases:
            labels.update(self.aliases)
        return labels


class Dimension(BaseModel):
    id: Identifier
    label: I18nString | None = None
    categories: List[DimensionCategory] = Field(default_factory=list)
    _hash: bytes | None = PrivateAttr(default=None)
    _cat_map: OrderedDict[str, DimensionCategory] = PrivateAttr(default_factory=dict)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        cat_map = OrderedDict([(str(cat.id), cat) for cat in self.categories])
        self._cat_map = cat_map

    def get(self, cat_id: str) -> DimensionCategory:
        if cat_id not in self._cat_map:
            raise KeyError("Dimension %s: category %s not found" % (self.id, cat_id))
        return self._cat_map[cat_id]

    def get_cat_ids(self) -> set[str]:
        return set(self._cat_map.keys())

    def get_cat_ids_ordered(self) -> list[str]:
        return list(self._cat_map.keys())

    def labels_to_ids(self) -> dict[str, Identifier]:
        all_labels = {}
        for cat in self.categories:
            for label in cat.all_labels():
                if label in all_labels:
                    raise Exception("Dimension %s: duplicate label %s" % (self.id, label))
                all_labels[label] = cat.id
        return all_labels

    def series_to_ids(self, s: 'pd.Series') -> 'pd.Series':
        if s.hasnans:
            raise Exception("Series contains NaNs")
        cat_map = self.labels_to_ids()
        s = s.str.strip()
        cs = s.map(cat_map)
        if cs.hasnans:
            missing_cats = s[~s.isin(cat_map)].unique()
            raise Exception("Some dimension categories failed to convert (%s)" % ', '.join(missing_cats))
        return cs

    def series_to_ids_pl(self, s: pl.Series) -> pl.Series:
        name = s.name
        if s.null_count():
            raise Exception("Series contains NaNs")
        s = s.cast(str).str.strip()
        cat_map = self.labels_to_ids()
        label = cat_map.keys()
        id = cat_map.values()
        map_df = pl.DataFrame(dict(label=label, id=id))
        df = pl.DataFrame(dict(cat=s))
        df = df.join(map_df, left_on='cat', right_on='label', how='left')
        if df['id'].null_count():
            missing_cats = df.filter(~pl.col('id'))['cat'].unique()
            raise Exception("Some dimension categories failed to convert (%s)" % ', '.join(missing_cats))
        ret = df['id'].cast(pl.Categorical)
        if name:
            ret = ret.alias(name)
        return ret

    def calculate_hash(self) -> bytes:
        if self._hash is not None:
            return self._hash
        h = hashlib.md5()
        h.update(self.json(exclude={'label': True, 'categories': {'__all__': {'label'}}}).encode('utf8'))
        self._hash = h.digest()
        return self._hash