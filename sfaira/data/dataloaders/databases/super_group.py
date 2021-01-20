from typing import Union

from sfaira.data import DatasetSuperGroup
from sfaira.data.dataloaders.databases.cellxgene import DatasetGroup as DatasetGroupCellxgene


class DatasetSuperGroupDatabases(DatasetSuperGroup):

    def __init__(
            self,
            path: Union[str, None] = None,
            meta_path: Union[str, None] = None,
            cache_path: Union[str, None] = None,
    ):
        dataset_groups = []
        # List all data bases here:
        dataset_groups.append(DatasetGroupCellxgene(
            path=path,
            meta_path=meta_path,
            cache_path=cache_path
        ))
        super().__init__(dataset_groups=dataset_groups)