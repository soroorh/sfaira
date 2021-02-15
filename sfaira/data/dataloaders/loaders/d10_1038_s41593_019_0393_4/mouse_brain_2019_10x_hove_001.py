import anndata
import numpy as np
import os
import pandas
import zipfile
import scipy.io
from typing import Union
from sfaira.data import DatasetBaseGroupLoadingOneFile

SAMPLE_IDS = [
    "Choroid plexus",
    "Dura mater",
    "Enr. SDM",
    "Whole brain",
]


class Dataset(DatasetBaseGroupLoadingOneFile):

    def __init__(
            self,
            sample_id: str,
            data_path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
            **kwargs
    ):
        super().__init__(sample_id=sample_id, data_path=data_path, meta_path=meta_path, cache_path=cache_path, **kwargs)
        sample_organ_dict = {
            "Choroid plexus": "choroid plexus",
            "Dura mater": "dura mater",
            "Enr. SDM": "brain meninx",
            "Whole brain": "brain",
        }
        self.obs_key_sample = "sample"
        self.organ = sample_organ_dict[self.sample_id]

        self.id = f"mouse_{''.join(self.organ.split(' '))}_2019_10x_hove_" \
                  f"{str(SAMPLE_IDS.index(self.sample_id)).zfill(3)}_10.1038/s41593-019-0393-4"

        self.download_url_data = \
            "https://www.brainimmuneatlas.org/data_files/toDownload/filtered_gene_bc_matrices_mex_WT_fullAggr.zip"
        self.download_url_meta = \
            "https://www.brainimmuneatlas.org/data_files/toDownload/annot_fullAggr.csv"

        self.author = "Hove"
        self.doi = "10.1038/s41593-019-0393-4"
        self.healthy = True
        self.normalization = "raw"
        self.organism = "mouse"
        self.protocol = "10X sequencing"
        self.state_exact = "healthy"
        self.year = 2019

        self.var_ensembl_col = "ensembl"
        self.var_symbol_col = "name"

        self.obs_key_cellontology_original = "cluster"
        self.obs_key_organ = "sample_anatomy"

        self.class_maps = {
            "0": {
                "Microglia": "microglial cell",
                "T/NKT cells": "CD8-positive, alpha-beta T cell",
                "Monocytes": "monocyte"
            },
        }

    def _load_full(self):
        fn = [
            os.path.join(self.data_dir, "filtered_gene_bc_matrices_mex_WT_fullAggr.zip"),
            os.path.join(self.data_dir, "annot_fullAggr.csv")
        ]

        with zipfile.ZipFile(fn[0]) as archive:
            x = scipy.io.mmread(archive.open('filtered_gene_bc_matrices_mex/mm10/matrix.mtx')).T.tocsr()
            self.adata = anndata.AnnData(x)
            var = pandas.read_csv(archive.open('filtered_gene_bc_matrices_mex/mm10/genes.tsv'), sep="\t", header=None)
            var.columns = ["ensembl", "name"]
            obs_names = pandas.read_csv(archive.open('filtered_gene_bc_matrices_mex/mm10/barcodes.tsv'),
                                        sep="\t",
                                        header=None
                                        )[0].values
        assert len(obs_names) == self.adata.shape[0]  # ToDo take asserts out
        assert var.shape[0] == self.adata.shape[1]  # ToDo take asserts out
        obs = pandas.read_csv(fn[1])

        # Match annotation to raw data.
        obs.index = obs["cell"].values
        obs = obs.loc[[i in obs_names for i in obs.index], :]
        idx_tokeep = np.where([i in obs.index for i in obs_names])[0]
        self.adata = self.adata[idx_tokeep, :]
        obs_names = obs_names[idx_tokeep]
        idx_map = np.array([obs.index.tolist().index(i) for i in obs_names])
        self.adata = self.adata[idx_map, :]
        obs_names = obs_names[idx_map]

        # Assign attributes
        self.adata.obs_names = obs_names
        self.adata.var = var
        self.adata.obs = obs
        assert np.all(self.adata.obs_names == self.adata.obs["cell"].values)  # ToDo take asserts out