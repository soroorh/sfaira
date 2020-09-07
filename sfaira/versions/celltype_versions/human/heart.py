from .external import CelltypeVersionsBase

CELLTYPES_HUMAN_HEART_V0 = [
    ['Antigen presenting cell (RPS high)', "nan"],
    ['B cell', "nan"],
    ['B cell (Plasmocyte)', "nan"],
    ['CB CD34+', "nan"],
    ['Dendritic cell', "nan"],
    ['Endothelial cell', "nan"],
    ['Endothelial cell (APC)', "nan"],
    ['Endothelial cell (endothelial to mesenchymal transition)', "nan"],
    ['Epithelial cell', "nan"],
    ['Erythroid cell', "nan"],
    ['Erythroid progenitor cell (RP high)', "nan"],
    ['Fasciculata cell', "nan"],
    ['Fetal Neuron', "nan"],
    ['Fetal epithelial progenitor', "nan"],
    ['Fetal fibroblast', "nan"],
    ['Fetal mesenchymal progenitor', "nan"],
    ['Fetal neuron', "nan"],
    ['Fetal skeletal muscle cell', "nan"],
    ['Fetal stromal cell', "nan"],
    ['Fibroblast', "nan"],
    ['M2 Macrophage', "nan"],
    ['Macrophage', "nan"],
    ['Mast cell', "nan"],
    ['Monocyte', "nan"],
    ['Myeloid cell', "nan"],
    ['Neutrophil', "nan"],
    ['Neutrophil (RPS high)', "nan"],
    ['Primordial germ cell', "nan"],
    ['Proliferating T cell', "nan"],
    ['Sinusoidal endothelial cell', "nan"],
    ['Smooth muscle cell', "nan"],
    ['Stromal cell', "nan"],
    ['T cell', "nan"],
    ['Ventricle cardiomyocyte', "nan"]
]
ONTOLOGIES_HUMAN_HEART_V0 = {
    "names": {},
    "ontology_ids": {},
}


class CelltypeVersionsHumanHeart(CelltypeVersionsBase):

    def __init__(self, **kwargs):
        self.celltype_universe = {
            "0": CELLTYPES_HUMAN_HEART_V0
        }
        self.ontology = {
            "0": ONTOLOGIES_HUMAN_HEART_V0
        }
        super(CelltypeVersionsHumanHeart, self).__init__(**kwargs)
