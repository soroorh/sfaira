CELLTYPEMARKER_TOPOLOGIES = {
    "0.0.1": {
        "genome": "Homo_sapiens_GRCh38_97",
        "hyper_parameters": {
            "l1_coef": 0.,
            "l2_coef": 0.,
            "kernel_initializer": 'glorot_uniform',
            "bias_initializer": 'zeros',
            "bias_regularizer": None,
            "kernel_constraint": None,
            "bias_constraint": None
        }
    }
}

# Load versions from extension if available:
try:
    import sfaira_extension as sfairae
    ADD_TOPOLOGIES = sfairae.versions.topology_versions.human.celltype.CELLTYPEMARKER_TOPOLOGIES
    for k in CELLTYPEMARKER_TOPOLOGIES.keys():
        if k in ADD_TOPOLOGIES.keys():
            CELLTYPEMARKER_TOPOLOGIES.update(ADD_TOPOLOGIES)
except ImportError:
    pass
