# -*- coding: utf-8 -*-

from __future__ import absolute_import

from ast import literal_eval
from collections import OrderedDict
from operator import attrgetter, itemgetter

import numpy as np
from numpy import bool_, float_
from six import iteritems, string_types

from cobra.core import (Gene, Metabolite, Model, Reaction,
                        UserDefinedConstraint,
                        ConstraintComponent, Group)
from cobra.core.metadata import MetaData, Notes
from cobra.util.solver import set_objective


_REQUIRED_REACTION_ATTRIBUTES = [
    "id",
    "name",
    "metabolites",
    "lower_bound",
    "upper_bound",
    "gene_reaction_rule",
]
_ORDERED_OPTIONAL_REACTION_KEYS = [
    "objective_coefficient",
    "subsystem",
    "notes",
    "annotation",
]
_OPTIONAL_REACTION_ATTRIBUTES = {
    "objective_coefficient": 0,
    "subsystem": "",
    "notes": {},
    "annotation": {},
}

_REQUIRED_METABOLITE_ATTRIBUTES = ["id", "name", "compartment"]
_ORDERED_OPTIONAL_METABOLITE_KEYS = [
    "charge",
    "formula",
    "_bound",
    "notes",
    "annotation",
]
_OPTIONAL_METABOLITE_ATTRIBUTES = {
    "charge": None,
    "formula": None,
    "_bound": 0,
    "notes": {},
    "annotation": {},
}

_REQUIRED_GENE_ATTRIBUTES = ["id", "name"]
_ORDERED_OPTIONAL_GENE_KEYS = ["notes", "annotation"]
_OPTIONAL_GENE_ATTRIBUTES = {
    "notes": {},
    "annotation": {},
}

_REQUIRED_GROUP_ATTRIBUTES = ["id", "kind", "members"]
_ORDERED_OPTIONAL_GROUP_KEYS = ["name", "notes", "annotation"]
_OPTIONAL_GROUP_ATTRIBUTES = {
    "name": '',
    "notes": {},
    "annotation": {},
}

_REQUIRED_CONSTRAINT_ATTRIBUTES = ["lower_bound",
                                   "upper_bound", "constraint_comps"]
_ORDERED_OPTIONAL_CONSTRAINT_KEYS = ["id", "name", "notes", "annotation"]
_OPTIONAL_CONSTRAINT_ATTRIBUTES = {
    "id": None,
    "name": None,
    "notes": {},
    "annotation": {},
}

_REQUIRED_CONSTRAINT_COMP_ATTRIBUTES = ["variable", "coefficient", "variable_type"]
_ORDERED_OPTIONAL_CONSTRAINT_COMP_KEYS = ["id", "name", "notes", "annotation"]
_OPTIONAL_CONSTRAINT_COMP_ATTRIBUTES = {
    "id": None,
    "name": None,
    "notes": {},
    "annotation": {},
}

_ORDERED_OPTIONAL_MODEL_KEYS = ["name", "compartments", "notes", "annotation"]
_OPTIONAL_MODEL_ATTRIBUTES = {
    "name": None,
    #  "description": None, should not actually be included
    "compartments": [],
    "notes": {},
    "annotation": {},
}


def _fix_type(value):
    """convert possible types to str, float, and bool"""
    # Because numpy floats can not be pickled to json
    if isinstance(value, string_types):
        return str(value)
    if isinstance(value, float_):
        return float(value)
    if isinstance(value, bool_):
        return bool(value)
    if isinstance(value, set):
        return list(value)
    if isinstance(value, dict):
        return OrderedDict((key, value[key]) for key in sorted(value))
    if isinstance(value, Notes):
        return str(value)
    # handle legacy Formula type
    if value.__class__.__name__ == "Formula":
        return str(value)
    if value is None:
        return ""
    return value


