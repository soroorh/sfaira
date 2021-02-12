from typing import Dict, List, Union

from sfaira.versions.metadata import CelltypeUniverse


def map_celltype_to_ontology(
        queries: Union[str, List[str]],
        organism: str,
        include_synonyms: bool = True,
        anatomical_constraint: Union[str, None] = None,
        omit_target_list: list = ["cell"],
        n_suggest: int = 4,
        choices_for_perfect_match: bool = True,
        keep_strategy: bool = False,
        always_return_list: bool = False,
        threshold_for_partial_matching: float = 90.,
        **kwargs
) -> Union[List[str], Dict[str, List[str]], str]:
    """
    Map free text node name to ontology node names via sfaira cell type matching.

    For details, see also sfaira.versions.metadata.CelltypeUniverse.prepare_celltype_map_fuzzy()

    :param queries: Free text node label which is to be matched to ontology nodes.
        Can also be a list of strings to query.
    :param organism: Organism, defines ontology extension used.
    :param include_synonyms: Whether to include synonyms of nodes in string search.
    :param anatomical_constraint: Whether to require suggestions to be within a target anatomy defined within UBERON.
    :param omit_target_list: Ontology nodes to not match to.
    :param n_suggest: Number of cell types to suggest per search strategy.
    :param choices_for_perfect_match: Whether to give additional matches if a perfect match was found. Note that there
        are cases in which an apparent perfect match corresponds to a general term which could be specified knowing the
        anatomic location of the sample. If this is False and a perfect match is found, only this perfect match is
        returned as a string, rather than as a list.
    :param keep_strategy: Whether to keep search results structured by search strategy.
        For details, see also sfaira.versions.metadata.CelltypeUniverse.prepare_celltype_map_fuzzy()
    :param always_return_list: Also return a list over queries if only one query was given.
    :param threshold_for_partial_matching: Maximum fuzzy match score below which lenient matching (ratio) is
        extended through partial_ratio.
    :param **kwargs: Additional parameters to CelltypeUniverse.
    :return: List over queries, each entry is:
        A list of high priority matches or perfect match (see choices_for_perfect_match) or, if keep_strategy,
        dictionary of lists of search strategies named by strategy name. If a search strategy yields perfect matches, it
        does not return a list of strings but just a single string.
    """
    if isinstance(queries, str):
        queries = [queries]
    cu = CelltypeUniverse(organism=organism, **kwargs)
    matches_to_return = {}
    matches = cu.prepare_celltype_map_fuzzy(
        source=queries,
        match_only=False,
        include_synonyms=include_synonyms,
        anatomical_constraint=anatomical_constraint,
        choices_for_perfect_match=choices_for_perfect_match,
        omit_list=[],
        omit_target_list=omit_target_list,
        n_suggest=n_suggest,
        threshold_for_partial_matching=threshold_for_partial_matching,
    )
    # Prepare the output:
    for x, matches_i in zip(queries, matches):
        matches_i = matches_i[0]
        # Flatten list of lists:
        # Flatten dictionary of lists and account for string rather than list entries.
        if len(matches_i.values()) == 1 and isinstance(list(matches_i.values())[0], str):
            matches_flat = list(matches_i.values())[0]
        else:
            matches_flat = []
            for xx in matches_i.values():
                if isinstance(xx, list):
                    matches_flat.extend(xx)
                else:
                    assert isinstance(xx, str)
                    matches_flat.append(xx)
        if not choices_for_perfect_match and x in matches_flat:
            matches_to_return.update({x: x})
        elif keep_strategy:
            matches_to_return.update({x: matches_i})
        else:
            matches_to_return.update({x: matches_flat})
    # Only return a list over queries if more than one query was given.
    if len(queries) == 1 and not always_return_list:
        return matches_to_return
    else:
        return matches_to_return[queries[0]]