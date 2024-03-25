# some tools for iteration
from collections import OrderedDict
from itertools import product

# basic bbc import
from bbc.xlxf import (
    SheetFields,
    Address,
    Rf,
    FieldValue,
    EnvRef,
    process_workbooks,
    AutoProcessor,
    XLStringJoin,
    XFProcessor,
    TitleTable,
    EnvDict,
    TableValue,
    TableColumnValues
)
from bbc.xfutils import (
    iso_date,
    DictUpdate,
    b_starts_with_a,
    add_suffix,
    zip_lists,
    list_xf,
    xf_match_values,
    add_to_value,
    get_by_index
)

from pprint import pprint

import bbc.xlxf.core
bbc.xlxf.core.sheet_name_cmp = b_starts_with_a

__doc__ = """ """
__errors__ = """ """

xf_env = {

    "variables": {

        # loading the big table-- need diff key columns for qc vs std
        "qc_table": {
            "type": TitleTable,
            "params": {
                "sheet_name": "MZ-",  # the mass spec sheet starts with "MZ-"
                "column_header": "Index",
                "auto_headers": True,
                "key_columns": ["Sample ID"],
            },
            # "debug": print,
        },
        "std_table": {
            "type": TitleTable,  # SheetTable: table_address: Address(SheetName!A2)
            "params": {
                "sheet_name": "MZ-",
                "column_header": "Index",
                "auto_headers": True,
                "key_columns": ["Index"],  # the std rows are NOT unique so we have to be clever here
            },
            # "debug": print,
        },

        # for qcs, we can look-up directly
        "replicate_suffix": ["", "_0", "_1", "_2", "_3", "_4", "_5"],

        # the qc values-- we are assuming these are always the same, & come from the machine
        "qc_names": ["ULQC", "LQC", "MQC", "HQC"],

        # let's keep everything in the env-- we are assuming these are always the same, & come from the machine
        "qc_name_map": {
            "ULQC": "QC1",
            "LQC": "QC2",
            "MQC": "QC3",
            "HQC": "QC4",
        },

        # the std sample names-- we are assuming these are always the same, & come from the machine
        "std_names": ["STD-01", "STD-02", "STD-03", "STD-04", "STD-05", "STD-06", "STD-07",
                      "STD-08", "STD-09", "STD-10", "STD-11", "STD-12", "STD-13"],

        # the samle name list, and the index list... we need to zip these
        "sample_ids": {
            "requires": "std_table",
            "type": TableColumnValues,
            "params": {
                "table": Rf("std_table"),
                "column": "Sample ID"
            },
            "xf": list,
            # "debug": pprint,
        },
        "index_ids": {
            "requires": "std_table",
            "type": TableColumnValues,
            "params": {
                "table": Rf("std_table"),
                "column": "Index"
            },
            "xf": [list, list_xf(str)],
            # "debug": pprint,
        },

        # zip the two lists together
        "index_and_sample": {
            "requires": ["sample_ids", "index_ids", "std_names"],
            "type": zip_lists(include=Rf("std_names"), rf=True),
            "params": [Rf("index_ids"), Rf("sample_ids")],
            "debug": pprint,
        },

    }
}

qc_sheet_def_odd = {
    "sheet_name": "QC Table (Odd Replicates)",
    "row_iterator": [
        (Rf("qc_names"), "qc_name"),
    ],
    "row_id": True,
    "columns": [
        {
            "header": "Sample Name",
            "xf": EnvDict("qc_name_map", Rf("qc_name"))
        },
        {
            "header": "Nominal Concentration (nM)",
            "xf": TableValue(Rf("qc_table"), Rf("qc_name"), "Actual Concentration")
        },
        {
            "header": "1 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 0), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "1 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 0), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "3 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 2), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "3 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 2), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "5 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 4), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "5 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 4), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "7 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 6), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "7 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 6), dereference_suffix=True)),
                "Accuracy"
            )
        },
    ]
}

qc_sheet_def_even = {
    "sheet_name": "QC Table (Even Replicates)",
    "row_iterator": [
        (Rf("qc_names"), "qc_name"),
    ],
    "row_id": True,
    "columns": [
        {
            "header": "Sample Name",
            "xf": EnvDict("qc_name_map", Rf("qc_name"))
        },
        {
            "header": "Nominal Concentration (nM)",
            "xf": TableValue(Rf("qc_table"), Rf("qc_name"), "Actual Concentration")
        },
        {
            "header": "2 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 1), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "2 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 1), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "4 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 3), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "4 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 3), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "6 - Calculated Concentration (nM)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 5), dereference_suffix=True)),
                "Calculated Concentration"
            )
        },
        {
            "header": "6 - Accuracy (%)",
            "xf": TableValue(
                Rf("qc_table"),
                EnvRef(
                    "qc_name",
                    xf_env=add_suffix(suffix=EnvDict("replicate_suffix", 5), dereference_suffix=True)),
                "Accuracy"
            )
        },
        {
            "header": "8 - Calculated Concentration (nM)",
            "xf": ""
        },
        {
            "header": "8 - Accuracy (%)",
            "xf": "0"
        },
    ]
}

std_sheet_def = {
    "sheet_name": "STD Table",
    "row_iterator": [
        (EnvRef("std_names", xf=[len, range]), "std_idx"),
    ],
    "row_id": True,
    "columns": [
        {
            "header": "Sample Name",
            "xf": EnvDict(
                "std_names",
                Rf("std_idx"),
                xf=xf_match_values(patterns="-0|-", re=True, substitute=True, replace=" ")
            )
        },
        {
            "header": "Nominal Concentration (nM)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    EnvRef("std_idx"),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Actual Concentration",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "1 - Caclulated Concentration (nM)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx"),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Calculated Concentration",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "1 - Accuracy (%)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx"),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Accuracy",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "2 - Caclulated Concentration (nM)",
            "xf": TableValue(  # STD-02, block 2: "index" = 218, std_idx = 1
                Rf("std_table"),
                EnvDict( # => index_and_sample[1+13] => index_and_sample[14] = (218, STD-02)
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx", xf=add_to_value(13)),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ), # => 218
                "Calculated Concentration",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "2 - Accuracy (%)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx", xf=add_to_value(13)),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Accuracy",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "3 - Caclulated Concentration (nM)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx", xf=add_to_value(26)),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Calculated Concentration",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "3 - Accuracy (%)",
            "xf": TableValue(
                Rf("std_table"),
                EnvDict(
                    # this is a list of the indices and samples
                    "index_and_sample",
                    # the index is given by std_idx + (13 * [replicate - 1])
                    EnvRef("std_idx", xf=add_to_value(26)),
                    # we need the first element as an int
                    xf=get_by_index(0),
                ),
                "Accuracy",
                allow_int_keys=True,  # to be safe with our str/int conversions
            )
        },
        {
            "header": "4 - Caclulated Concentration (nM)",
            "xf": ""
        },
        {
            "header": "4 - Accuracy (%)",
            "xf": "0"
        }
    ]
}


class Assay(XFProcessor):

    xf_env = xf_env
    sheet_defs = [
        qc_sheet_def_even,
        qc_sheet_def_odd,
        std_sheet_def
    ]


if __name__ == "__main__":
    import os.path

    _assay = Assay()
    process_workbooks(_assay, data_only=True, print_env=False)