def _annotation_to_dict(annotation):
    anno_str = str(annotation.cvterms)
    anno_dict = literal_eval(anno_str)
    final_dict = {"cvterms": anno_dict}

    if annotation.history.is_set_history():
        history_str = str(annotation.history)
        history_dict = literal_eval(history_str)
        final_dict["history"] = history_dict

    if 'sbo' in annotation and annotation['sbo'] != []:
        final_dict['sbo'] = annotation['sbo'][0]

    return final_dict


def _extract_annotation(data):
        cvterms = data["cvterms"] if "cvterms" in data else None
        history = data["history"] if "history" in data else None
        keyValueDict = data["history"] if "keyValueDict" in data else None

        if cvterms is not None or history is not None or \
                keyValueDict is not None:
            annotation = MetaData(cvterms, history, keyValueDict)
        else:
            annotation = MetaData()
            annotation.cvterms.add_simple_annotations(data)
        if "sbo" in data:
            annotation["sbo"] = [data["sbo"]]
        return annotation


def _update_optional(cobra_object, new_dict, optional_attribute_dict,
                     ordered_keys):
    """update new_dict with optional attributes from cobra_object"""
    for key in ordered_keys:
        default = optional_attribute_dict[key]
        value = getattr(cobra_object, key)
        if key == 'notes' and (value.notes_xhtml is None or
                               len(value.notes_xhtml) == 0):
            continue
        if value is None or value == default:
            continue
        if key == "annotation":
            value = _annotation_to_dict(value)
        new_dict[key] = _fix_type(value)


def metabolite_to_dict(metabolite):
    new_met = OrderedDict()
    for key in _REQUIRED_METABOLITE_ATTRIBUTES:
        new_met[key] = _fix_type(getattr(metabolite, key))
    _update_optional(
        metabolite,
        new_met,
        _OPTIONAL_METABOLITE_ATTRIBUTES,
        _ORDERED_OPTIONAL_METABOLITE_KEYS,
    )
    return new_met


def metabolite_from_dict(metabolite):
    new_metabolite = Metabolite()
    for k, v in iteritems(metabolite):
        if k == "annotation":
            value = _extract_annotation(v)
            setattr(new_metabolite, k, value)
        elif k == "notes":
            notes_data = Notes(v)
            setattr(new_metabolite, k, notes_data)
        else:
            setattr(new_metabolite, k, v)
    return new_metabolite


def gene_to_dict(gene):
    new_gene = OrderedDict()
    for key in _REQUIRED_GENE_ATTRIBUTES:
        new_gene[key] = _fix_type(getattr(gene, key))
    _update_optional(
        gene, new_gene, _OPTIONAL_GENE_ATTRIBUTES, _ORDERED_OPTIONAL_GENE_KEYS
    )
    return new_gene


def gene_from_dict(gene):
    new_gene = Gene(gene["id"])
    for k, v in iteritems(gene):
        if k == "annotation":
            value = _extract_annotation(v)
            setattr(new_gene, k, value)
        elif k == "notes":
            notes_data = Notes(v)
            setattr(new_gene, k, notes_data)
        else:
            setattr(new_gene, k, v)
    return new_gene


def reaction_to_dict(reaction):
    new_reaction = OrderedDict()
    for key in _REQUIRED_REACTION_ATTRIBUTES:
        if key != "metabolites":
            if key == "lower_bound" and (
                np.isnan(reaction.lower_bound) or np.isinf(reaction.lower_bound)
            ):
                new_reaction[key] = str(_fix_type(getattr(reaction, key)))
            elif key == "upper_bound" and (
                np.isnan(reaction.upper_bound) or np.isinf(reaction.upper_bound)
            ):
                new_reaction[key] = str(_fix_type(getattr(reaction, key)))
            else:
                new_reaction[key] = _fix_type(getattr(reaction, key))
            continue
        mets = OrderedDict()
        for met in sorted(reaction.metabolites, key=attrgetter("id")):
            mets[str(met)] = reaction.metabolites[met]
        new_reaction["metabolites"] = mets
    _update_optional(
        reaction,
        new_reaction,
        _OPTIONAL_REACTION_ATTRIBUTES,
        _ORDERED_OPTIONAL_REACTION_KEYS,
    )
    return new_reaction


