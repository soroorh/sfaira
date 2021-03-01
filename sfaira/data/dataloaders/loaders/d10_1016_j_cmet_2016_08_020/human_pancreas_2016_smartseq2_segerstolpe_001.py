import anndata
import os
from typing import Union
import pandas as pd

from sfaira.data import DatasetBase


class Dataset(DatasetBase):
    """
    ToDo: revisit gamma cell missing in CO
    """

    def __init__(
            self,
            data_path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
            **kwargs
    ):
        super().__init__(data_path=data_path, meta_path=meta_path, cache_path=cache_path, **kwargs)
        self.download_url_data = "https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-5061/E-MTAB-5061.processed.1.zip"
        self.download_url_meta = "https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-5061/E-MTAB-5061.sdrf.txt"

        self.author = "Segerstolpe"
        self.doi = "10.1016/j.cmet.2016.08.020"
        self.normalization = "raw"
        self.organ = "pancreas"
        self.organism = "human"
        self.protocol = "Smart-seq2"
        self.year = 2016

        self.var_symbol_col = "index"
        self.obs_key_cellontology_original = "Characteristics[cell type]"
        self.obs_key_state_exact = "Characteristics[disease]"
        self.obs_key_healthy = self.obs_key_state_exact
        self.healthy_state_healthy = "normal"

        self.set_dataset_id(idx=1)

    def _load(self):
        fn = [
            os.path.join(self.data_dir, "E-MTAB-5061.processed.1.zip"),
            os.path.join(self.data_dir, "E-MTAB-5061.sdrf.txt")
        ]
        df = pd.read_csv(fn[0], sep="\t")
        df.index = df.index.get_level_values(0)
        df = df.drop("#samples", axis=1)
        df = df.T.iloc[:, :26178]
        adata = anndata.AnnData(df)
        adata.obs = pd.read_csv(fn[1], sep="\t").set_index("Source Name").loc[adata.obs.index]
        # filter observations which are not cells (empty wells, low quality cells etc.)
        adata = adata[adata.obs["Characteristics[cell type]"] != "not applicable"].copy()
        self.set_unknown_class_id(ids=["unclassified cell", "MHC class II cell"])

        return adata
