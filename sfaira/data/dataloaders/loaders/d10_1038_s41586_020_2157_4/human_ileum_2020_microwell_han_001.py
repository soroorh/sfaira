from typing import Union
from .base import Dataset_d10_1038_s41586_020_2157_4


class Dataset(Dataset_d10_1038_s41586_020_2157_4):

    def __init__(
            self,
            path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
            **kwargs
    ):
        super().__init__(path=path, meta_path=meta_path, cache_path=cache_path, **kwargs)
        self.id = "human_ileum_2020_microwell_han_001_10.1038/s41586-020-2157-4"
        self.organ = "ileum"
        self.class_maps = {
            "0": {
                "B cell": "B cells",
                "B cell (Plasmocyte)": "Plasma Cells",
                "Dendritic cell": "Dendritic cell",
                "Endothelial cell": "Endothelial cell",
                "Endothelial cell (APC)": "Endothelial cell",
                "Endothelial cell (endothelial to mesenchymal transition)": "Endothelial cell",
                "Enterocyte": "Enterocytes",
                "Enterocyte progenitor": "Enterocytes",
                "Epithelial cell": "Epithelial cell",
                "Fetal Neuron": "Fetal neuron",
                "Fetal enterocyte": "Enterocytes",
                "Fetal epithelial progenitor": "Progenitors",
                "Fetal mesenchymal progenitor": "Fetal mesenchymal progenitor",
                "Fetal neuron": "Fetal neuron",
                "Fetal stromal cell": "Fetal stromal cell",
                "Fibroblast": "Fibroblasts",
                "Hepatocyte/Endodermal cell": "Hepatocyte/Endodermal cell",
                "M2 Macrophage": "M2 Macrophage",
                "Macrophage": "Macrophage",
                "Mast cell": "Mast cells",
                "Monocyte": "Monocyte",
                "Neutrophil (RPS high)": "Neutrophil (RPS high)",
                "Proliferating T cell": "T cells",
                "Smooth muscle cell": "Smooth muscle cell",
                "Stromal cell": "Stromal cell",
                "T cell": "T cells",
            },
        }

    def _load(self, fn=None):
        self._load_generalized(fn=fn, sample_id="AdultIleum_2")