def reaction_from_dict(reaction, model):
    new_reaction = Reaction()
    for k, v in iteritems(reaction):
        if k in {"objective_coefficient", "reversibility", "reaction"}:
            continue
        elif k == "metabolites":
            new_reaction.add_metabolites(
                OrderedDict(
                    (model.metabolites.get_by_id(str(met)), coeff)
                    for met, coeff in iteritems(v)
                )
            )
        else:
            if k == "annotation":
                value = _extract_annotation(v)
                setattr(new_reaction, k, value)
            elif k == "notes":
                notes_data = Notes(v)
                setattr(new_reaction, k, notes_data)
            elif k == "lower_bound" or k == "upper_bound":
                setattr(new_reaction, k, float(v))
            else:
                setattr(new_reaction, k, v)
    return new_reaction


def const_comp_to_dict(component):
    new_const_comp = OrderedDict()
    for key in _REQUIRED_CONSTRAINT_COMP_ATTRIBUTES:
        new_const_comp[key] = _fix_type(getattr(component, key))
    _update_optional(component, new_const_comp,
                     _OPTIONAL_CONSTRAINT_COMP_ATTRIBUTES,
                     _ORDERED_OPTIONAL_CONSTRAINT_COMP_KEYS)
    return new_const_comp


def user_defined_const_to_dict(constraint):
    new_const = OrderedDict()
    for key in _REQUIRED_CONSTRAINT_ATTRIBUTES:
        if key != "constraint_comps":
            new_const[key] = _fix_type(getattr(constraint, key))
            continue
        new_const["constraint_comps"] = list(map(const_comp_to_dict,
                                                 constraint.constraint_comps))
    _update_optional(constraint, new_const, _OPTIONAL_CONSTRAINT_ATTRIBUTES,
                     _ORDERED_OPTIONAL_CONSTRAINT_KEYS)
    return new_const


def user_defined_const_from_dict(constraint):
    new_user_defined_const = UserDefinedConstraint()
    for k, v in iteritems(constraint):
        if k == "constraint_comps":
            for comp in v:
                new_comp = ConstraintComponent(**comp)
                new_user_defined_const.add_constraint_comps([new_comp])
        elif k == "annotation":
            value = _extract_annotation(v)
            setattr(new_user_defined_const, k, value)
        elif k == "notes":
            notes_data = Notes(v)
            setattr(new_user_defined_const, k, notes_data)
        else:
            setattr(new_user_defined_const, k, v)
    return new_user_defined_const


def group_to_dict(group):
    new_group = OrderedDict()
    for key in _REQUIRED_GROUP_ATTRIBUTES:
        if key != "members":
            new_group[key] = _fix_type(getattr(group, key))
            continue
        members = []
        for member in group.members:
            json_member = {"idRef": member.id, "type": type(member).__name__}
            members.append(json_member)
        new_group["members"] = members
    _update_optional(group, new_group, _OPTIONAL_GROUP_ATTRIBUTES,
                     _ORDERED_OPTIONAL_GROUP_KEYS)
    return new_group


def group_from_dict(group, model):
    new_group = Group(group["id"])
    for k, v in iteritems(group):
        if k == "annotation":
            value = _extract_annotation(v)
            setattr(new_group, k, value)
        elif k == "notes":
            notes_data = Notes(v)
            setattr(new_group, k, notes_data)
        elif k == "members":
            cobra_members = []
            for member in group["members"]:
                if member["type"] == "Reaction":
                    cobra_obj = model.reactions.get_by_id(member["idRef"])
                    cobra_members.append(cobra_obj)
                elif member["type"] == "Metabolite":
                    cobra_obj = model.metabolites.get_by_id(member["idRef"])
                    cobra_members.append(cobra_obj)
                elif member["type"] == "Gene":
                    cobra_obj = model.genes.get_by_id(member["idRef"])
                    cobra_members.append(cobra_obj)
            new_group.add_members(cobra_members)
        else:
            setattr(new_group, k, v)
    return new_group


