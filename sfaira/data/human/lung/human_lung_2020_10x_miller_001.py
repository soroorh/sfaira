import os
from typing import Union
from .external import DatasetBase
import anndata
import numpy as np
import scipy.sparse


class Dataset(DatasetBase):
    """
    This data loader directly processes the raw data file which can be obtained from the `download_website` attribute of
    this class.

    :param path:
    :param meta_path:
    :param kwargs:
    """

    def __init__(
            self,
            path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            **kwargs
    ):
        DatasetBase.__init__(self=self, path=path, meta_path=meta_path, **kwargs)
        self.species = "human"
        self.id = "human_lung_2020_10x_miller_001_10.1016/j.devcel.2020.01.033"
        self.download_website = "https://covid19.cog.sanger.ac.uk/miller20.processed.h5ad"
        self.organ = "lung"
        self.sub_tissue = "fetal lung"
        self.has_celltypes = True

        self.class_maps = {
            "0": {
                'Airway Smooth Muscle': 'Airway smooth muscle',
                'Basal cell': 'Basal',
                'Bud tip adjacent': '2_Fetal airway progenitors',
                'Bud tip progenitor': '2_Fetal airway progenitors',
                'Cartilage': '2_Cartilage',
                'Club-like secretory': 'Secretory',
                'Endothelial': '1_Endothelial',
                'Epithelial': '1_Epithelial',
                'Goblet-like secretory': 'Secretory',
                'Hematopoietic, B Cells': 'B cell lineage',
                'Hematopoietic, Macrophage': 'Macrophages',
                'Hematopoietic, Natural Killer Cell': 'Innate lymphoid cells',
                'Hematopoietic, T Cells': 'T cell lineage',
                'Immune': '1_Immune',
                'Intermediate ciliated': 'Multiciliated lineage',
                'Mesenchyme RSPO2+': '1_Stroma',
                'Mesenchyme SERPINF1-high': '1_Stroma',
                'Multiciliated cell': 'Multiciliated lineage',
                'Multiciliated precursor': 'Multiciliated lineage',
                'Neuroendocrine': 'Rare',
                'Pericyte': 'Fibroblasts',
                'RBC': 'Erythrocytes',
                'Secretory progenitor': 'Secretory',
                'Submucosal gland': 'Submucosal Secretory',
                'Submucosal gland basal': 'Submucosal Secretory',
            },
        }

    def _load(self, fn=None):
        if fn is None and self.path is None:
            raise ValueError("provide either fn in load or path in constructor")

        if self._load_raw or not self._load_raw:
            if fn is None:
                fn = os.path.join(self.path, "human/lung/miller20.processed.h5ad")
            self.adata = anndata.read(fn)
            self.adata.X = np.expm1(self.adata.X)
            self.adata.X = self.adata.X.multiply(scipy.sparse.csc_matrix(self.adata.obs['nUMI'].values[:, None]))\
                                       .multiply(1/10000)

        self.adata.uns["lab"] = 'Spence'
        self.adata.uns["year"] = 2020
        self.adata.uns["doi"] = "10.1016/j.devcel.2020.01.033"
        self.adata.uns["protocol"] = '10x'
        self.adata.uns["organ"] = self.organ
        self.adata.uns["subtissue"] = self.sub_tissue
        self.adata.uns["animal"] = "human"
        self.adata.uns["id"] = self.id
        self.adata.uns["wget_download"] = self.download_website
        self.adata.uns["has_celltypes"] = self.has_celltypes
        self.adata.uns["counts"] = 'raw'

        self.adata.obs["cell_ontology_class"] = self.adata.obs['Cell_type']
        self.adata.obs["healthy"] = True
        self.adata.obs['state_exact'] = 'healthy'

        self._convert_and_set_var_names(symbol_col='index', ensembl_col=None, new_index='ensembl')
