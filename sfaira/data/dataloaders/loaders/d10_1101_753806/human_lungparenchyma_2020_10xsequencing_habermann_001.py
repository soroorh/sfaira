import anndata
import os
from typing import Union
import pandas as pd

from sfaira.data import DatasetBase


class Dataset(DatasetBase):

    def __init__(
            self,
            data_path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
            **kwargs
    ):
        super().__init__(data_path=data_path, meta_path=meta_path, cache_path=cache_path, **kwargs)
        self.download_url_data = [
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135893/suppl/GSE135893%5Fmatrix%2Emtx%2Egz",
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135893/suppl/GSE135893%5Fgenes%2Etsv%2Egz",
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135893/suppl/GSE135893%5Fbarcodes%2Etsv%2Egz"
        ]
        self.download_url_meta = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135893/suppl/GSE135893%5FIPF%5Fmetadata%2Ecsv%2Egz"

        self.author = "Habermann"
        self.doi = "10.1101/753806"
        self.normalization = "raw"
        self.organ = "lung parenchyma"
        self.organism = "human"
        self.protocol = "10X sequencing"
        self.year = 2020

        self.var_symbol_col = "index"
        self.obs_key_cellontology_original = "celltype"
        self.obs_key_state_exact = "Diagnosis"
        self.obs_key_healthy = "Status"
        self.healthy_state_healthy = "Control"

        self.set_dataset_id(idx=1)

    def _load(self):
        fn = [
            os.path.join(self.data_dir, "GSE135893_matrix.mtx.gz"),
            os.path.join(self.data_dir, "GSE135893_genes.tsv.gz"),
            os.path.join(self.data_dir, "GSE135893_barcodes.tsv.gz"),
            os.path.join(self.data_dir, "GSE135893_IPF_metadata.csv.gz"),
        ]
        adata = anndata.read_mtx(fn[0]).T
        adata.var = pd.read_csv(fn[1], index_col=0, header=None, names=["ids"])
        adata.obs = pd.read_csv(fn[2], index_col=0, header=None, names=["barcodes"])
        obs = pd.read_csv(fn[3], index_col=0)
        adata = adata[obs.index.tolist(), :].copy()
        adata.obs = obs
        self.set_unknown_class_id(ids=["1_Unicorns and artifacts"])

        return adata