"""Example Loader for extracting Calibration, QC, and Group results from the Mass Spec file"""

from collections import OrderedDict

from bbc.xlxf import *
from bbc.xfutils import *

import bbc.xlxf.core
bbc.xlxf.core.sheet_name_cmp = a_re_eq_b

xf_env = {
    "variables": {

        # Hardcoding for the example. In a larger loader process, this will be pulled from a meta-data sheet.
        "sample_id": "\d+",

        # Tables
        "ms_table": {
            # The result sheet is named after the sample id
            "requires": ["sample_id"],

            "type": TitleTable,
            "params": {
                "sheet_name": Rf("sample_id"),

                # Use the "FileName" column to locate the table, no need for a title
                "column_header": "FileName",
                "auto_headers": True,

                # FileName is also a potential option for a key_column, but the STD samples would be tricky with that.
                "key_columns": ["Sample ID", "Specified Conc"]
            }
        },

        # Variables

        # STDs are labeled from 1-13, using both "STD 1" and "STD-01" formats
        "std_labels": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],

        # These are stored as integers in the sheet
        "std_conc_values": [
            1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000
        ],

        # Zip labels and concs for the iterator. this could be done directly, but it makes a simple exmaple of
        # more creating variables from variables
        "std_labels_conc_values": {
            "requires": ["std_labels", "std_conc_values"],
            "type": lambda a, b: zip(a, b),
            "params": [ Rf("std_labels"), Rf("std_conc_values") ],
            "xf": list
        },

        # STD replicates are not directly labeled, use row offsets
        "std_replicate_offsets": [0, 1, 2],

        # qc values
        "qc_labels": ["ULQC", "LQC", "MQC", "HQC"],

        # qc concs
        "qc_conc_values": [3, 30, 300, 3000],

        # zip together
        "qc_labels_conc_values": {
            "requires": ["qc_labels", "qc_conc_values"],
            "type": zip,
            "params": [Rf("qc_labels"), Rf("qc_conc_values")],
            "xf": list,
            # "debug": print,
        },

        # let's keep everything in the env-- we are assuming these are always the same, & come from the machine
        "qc_name_map": {
            "ULQC": "QC1",
            "LQC": "QC2",
            "MQC": "QC3",
            "HQC": "QC4",
        },

    }
}

std_replicate_sheet_def = {
    "sheet_name": "STD Calibration Curves",

    "row_iterator": [
        (Rf("std_labels_conc_values"), "std_label_conc"),
    ],

    "row_env_update": DictUpdate(OrderedDict((
        ("std_label", lambda env: env["std_label_conc"][0]),
        ("std_conc", lambda env: env["std_label_conc"][1]),

        ("ms_sample_name", lambda env: "STD-{std_label:02}".format(**env)),  # zero-pad single digits
        ("sample_name", lambda env: "STD {std_label}".format(**env)),
    ))),

    "columns": [
        {
            "header": "Sample Name",
            "xf":     Rf("sample_name")
        },
        {
            "header": "Nominal Concentration (nM)",
            "xf":     EnvRef("std_conc", xf=lambda v: f"{float(v):0.1f}")  # example of xf formatting
        },

        {
            "header": "Curve 1 - Calculated Concentration (nM)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=0)
        },

        {
            "header": "Curve 1 - Accuracy (%)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=0,
                                 xf_env=lambda v, env: float(v) / float(env["std_conc"])),
        },

        {
            "header": "Curve 2 - Calculated Concentration (nM)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=1)
        },

        {
            "header": "Curve 2 - Accuracy (%)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=1,
                                 xf_env=lambda v, env: float(v) / float(env["std_conc"])),
        },

        {
            "header": "Curve 3 - Calculated Concentration (nM)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=2)
        },

        {
            "header": "Curve 3 - Accuracy (%)",
            "xf":     TableValue(Rf("ms_table"), Rf("ms_sample_name", "std_conc"), "Calculated Conc", row_offset=2,
                                 xf_env=lambda v, env: float(v) / float(env["std_conc"])),
        },

        {
            "header": "Curve 4 - Calculated Concentration (nM)",
            "xf":     "",
        },

        {
            "header": "Curve 4 - Accuracy (%)",
            "xf":     0.0,
        },

    ]
}


qc_replicate_sheet_def = {
    "sheet_name": "QC Calibration",

    "row_iterator": [
        (Rf("qc_labels_conc_values"), "qc_label_conc"),
    ],

    "row_env_update": DictUpdate(OrderedDict((
        ("qc_label", lambda env: env["qc_label_conc"][0]),
        ("qc_conc", lambda env: env["qc_label_conc"][1]),
    ))),

    "columns": [
        {
            "header": "Sample Name",
            "xf": EnvDict("qc_name_map", Rf("qc_label"))
        },
        {
            "header": "Nominal Concentration (nM)",
            "xf": Rf("qc_conc")
        },
        {
            "header": "1 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("ms_table"),
                Rf("qc_label", "qc_conc"),
                "Calculated Conc",
                cmp=b_starts_with_a,  # if we give you ULQC, and you see ULQC_#, give us that row
            )
        },
        {
            "header": "1 - Accuracy (%)",
            "xf": TableValue(
                Rf("ms_table"),
                Rf("qc_label", "qc_conc"),
                "Calculated Conc",
                cmp=b_starts_with_a,
                row_offset=0,
                xf_env=lambda v, env: float(v) / float(env["qc_conc"])  # accuracy as a fraction
            ),
        },
        {
            "header": "3 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("ms_table"),
                Rf("qc_label", "qc_conc"),
                "Calculated Conc",
                cmp=b_starts_with_a,  # if we give you ULQC, and you see ULQC_#, give us that row
                row_offset=2,
            )
        },
        {
            "header": "3 - Accuracy (%)",
            "xf": ""
        },
        {
            "header": "5 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("ms_table"),
                Rf("qc_label", "qc_conc"),
                "Calculated Conc",
                cmp=b_starts_with_a,  # if we give you ULQC, and you see ULQC_#, give us that row
                row_offset=4,
            )
        },
        {
            "header": "5 - Accuracy (%)",
            "xf": ""
        },
        {
            "header": "7 - Calculated Concentration (nM)",
            "xf": ""
        },
        {
            "header": "7 - Accuracy (%)",
            "xf": ""
        },
    ]
}


class MSExtractor(XFProcessor):
    xf_env = xf_env

    sheet_defs = [
        std_replicate_sheet_def,
        qc_replicate_sheet_def
    ]

if __name__=="__main__":
    ms_extractor = MSExtractor()

    process_workbooks(ms_extractor, data_only=True)
