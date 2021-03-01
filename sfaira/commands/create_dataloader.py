import logging
import os
import re
from dataclasses import dataclass, asdict
from shutil import copyfile
from typing import Union

from sfaira.commands.questionary import sfaira_questionary
from rich import print
from cookiecutter.main import cookiecutter

log = logging.getLogger(__name__)


@dataclass
class TemplateAttributes:
    dataloader_type: str = ''  # One of single_dataset, multiple_datasets_single_file, multiple_datasets_streamlined, multiple_datasets_not_streamlined
    id: str = ''  # unique identifier of data set (Organism_Organ_Year_Protocol_NumberOfDataset_FirstAuthorLastname_doi).
    id_without_doi: str = ''  # complete id without the doi -> usually used to name the python scripts

    author: Union[str, list] = ''  # author (list) who sampled / created the data set
    doi: str = ''  # doi of data set accompanying manuscript
    doi_sfaira_repr: str = ''  # internal representation with any special characters replaced with underscores

    download_url_data: str = ''  # download website(s) of data files
    download_url_meta: str = ''  # download website(s) of meta data files

    organ: str = ''  # (*, optional) organ (anatomical structure)
    organism: str = ''  # (*) species / organism
    protocol: str = ''  # (*, optional) protocol used to sample data (e.g. smart-seq2)
    year: str = 2021  # year in which sample was acquired
    number_of_datasets: str = 1  # Required to determine the file names


class DataloaderCreator:

    def __init__(self):
        self.WD = os.path.dirname(__file__)
        self.TEMPLATES_PATH = f'{self.WD}/templates'
        self.template_attributes = TemplateAttributes()

    def create_dataloader(self):
        """
        Prompts and guides the user through a number of possible dataloader choices.
        Prompts the user for required attributes which must be present in the dataloader.
        Finally creates the specific cookiecutter dataloader template.
        """
        self._prompt_dataloader_template()
        self._prompt_dataloader_configuration()
        self._create_dataloader_template()

    def _prompt_dataloader_template(self) -> None:
        """
        Guides the user to select the appropriate dataloader template for his dataset.
        Sets the dataloader_type
        """
        number_datasets = sfaira_questionary(function='select',
                                             question='How many datasets does your project have?',
                                             choices=['One', 'More than one'])
        # One dataset
        if number_datasets == 'One':
            self.template_attributes.dataloader_type = 'single_dataset'
            return
        # More than one dataset
        dataset_counts = sfaira_questionary(function='select',
                                            question='Are your datasets in a single file or is there one file per dataset?',
                                            choices=['Single dataset file', 'Multiple dataset files'])
        if dataset_counts == 'Single dataset file':
            self.template_attributes.dataloader_type = 'multiple_datasets_single_file'
            return

        # streamlined?
        streamlined_datasets = sfaira_questionary(function='select',
                                                  question='Are your datasets in a similar format?',
                                                  choices=['Same format', 'Different formats'])
        if streamlined_datasets == 'Same format':
            self.template_attributes.dataloader_type = 'multiple_datasets_streamlined'
            return
        else:
            self.template_attributes.dataloader_type = 'multiple_datasets_not_streamlined'
            return

    def _prompt_dataloader_configuration(self):
        """
        Prompts the user for all required attributes for a dataloader such as DOI, author, etc.
        """
        author = sfaira_questionary(function='text',
                                    question='Author(s):',
                                    default='Einstein, Albert; Hawking, Stephen')
        self.template_attributes.author = author.split(';') if ';' in author else author
        doi = sfaira_questionary(function='text',
                                 question='DOI:',
                                 default='10.1000/j.journal.2021.01.001')
        while not re.match(r'\b10\.\d+/[\w.]+\b', doi):
            print('[bold red]The entered DOI is malformed!')  # noqa: W605
            doi = sfaira_questionary(function='text',
                                     question='DOI:',
                                     default='10.1000/j.journal.2021.01.001')
        self.template_attributes.doi = doi
        self.template_attributes.doi_sfaira_repr = f'd{doi.translate({ord(c): "_" for c in r"!@#$%^&*()[]/{};:,.<>?|`~-=_+"})}'

        self.template_attributes.organism = sfaira_questionary(function='text',
                                                               question='Organism:',
                                                               default='NA')
        self.template_attributes.organ = sfaira_questionary(function='text',
                                                            question='Organ:',
                                                            default='NA')
        self.template_attributes.protocol = sfaira_questionary(function='text',
                                                               question='Protocol:',
                                                               default='NA')
        self.template_attributes.year = sfaira_questionary(function='text',
                                                           question='Year:',
                                                           default='2021')
        first_author = author[0] if isinstance(author, list) else author
        try:
            first_author_lastname = first_author.split(',')[0]
        except KeyError:
            print('[bold yellow] First author was not in the expected format. Using full first author for the id.')
            first_author_lastname = first_author
        self.template_attributes.id_without_doi = f'{self.template_attributes.organism}_{self.template_attributes.organ}_' \
                                                  f'{self.template_attributes.year}_{self.template_attributes.protocol}_' \
                                                  f'{first_author_lastname}_001'
        self.template_attributes.id = self.template_attributes.id_without_doi + f'_{self.template_attributes.doi_sfaira_repr}'
        self.template_attributes.download_url_data = sfaira_questionary(function='text',
                                                                        question='URL to download the data',
                                                                        default='https://ftp.ncbi.nlm.nih.gov/geo/')
        self.template_attributes.number_of_datasets = sfaira_questionary(function='text',
                                                                         question='Number of datasets:',
                                                                         default='1').zfill(3)

    def _template_attributes_to_dict(self) -> dict:
        """
        Create a dict from the our Template Structure dataclass
        :return: The dict containing all key-value pairs with non empty values
        """
        return {key: val for key, val in asdict(self.template_attributes).items() if val != ''}

    def _create_dataloader_template(self):
        template_path = f'{self.TEMPLATES_PATH}/{self.template_attributes.dataloader_type}'
        cookiecutter(f'{template_path}',
                     no_input=True,
                     overwrite_if_exists=True,
                     extra_context=self._template_attributes_to_dict())

        # multiple datasets not streamlined are not contained in a single file but in multiple files
        # Hence, we create one copy per dataset and adapt the ID per dataloader script
        if self.template_attributes.dataloader_type == 'multiple_datasets_not_streamlined':
            for i in range(2, int(self.template_attributes.number_of_datasets.lstrip('0')) + 1):
                copyfile(f'{self.template_attributes.doi_sfaira_repr}/{self.template_attributes.id_without_doi}.py',
                         f'{self.template_attributes.doi_sfaira_repr}/{self.template_attributes.id_without_doi[:-3]}{str(i).zfill(3)}.py')

                # Replace the default ID of 1 with the file specific ID
                with open(f'{self.template_attributes.doi_sfaira_repr}/{self.template_attributes.id_without_doi[:-3]}{str(i).zfill(3)}.py', 'r') as file:
                    content = file.readlines()
                idx_fixed = list(map(lambda line: f'        self.set_dataset_id(idx={i})  # autogenerated by sfaira'
                                     if line.strip().startswith('self.set_dataset_id(idx=1)')
                                     else line,
                                     content))
                with open(f'{self.template_attributes.doi_sfaira_repr}/{self.template_attributes.id_without_doi[:-3]}{str(i).zfill(3)}.py', 'w') as file:
                    for line in idx_fixed:
                        file.write(line)