def model_to_dict(model, sort=False):
    """Convert model to a dict.

    Parameters
    ----------
    model : cobra.Model
        The model to reformulate as a dict.
    sort : bool, optional
        Whether to sort the metabolites, reactions, and genes or maintain the
        order defined in the model.

    Returns
    -------
    OrderedDict
        A dictionary with elements, 'genes', 'compartments', 'id',
        'metabolites', 'notes' and 'reactions'; where 'metabolites', 'genes'
        and 'metabolites' are in turn lists with dictionaries holding all
        attributes to form the corresponding object.

    See Also
    --------
    cobra.io.model_from_dict
    """
    obj = OrderedDict()
    obj["metabolites"] = list(map(metabolite_to_dict, model.metabolites))
    obj["reactions"] = list(map(reaction_to_dict, model.reactions))
    obj["genes"] = list(map(gene_to_dict, model.genes))
    obj["groups"] = list(map(group_to_dict, model.groups))
    obj["user_defined_constraints"] = list(map(user_defined_const_to_dict,
                                               model.user_defined_const))
    obj["id"] = model.id
    _update_optional(
        model, obj, _OPTIONAL_MODEL_ATTRIBUTES, _ORDERED_OPTIONAL_MODEL_KEYS
    )
    if sort:
        get_id = itemgetter("id")
        obj["metabolites"].sort(key=get_id)
        obj["reactions"].sort(key=get_id)
        obj["genes"].sort(key=get_id)
        obj["groups"].sort(key=get_id)
    return obj


def model_from_dict(obj):
    """Build a model from a dict.

    Models stored in json are first formulated as a dict that can be read to
    cobra model using this function.

    Parameters
    ----------
    obj : dict
        A dictionary with elements, 'genes', 'compartments', 'id',
        'metabolites', 'notes' and 'reactions'; where 'metabolites', 'genes'
        and 'metabolites' are in turn lists with dictionaries holding all
        attributes to form the corresponding object.

    Returns
    -------
    cora.core.Model
        The generated model.

    See Also
    --------
    cobra.io.model_to_dict
    """
    if "reactions" not in obj:
        raise ValueError("Object has no reactions attribute. Cannot load.")
    model = Model()
    model.add_metabolites(
        [metabolite_from_dict(metabolite) for metabolite in obj["metabolites"]]
    )
    model.genes.extend([gene_from_dict(gene) for gene in obj["genes"]])
    model.add_reactions(
        [reaction_from_dict(reaction, model) for reaction in obj["reactions"]]
    )
    objective_reactions = [
        rxn for rxn in obj["reactions"] if rxn.get("objective_coefficient", 0) != 0
    ]
    coefficients = {
        model.reactions.get_by_id(rxn["id"]): rxn["objective_coefficient"]
        for rxn in objective_reactions
    }
    if 'groups' in obj:
        model.add_groups(
            [group_from_dict(group, model) for group in obj['groups']]
        )
    if "user_defined_constraints" in obj:
        model.add_user_defined_constraints(
            [user_defined_const_from_dict(cons) for cons in obj["user_defined_constraints"]]
        )
    set_objective(model, coefficients)
    for k, v in iteritems(obj):
        if k == "annotation":
            value = _extract_annotation(v)
            setattr(model, k, value)
        elif k == "notes":
            notes_data = Notes(v)
            setattr(model, k, notes_data)
        elif k in {'id', 'name', 'notes', 'compartments'}:
            setattr(model, k, v)
    return model