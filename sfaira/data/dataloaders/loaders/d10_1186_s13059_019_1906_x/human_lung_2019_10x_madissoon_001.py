import anndata
import os
from typing import Union

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
        self.id = "human_lung_2019_10x_madissoon_001._10.1186/s13059-019-1906-x"

        self.download = "https://covid19.cog.sanger.ac.uk/madissoon19_lung.processed.h5ad"
        self.download_meta = None

        self.author = "Meyer"
        self.doi = "10.1186/s13059-019-1906-x"
        self.healthy = True
        self.normalization = "raw"
        self.state_exact = "healthy"
        self.organ = "lung"  # ToDo: "parenchyma"
        self.organism = "human"
        self.protocol = "10x"
        self.year = 2020

        self.var_symbol_col = "index"
        self.var_ensembl_col = "gene.ids.HCATisStab7509734"

        self.obs_key_cellontology_original = "CellType"

        self.class_maps = {
            "0": {
                "T_CD4": "T cell lineage",
                "Mast_cells": "Mast cells",
                "Monocyte": "Monocytes",
                "Blood_vessel": "2_Blood vessels",
                "Ciliated": "Multiciliated lineage",
                "Macrophage_MARCOneg": "Macrophages",
                "DC_plasmacytoid": "Dendritic cells",
                "DC_1": "Dendritic cells",
                "Muscle_cells": "2_Smooth Muscle",
                "Macrophage_MARCOpos": "Macrophages",
                "T_cells_Dividing": "T cell lineage",
                "DC_Monocyte_Dividing": "Dendritic cells",
                "B_cells": "B cell lineage",
                "T_CD8_CytT": "T cell lineage",
                "NK_Dividing": "Innate lymphoid cells",
                "T_regulatory": "T cell lineage",
                "DC_2": "Dendritic cells",
                "Alveolar_Type2": "AT2",
                "Plasma_cells": "B cell lineage",
                "NK": "Innate lymphoid cells",
                "Alveolar_Type1": "AT1",
                "Fibroblast": "2_Fibroblast lineage",
                "DC_activated": "Dendritic cells",
                "Macrophage_Dividing": "Macrophages",
                "Lymph_vessel": "Lymphatic EC",
            },
        }

    def _load(self, fn=None):
        if fn is None:
            fn = os.path.join(self.path, "human", "lung", "madissoon19_lung.processed.h5ad")
        self.adata = anndata.read(fn)

        self.set_unkown_class_id(ids=["1_Unicorns and artifacts"])