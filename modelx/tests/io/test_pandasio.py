
import itertools
import pandas as pd
import numpy as np
import modelx as mx
import pytest
from modelx.serialize import ziputil

from modelx.io.baseio import BaseDataSpec

# Modified from the sample code on
# https://pandas.pydata.org/docs/user_guide/advanced.html

cols = [
    ["bar", "bar", "baz", "baz", "foo", "foo", "qux", "qux"],
    ["one", "two", "one", "two", "one", "two", "one", "two"]
]
cols = list(zip(*cols))
cols = pd.MultiIndex.from_tuples(cols, names=["first", "second"])
idx = pd.MultiIndex.from_product([["A", "B"], ["c", "d", "e"]])

S_IDX1 = pd.Series(np.random.randn(8), index=range(8))
S_IDX1.index.name = "Idx"
S_IDX2 = pd.Series(np.random.randn(8), index=cols)
DF_COL2_IDX2 = pd.DataFrame(np.random.randn(6, 8), index=idx, columns=cols)

params = [[p1, *p2, p3, p4] for p1, p2, p3, p4 in
          itertools.product(
              [S_IDX1, S_IDX2, DF_COL2_IDX2],
              [("model", True), ("space", False)],
              ("write", "zip", "backup"),
              ("excel", "csv")
            )
          ]


@pytest.mark.parametrize(
    "pdobj, pstr, is_relative, save_meth, filetype",
    params)
def test_new_pandas(
        tmp_path, pdobj, pstr, is_relative, save_meth, filetype):

    m = mx.new_model()
    if pstr == "model":
        parent = m
    else:
        parent = m.new_space()

    parent_name = parent.name

    file_path = "files/testpandas.xlsx" if is_relative else (
            tmp_path / "testpandas.xlsx")

    parent.new_pandas(name="pdref", path=file_path,
                 data=pdobj, filetype=filetype)

    for nth in "12":
        model_name = "model%s" % nth
        model_loc = tmp_path / model_name
        file_loc = (model_loc / file_path) if is_relative else file_path

        # Save, close and restore
        if save_meth == "backup":
            getattr(m, save_meth)(model_loc)
            m.close()
            m = mx.restore_model(model_loc)
        else:
            getattr(m, save_meth)(model_loc)
            m.close()
            assert ziputil.exists(file_loc)
            m = mx.read_model(model_loc)

        parent = m if pstr == "model" else m.spaces[parent_name]

        m._impl.system._check_sanity(check_members=False)
        m._impl._check_sanity()

        if isinstance(pdobj, pd.DataFrame):
            pd.testing.assert_frame_equal(parent.pdref, pdobj)
        elif isinstance(pdobj, pd.Series):
            pd.testing.assert_series_equal(parent.pdref, pdobj)

    m.close()


params2 = zip([S_IDX1, S_IDX2, DF_COL2_IDX2], ["B2:B9", "C2:C9", "C4:J9"])


@pytest.mark.parametrize("pdobj, range_", params2)
def test_new_pandas_change_excel(tmp_path, pdobj, range_):

    p = mx.new_model().new_space("SpaceA")

    path = "files/testpandas.xlsx"
    p.new_pandas(name="pdref", path=path, data=pdobj, filetype="excel")

    p.model.write(tmp_path / "model")
    p.model.close()

    import openpyxl as pyxl

    wb = pyxl.load_workbook(tmp_path / "model" / path)
    ws = wb.worksheets[0]

    for row in ws[range_]:
        for cel in row:
            cel.value += 1

    wb.save(tmp_path / "model" / path)

    m2 = mx.read_model(tmp_path / "model")
    p2 = m2.spaces["SpaceA"]

    if isinstance(pdobj, pd.DataFrame):
        pd.testing.assert_frame_equal(p2.pdref, pdobj + 1)
    elif isinstance(pdobj, pd.Series):
        pd.testing.assert_series_equal(p2.pdref, pdobj + 1)


    m2.close()
