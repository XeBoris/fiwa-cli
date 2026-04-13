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

            self._items_df["bought_date"] = pd.to_datetime(self._items_df["bought_date"], format='mixed').dt.normalize()
            self._items_df["exchange_rate"] = pd.to_datetime(self._items_df["exchange_rate"],
                                                             format='mixed').dt.normalize()
            self._items_df.sort_values(by="bought_date", inplace=True)

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

    def aggr_period(self, return_df=False):
        """Aggregate and analyze financial data by period with comprehensive breakdown.

        This method performs a comprehensive financial analysis of items within a period,
        breaking down transactions by type (fixed, variable, daily) and category
        (home vs travel). It calculates totals, applies expense/revenue multipliers,
        and generates summary statistics with optional DataFrame conversion.

        The method processes the internal items dataframe (`_items_df`) and categorizes
        transactions based on their labels:
            - **Fixed/Variable** (`label_t`): Regular recurring transactions
            - **Daily** (`label_t`): Day-to-day expenses/income
            - **Travel** (`label_s`): Travel-related daily transactions
            - **Home** (`label_s`): Non-travel daily transactions

        Workflow:
            1. Apply expense/revenue multipliers (-1 for expenses, +1 for revenue)
            2. Calculate adjusted final prices (price_final * multiplier)
            3. Split data into Fixed/Variable, Daily Travel, and Daily Home
            4. Aggregate by bank account (`label_b`) and transaction type (`label_c`)
            5. Generate summary statistics and categorized breakdowns
            6. Optionally convert results to pandas DataFrames

        Args:
            return_df (bool, optional): If True, returns all data as pandas DataFrames.
                If False, returns native Python data structures (dict/list).
                Defaults to False.

        Returns:
            tuple: A tuple of five elements containing aggregated financial data.
                The type of each element depends on the `return_df` parameter:

                **When return_df=False (default):**

                - **d0** (dict): Overall period totals with keys:
                    - "total_fv" (float): Total for fixed/variable transactions
                    - "total_daily" (float): Total for all daily transactions
                    - "total_daily_trav" (float): Total for travel-related daily transactions
                    - "total_daily_home" (float): Total for home/non-travel daily transactions

                - **d1** (list[dict]): High-level summary by account, each dict contains:
                    - "label" (str): Account name or category
                    - "value" (float): Net amount for the category
                    Special entries: "Daily Home", "Daily Travel", "Savings (EoM)"

                - **k_fv** (list[dict]): Detailed fixed/variable transactions
                - **k_home** (list[dict]): Detailed daily home transactions
                - **k_trav** (list[dict]): Detailed daily travel transactions

                **When return_df=True:**

                - **d0** (pd.DataFrame): Overall period totals with columns:
                    - `label` (str): Total category name
                    - `value` (float): Monetary value (expenses negative, revenue positive)

                - **d1** (pd.DataFrame): High-level summary by account with columns:
                    - `label` (str): Account name or category
                    - `value` (float): Net amount for the category
                    Sorted by value in descending order with "Savings (EoM)" at the bottom.

                - **k_fv** (pd.DataFrame): Detailed fixed/variable transactions with columns:
                    - `label` (str): Bank account name (`label_b`)
                    - `transaction` (str): Transaction type (`label_c`)
                    - `value` (float): Net transaction value

                - **k_home** (pd.DataFrame): Detailed daily home transactions with columns:
                    - `label` (str): Bank account name (`label_b`)
                    - `transaction` (str): Transaction type (`label_c`)
                    - `value` (float): Net transaction value

                - **k_trav** (pd.DataFrame): Detailed daily travel transactions with columns:
                    - `label` (str): Bank account name (`label_b`)
                    - `transaction` (str): Transaction type (`label_c`)
                    - `value` (float): Net transaction value

        Raises:
            AttributeError: If `_items_df` is not initialized or is empty
            KeyError: If required label columns are missing from the dataframe
            TypeError: If dataframe columns have incorrect data types

        Example:
            **Using native Python structures (default):**

            >>> stats = ProjectStats(project_style="ExpenseTracker")
            >>> stats.set_items(items_list)
            >>> d0, d1, k_fv, k_home, k_trav = stats.aggr_period()
            >>>
            >>> # View overall totals as dict
            >>> print(d0)
            {'total_fv': -1234.56, 'total_daily': -987.65, 
             'total_daily_trav': -234.00, 'total_daily_home': -753.65}
            >>>
            >>> # View account summary as list
            >>> print(d1)
            [{'label': 'CheckingAccount', 'value': -500.00},
             {'label': 'Daily Home', 'value': -753.65},
             {'label': 'Daily Travel', 'value': -234.00},
             {'label': 'Savings (EoM)', 'value': -1487.65}]

            **Using pandas DataFrames:**

            >>> d0, d1, k_fv, k_home, k_trav = stats.aggr_period(return_df=True)
            >>>
            >>> # View overall totals as DataFrame
            >>> print(d0)
                         label      value
            0        total_fv  -1234.56
            1    total_daily   -987.65
            2  total_daily_trav -234.00
            3  total_daily_home -753.65
            >>>
            >>> # View account summary as DataFrame (sorted)
            >>> print(d1)
                      label      value
            0  CheckingAccount  -500.00
            1      Daily Home  -753.65
            2    Daily Travel  -234.00
            3  Savings (EoM) -1487.65

        Notes:
            - Expenses are represented as negative values (multiplier = -1)
            - Revenue/Income is represented as positive values (multiplier = +1)
            - The method assumes specific label structure in the dataframe:
                - `label_c`: Transaction category (used for expense/revenue classification)
                - `label_t`: Transaction type (fixed/variable/daily)
                - `label_b`: Bank account label
                - `label_s`: Secondary labels (list) - checked for 'travel' keyword
            - Travel transactions are identified by the presence of 'travel' in `label_s`
            - All monetary values are in the project's main currency
            - The "Savings (EoM)" entry represents the net balance for the period
            - When `return_df=True`, d1 is sorted by value in descending order
            - Use `return_df=False` for lightweight operations or JSON serialization
            - Use `return_df=True` for data analysis, visualization, or further pandas operations

        See Also:
            aggregate_daily_df: For daily transaction aggregation
            aggregate_fv_df: For fixed/variable transaction aggregation
            op_parse_df: For initial dataframe preparation
        """
        df = self._items_df.copy()

        for k, krow in df.iterrows():
            if krow["label_c"] == "expenses":
                c_multiplier = -1
            else:
                c_multiplier = 1
            df.at[k, "e"] = c_multiplier

        df["price_final1"] = df["e"] * df["price_final"]

        # we need
        df_fv = df[(df["label_t"] == "fixed") | (df["label_t"] == "variable")].copy()

        df_d = df[df["label_t"] == "daily"].copy()
        df_d_trav = df_d[df_d["label_s"].apply(lambda x: 'travel' in x)].copy()
        df_d_home = df_d[df_d["label_s"].apply(lambda x: 'travel' not in x)].copy()

        # build a dataframe with all the totals:
        d0 = {
            "total_fv": df_fv["price_final1"].sum(),
            "total_daily": df_d["price_final1"].sum(),
            "total_daily_trav": df_d_trav["price_final1"].sum(),
            "total_daily_home": df_d_home["price_final1"].sum()
        }
        if return_df:
            d0 = pd.DataFrame([d0]).T.reset_index()
            d0.columns = ["label", "value"]

        def run(subdf):
            r = {}
            k = {}
            klist = []
            for kgr, kdf in subdf.groupby(["label_b", "label_c"]):
                k_label_b = kgr[0]
                k_label_c = kgr[1]

                if f"s_{k_label_b}" in r:
                    r[f"s_{k_label_b}"] += kdf["e"].iloc[0] * kdf["price_final"].sum()
                else:
                    r[f"s_{k_label_b}"] = kdf["e"].iloc[0] * kdf["price_final"].sum()

                kk = {
                    "label": k_label_b,
                    "transaction": k_label_c,
                    "value": kdf["price_final1"].sum()
                }
                klist.append(kk)

            return r, klist

        # receive summaries:
        r_fv, k_fv = run(df_fv)
        r_trav, k_trav = run(df_d_trav)
        r_trav_sum = sum([v for k, v in r_trav.items()])
        r_home, k_home = run(df_d_home)
        r_home_sum = sum([v for k, v in r_home.items()])

        # print(r_fv)
        # print(r_trav, r_trav_sum)
        # print(r_home, r_home_sum)

        d1 = []
        for k, v in r_fv.items():
            d1.append({"label": k[2:],
                       "value": v})

        d1.append({"label": "Daily Home",
                   "value": r_home_sum})
        d1.append({"label": "Daily Travel",
                   "value": r_trav_sum})

        # add the end of month sum:
        # suggested to be zero
        d1sum = sum([v["value"] for v in d1])
        d1.append({"label": "Savings (EoM)",
                   "value": d1sum})

        if return_df:
            d1 = pd.DataFrame(d1)
            d1.sort_values("value", inplace=True, ascending=False)
            d1.reset_index(inplace=True, drop=True)


            k_fv = pd.DataFrame(k_fv)
            k_home = pd.DataFrame(k_home)
            k_trav = pd.DataFrame(k_trav)

        return d0, d1, k_fv, k_home, k_trav