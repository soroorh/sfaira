import anndata
import numpy as np
import os
import pandas
from typing import Union
from .external import DatasetBase
from .external import ADATA_IDS_SFAIRA


class Dataset(DatasetBase):

    id: str

    def __init__(
            self,
            path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            **kwargs
    ):
        DatasetBase.__init__(self=self, path=path, meta_path=meta_path, **kwargs)
        self.species = "mouse"
        self.id = "mouse_pancreas_2019_10x_thompson_003_10.1016/j.cmet.2019.01.021"
        self.download_website = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE117770"
        self.organ = "pancreas"
        self.sub_tissue = "pancreas"
        self.has_celltypes = True

        self.class_maps = {
            "0": {
                'acinar': 'pancreatic acinar cell',
                'ductal': 'pancreatic ductal cell',
                'leukocyte': 'leukocyte',
                'T cell(Pancreas)': 't cell',
                'B cell(Pancreas)': 'b cell',
                'beta': "pancreatic B cell",
                'alpha': "pancreatic A cell",
                'delta': "pancreatic D cell",
                'pp': "pancreatic PP cell",
                'smooth_muscle': "smooth muscle cell",
                'stellate cell': "pancreatic stellate cell",
                'fibroblast': "stromal cell",
                'endothelial': "endothelial cell"
            },
        }

    def _load(self, fn=None):
        if fn is None:
            if self.path is None:
                raise ValueError("provide either fn in load or path in constructor")
            fn = os.path.join(self.path, "mouse/pancreas/GSM3308548_NOD_14w_A")
            fn_meta = os.path.join(self.path, "mouse/pancreas/GSM3308548_NOD_14w_A_annotation.csv")

        celltypes = pandas.read_csv(fn_meta, index_col=0)

        self.adata = anndata.read_mtx(fn + '_matrix.mtx.gz').transpose()
        self.adata.var_names = np.genfromtxt(fn + '_genes.tsv.gz', dtype=str)[:, 1]
        self.adata.obs_names = np.genfromtxt(fn + '_barcodes.tsv.gz', dtype=str)
        self.adata.var_names_make_unique()
        self.adata = self.adata[celltypes.index]

        self.adata.uns[ADATA_IDS.author] = "Bhushan"
        self.adata.uns[ADATA_IDS.year] = "2019"
        self.adata.uns[ADATA_IDS.doi] = "10.1016/j.cmet.2019.01.021"
        self.adata.uns[ADATA_IDS.protocol] = "10x"
        self.adata.uns[ADATA_IDS.organ] = self.organ
        self.adata.uns[ADATA_IDS.subtissue] = self.sub_tissue  # TODO
        self.adata.uns[ADATA_IDS.animal] = "mouse"
        self.adata.uns[ADATA_IDS.id] = self.id
        self.adata.uns[ADATA_IDS.wget_download] = self.download_website
        self.adata.uns[ADATA_IDS.has_celltypes] = self.has_celltypes
        self.adata.uns[ADATA_IDS.normalization] = 'raw'
        self.adata.obs[ADATA_IDS.cell_ontology_class] = celltypes
        self.set_unkown_class_id(ids=[np.nan, "nan"])
        self.adata.obs[ADATA_IDS.cell_types_original] = celltypes
        self.adata.obs[ADATA_IDS.healthy] = False
        self.adata.obs[ADATA_IDS.state_exact] = "diabetic"

        self._convert_and_set_var_names(symbol_col='index', ensembl_col=None, new_index=ADATA_IDS.gene_id_ensembl)
