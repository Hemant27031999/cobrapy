# -*- coding: utf-8 -*-

"""Test functionalities of json.py"""

from __future__ import absolute_import

import json
from os.path import join

import pytest
import jsonschema

import cobra.io as cio
from cobra.io.json_schemas.json_schema_v1 import json_schema_V1
from cobra.test.test_io.conftest import compare_models


def test_validate_json_model(data_directory):
    """Validate some JSON models according to JSON-schema v1"""
    # JSON models to be validated
    JSON_models = ["mini.json", "e_coli_core.json", "salmonella.json"]
    for model in JSON_models:
        assert cio.validate_json_model(join(data_directory, model),
                                       1) == (True, "")


def test_load_json_model(data_directory, mini_model):
    """Test the reading of JSON model."""
    json_model = cio.load_json_model(join(data_directory, "mini.json"))
    assert compare_models(mini_model, json_model) is None


def test_save_json_model(tmpdir, mini_model):
    """Test the writing of JSON model."""
    output_file = tmpdir.join("mini.json")
    cio.save_json_model(mini_model, output_file.strpath, pretty=True)
    # validate against JSONSchema
    with open(output_file.strpath, "r") as infile:
        assert cio.validate_json_model(infile, 1) == (True, "")
