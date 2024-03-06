"""Example Loader for extracting Calibration, QC, and Group results from the Mass Spec file"""

from collections import OrderedDict

from bbc.xlxf import *
from bbc.xfutils import *

xf_env = {
    "variables": {
        # Hardcoding for the example. In a larger loader process, this will be pulled from a meta-data sheet.
        "sample_id": "1618289",

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
        "std_labels": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12, 13],

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


class MSExtractor(XFProcessor):
    xf_env = xf_env

    sheet_defs = [
        std_replicate_sheet_def,
    ]

if __name__=="__main__":
    ms_extractor = MSExtractor()

    process_workbooks(ms_extractor, data_only=True)
