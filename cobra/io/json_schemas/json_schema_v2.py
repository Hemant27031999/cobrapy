# This version of JSON schema is still under development

json_schema_V2 = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "COBRA",
    "description": "JSON representation of COBRA model",
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {
            "type": "string",
            "default": "2",
        },

        "reactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "metabolites": {
                        "type": "object",
                        "patternProperties": {
                            ".*": {"type": "number"},
                        }
                    },
                    "gene_reaction_rule": {"type": "string"},
                    "lower_bound": {"type": "number"},
                    "upper_bound": {"type": "number"},
                    "objective_coefficient": {
                        "type": "number",
                        "default": 0,
                    },
                    "subsystem": {"type": "string"},
                    "notes": {"type": "object"},
                    "annotation": {"type": "object"},
                },
                "required": ["id", "name", "metabolites", "lower_bound",
                             "upper_bound", "gene_reaction_rule"],
                "additionalProperties": False,
            }
        },
        "metabolites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "compartment": {
                        "type": "string",
                        "pattern": "[a-z]{1,2}"
                    },
                    "charge": {"type": "integer"},
                    "formula": {"type": "string"},
                    "_bound": {
                        "type": "number",
                        "default": 0
                    },
                    "notes": {"type": "object"},
                    "annotation": {"type": "object"},
                },
                "required": ["id", "name", "compartment"],
                "additionalProperties": False,
            }

        },
        "genes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "notes": {"type": "object"},
                    "annotation": {"type": "object"},
                },
                "required": ["id", "name"],
                "additionalProperties": False,
            }

        },
        "compartments": {
            "type": "object",
            "patternProperties": {
                "[a-z]{1,2}": {"type": "string"}
            }
        },
        "notes": {"type": "object"},
        "annotation": {"type": "object"},
    },
    "required": ["id", "reactions", "metabolites", "genes"],
    "additionalProperties": False,
}
