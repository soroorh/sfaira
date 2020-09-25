NMF_TOPOLOGIES = {
    "0.1": {
        "genome": "Homo_sapiens_GRCh38_97",
        "hyper_parameters": {
                "latent_dim": 64,
                "l1_coef": 0.,
                "l2_coef": 0.,
                "positive_components": True,
                "output_layer": "nb_shared_disp"
        }
    },

    "0.2": {
        "genome": "Homo_sapiens_GRCh38_97",
        "hyper_parameters": {
                "latent_dim": 128,
                "l1_coef": 0.,
                "l2_coef": 0.,
                "positive_components": True,
                "output_layer": "nb_shared_disp"
        }
    },

    "0.3": {
        "genome": "Homo_sapiens_GRCh38_97",
        "hyper_parameters": {
                "latent_dim": 128,
                "l1_coef": 0.,
                "l2_coef": 0.,
                "positive_components": True,
                "output_layer": "nb_const_disp"
        }
    }
}

# Load versions from extension if available:
try:
    import sfaira_extension.api as sfairae
    ADD_TOPOLOGIES = sfairae.versions.topology_versions.human.embedding.NMF_TOPOLOGIES
    for k in NMF_TOPOLOGIES.keys():
        if k in ADD_TOPOLOGIES.keys():
            NMF_TOPOLOGIES.update(ADD_TOPOLOGIES)
except ImportError:
    pass