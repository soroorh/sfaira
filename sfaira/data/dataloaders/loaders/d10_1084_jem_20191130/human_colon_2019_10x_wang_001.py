import anndata
import os
from typing import Union
import numpy as np
import scipy.sparse

from sfaira.data import DatasetBase


class Dataset(DatasetBase):

    def __init__(
            self,
            path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
            **kwargs
    ):
        super().__init__(path=path, meta_path=meta_path, cache_path=cache_path, **kwargs)
        self.id = "human_colon_2019_10x_wang_001_10.1084/jem.20191130"

        self.download = "https://covid19.cog.sanger.ac.uk/wang20_colon.processed.h5ad"
        self.download_meta = None

        self.author = "Chen"
        self.healthy = True
        self.normalization = "raw"
        self.organ = "colon"
        self.organism = "human"
        self.doi = "10.1084/jem.20191130"
        self.protocol = "10x"
        self.state_exact = "healthy"
        self.year = 2019

        self.var_symbol_col = "index"

        self.obs_key_cellontology_original = "CellType"

        self.class_maps = {
            "0": {
                "Progenitor": "Enterocyte Progenitors",
                "Enterocyte": "Enterocytes",
                "Goblet": "Goblet cells",
                "TA": "TA",
                "Paneth-like": "Paneth cells",
                "Stem Cell": "Stem cells",
                "Enteriendocrine": "Enteroendocrine cells",
            },
        }

    def _load(self, fn=None):
        if fn is None:
            fn = os.path.join(self.path, "human", "colon", "wang20_colon.processed.h5ad")
        self.adata = anndata.read(fn)
        self.adata.X = np.expm1(self.adata.X)
        self.adata.X = self.adata.X.multiply(scipy.sparse.csc_matrix(self.adata.obs["n_counts"].values[:, None]))\
                                   .multiply(1 / 10000)