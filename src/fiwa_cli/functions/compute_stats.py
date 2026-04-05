from typing import List, Dict
try:
    import pandas as pd
    import numpy as np
except:
    pass

class ProjectStats():
    def __init__(self, project_style:str = ""):
        self._project_style = project_style
        self._items: List = []
#        self._items_df: pd.DataFrame = None

    def set_items(self, items):
        self._items = items
        self.op_list2df()
        if len(self._items_df) > 0:
            self.op_parse_df()

    def op_list2df(self):
        try:
            self._items_df = pd.DataFrame(self._items)
        except Exception as e:
            self._items_df = pd.DataFrame()

    def op_parse_df(self):
        if self._project_style == "ExpenseTracker":
            self._items_df["bought_date"] = pd.to_datetime(self._items_df["bought_date"], format='mixed')
            self._items_df["exchange_rate_date"] = pd.to_datetime(self._items_df["exchange_rate_date"], format='mixed')
            self._items_df["price"] = pd.to_numeric(self._items_df["price"])
            self._items_df["price_final"] = pd.to_numeric(self._items_df["price_final"])
            self._items_df["exchange_rate"] = pd.to_numeric(self._items_df["exchange_rate"])

    def aggregate_daily_df(self):
        if len(self._items_df) == 0:
            return []

        # get daily
        pdf = self._items_df[self._items_df["label_t"] == "daily"].copy()
        # Convert to datetime first, then extract date only (strips timestamp to 00:00:00)
        pdf["bought_date"] = pd.to_datetime(pdf["bought_date"], format='mixed').dt.normalize()
        k = []
        for i, idf in pdf.groupby(pd.Grouper(key='bought_date', freq='D')):
            ik = {
                "date": i,
                "items": len(idf),
            }
            for j, jdf in idf.groupby("label_m"):
                ik[f"count?{j}"] = len(jdf)
                ik[f"sum?{j}"] = jdf["price_final"].sum()
            k.append(ik)

        return k

    def aggregate_fv_df(self):
        if len(self._items_df) == 0:
            return []

        # get daily
        df_fv = self._items_df[(self._items_df["label_t"] == "fixed") | (self._items_df["label_t"] == "variable")]
        df_d = self._items_df[self._items_df["label_t"] == "daily"]
        k = []
        return k

