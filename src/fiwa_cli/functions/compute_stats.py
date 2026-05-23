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
        """Parse and normalize DataFrame columns for ExpenseTracker projects.
        
        Converts date, price, and exchange rate columns to proper types.
        Handles missing columns gracefully.
        """
        if self._project_style == "ExpenseTracker":
            try:
                # Parse dates and normalize to remove time component
                if 'bought_date' in self._items_df.columns:
                    self._items_df["bought_date"] = pd.to_datetime(
                        self._items_df["bought_date"], format='mixed'
                    ).dt.normalize()
                
                if 'exchange_rate_date' in self._items_df.columns:
                    self._items_df["exchange_rate_date"] = pd.to_datetime(
                        self._items_df["exchange_rate_date"], format='%Y-%m-%d'
                    )#.dt.normalize()
                
                # Parse numeric columns
                if 'price' in self._items_df.columns:
                    self._items_df["price"] = pd.to_numeric(self._items_df["price"], errors='coerce')
                
                if 'price_final' in self._items_df.columns:
                    self._items_df["price_final"] = pd.to_numeric(
                        self._items_df["price_final"], errors='coerce'
                    )

                if 'exchange_rate' in self._items_df.columns:
                    # Convert to numeric with robust handling for corrupted date values
                    # (handles legacy data where exchange_rate was mistakenly parsed as datetime)
                    self._items_df["exchange_rate"] = pd.to_numeric(
                        self._items_df["exchange_rate"], errors='coerce'
                    )

                # Sort by date if column exists
                if 'bought_date' in self._items_df.columns:
                    self._items_df.sort_values(by="bought_date", inplace=True)
                    
            except Exception as e:
                print(f"ERROR in op_parse_df: {e}")
                # Continue with unparsed data rather than failing

    def aggregate_daily_df(self):
        """Aggregate daily transactions by date and main label.

        Returns:
            list: List of dictionaries with daily aggregations, or empty list if no data
        """
        if len(self._items_df) == 0:
            return []

        # Check if required columns exist
        if 'label_t' not in self._items_df.columns:
            print("WARNING: label_t column missing in DataFrame")
            return []
        
        if 'label_m' not in self._items_df.columns:
            print("WARNING: label_m column missing in DataFrame")
            return []

        # get daily
        pdf = self._items_df[self._items_df["label_t"] == "daily"].copy()
        
        if len(pdf) == 0:
            return []
        
        # Convert to datetime first, then extract date only (strips timestamp to 00:00:00)
        pdf["bought_date"] = pd.to_datetime(pdf["bought_date"], format='mixed').dt.normalize()
        k = []
        for i, idf in pdf.groupby(pd.Grouper(key='bought_date', freq='D')):
            ik = {
                "date": i,
                "items": len(idf),
            }
            for j, jdf in idf.groupby(by="label_m"):
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
            tuple: A tuple of five elements containing aggregated financial data:
                (period_totals, account_summary, fixed_variable_details, 
                 home_daily_details, travel_daily_details)

                The type of each element depends on the `return_df` parameter:

                **When return_df=False (default):**

                - **period_totals** (dict): Overall period totals with keys:
                    - "total_fv" (float): Total for fixed/variable transactions
                    - "total_daily" (float): Total for all daily transactions
                    - "total_daily_trav" (float): Total for travel-related daily transactions
                    - "total_daily_home" (float): Total for home/non-travel daily transactions

                - **account_summary** (list[dict]): High-level summary by account, each dict contains:
                    - "label" (str): Account name or category
                    - "value" (float): Net amount for the category
                    Special entries: "Daily Home", "Daily Travel", "Savings (EoM)"

                - **fixed_variable_details** (list[dict]): Detailed fixed/variable transactions
                    Each dict contains: "label", "transaction", "value"

                - **home_daily_details** (list[dict]): Detailed daily home transactions
                    Each dict contains: "label", "transaction", "value"

                - **travel_daily_details** (list[dict]): Detailed daily travel transactions
                    Each dict contains: "label", "transaction", "value"

                **When return_df=True:**

                - **period_totals** (pd.DataFrame): Overall period totals with columns:
                    - `label` (str): Total category name
                    - `value` (float): Monetary value (expenses negative, revenue positive)

                - **account_summary** (pd.DataFrame): High-level summary by account with columns:
                    - `label` (str): Account name or category
                    - `value` (float): Net amount for the category
                    Sorted by value in descending order with "Savings (EoM)" at the bottom.

                - **fixed_variable_details** (pd.DataFrame): Detailed fixed/variable transactions with columns:
                    - `label` (str): Bank account name (`label_b`)
                    - `transaction` (str): Transaction type (`label_c`)
                    - `value` (float): Net transaction value

                - **home_daily_details** (pd.DataFrame): Detailed daily home transactions with columns:
                    - `label` (str): Bank account name (`label_b`)
                    - `transaction` (str): Transaction type (`label_c`)
                    - `value` (float): Net transaction value

                - **travel_daily_details** (pd.DataFrame): Detailed daily travel transactions with columns:
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
            >>> (period_totals, account_summary, fixed_variable_details,
            ...  home_daily_details, travel_daily_details) = stats.aggr_period()
            >>>
            >>> # View overall totals as dict
            >>> print(period_totals)
            {'total_fv': -1234.56, 'total_daily': -987.65, 
             'total_daily_trav': -234.00, 'total_daily_home': -753.65}
            >>>
            >>> # View account summary as list
            >>> print(account_summary)
            [{'label': 'CheckingAccount', 'value': -500.00},
             {'label': 'Daily Home', 'value': -753.65},
             {'label': 'Daily Travel', 'value': -234.00},
             {'label': 'Savings (EoM)', 'value': -1487.65}]

            **Using pandas DataFrames:**

            >>> (period_totals, account_summary, fixed_variable_details,
            ...  home_daily_details, travel_daily_details) = stats.aggr_period(return_df=True)
            >>>
            >>> # View overall totals as DataFrame
            >>> print(period_totals)
                         label      value
            0        total_fv  -1234.56
            1    total_daily   -987.65
            2  total_daily_trav -234.00
            3  total_daily_home -753.65
            >>>
            >>> # View account summary as DataFrame (sorted)
            >>> print(account_summary)
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
            - When `return_df=True`, account_summary is sorted by value in descending order
            - Use `return_df=False` for lightweight operations or JSON serialization
            - Use `return_df=True` for data analysis, visualization, or further pandas operations

        See Also:
            aggregate_daily_df: For daily transaction aggregation
            aggregate_fv_df: For fixed/variable transaction aggregation
            op_parse_df: For initial dataframe preparation
        """
        # Validate DataFrame exists and has data
        if self._items_df is None or len(self._items_df) == 0:
            # Return empty structures
            period_totals = {
                "total_fv": 0.0,
                "total_daily": 0.0,
                "total_daily_trav": 0.0,
                "total_daily_home": 0.0
            }
            account_summary = []
            fixed_variable_details = []
            home_daily_details = []
            travel_daily_details = []
            
            if return_df:
                period_totals = pd.DataFrame([period_totals]).T.reset_index()
                period_totals.columns = ["label", "value"]
                account_summary = pd.DataFrame(account_summary)
                fixed_variable_details = pd.DataFrame(fixed_variable_details)
                home_daily_details = pd.DataFrame(home_daily_details)
                travel_daily_details = pd.DataFrame(travel_daily_details)
            
            return period_totals, account_summary, fixed_variable_details, home_daily_details, travel_daily_details
        
        # Validate required columns exist
        required_cols = ['label_c', 'label_t', 'label_b', 'label_s', 'price_final']
        missing = [col for col in required_cols if col not in self._items_df.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns for aggregation: {missing}. Available columns: {self._items_df.columns.tolist()}")
        
        df = self._items_df.copy()

        for k, krow in df.iterrows():
            if krow["label_c"] == "expenses":
                c_multiplier = -1
            else:
                c_multiplier = 1
            df.at[k, "e"] = c_multiplier

        df["price_final1"] = df["e"] * df["price_final"]

        # Helper function to check if label_s contains 'travel' (case-insensitive)
        def contains_travel(label_s_value):
            """Check if label_s contains 'travel' keyword (handles list or string)."""
            if isinstance(label_s_value, list):
                # Check if any item in the list contains 'travel'
                return any('travel' in str(item).lower() for item in label_s_value)
            elif isinstance(label_s_value, str):
                # Check if string contains 'travel'
                return 'travel' in label_s_value.lower()
            else:
                # Default: no travel
                return False

        # Helper function to safely sum a column from a DataFrame (handles empty frames)
        def safe_sum(subdf, col_name):
            """Sum a column safely, handling empty DataFrames with no columns."""
            if subdf.empty or col_name not in subdf.columns:
                return 0.0
            return subdf[col_name].sum()

        # Split transactions by type
        df_fv = df[(df["label_t"] == "fixed") | (df["label_t"] == "variable")].copy()

        df_d = df[df["label_t"] == "daily"].copy()
        df_d_trav = df_d[df_d["label_s"].apply(contains_travel)].copy()
        df_d_home = df_d[df_d["label_s"].apply(lambda x: not contains_travel(x))].copy()

        # build a dataframe with all the totals:
        period_totals = {
            "total_fv": safe_sum(df_fv, "price_final1"),
            "total_daily": safe_sum(df_d, "price_final1"),
            "total_daily_trav": safe_sum(df_d_trav, "price_final1"),
            "total_daily_home": safe_sum(df_d_home, "price_final1")
        }
        if return_df:
            period_totals = pd.DataFrame([period_totals]).T.reset_index()
            period_totals.columns = ["label", "value"]

        def run(subdf):
            """Process a subset of transactions grouped by account and type.
            
            Returns empty dicts/lists if DataFrame is empty to handle edge cases
            where filters produce empty results with no columns.
            """
            r = {}
            klist = []
            
            # Handle empty DataFrames (no rows or no columns)
            if subdf.empty or len(subdf.columns) == 0:
                return r, klist
            
            for kgr, kdf in subdf.groupby(by=["label_b", "label_c"]):
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
        r_fv, fixed_variable_details = run(df_fv)
        r_trav, travel_daily_details = run(df_d_trav)
        r_trav_sum = sum([v for k, v in r_trav.items()])
        r_home, home_daily_details = run(df_d_home)
        r_home_sum = sum([v for k, v in r_home.items()])

        # print(r_fv)
        # print(r_trav, r_trav_sum)
        # print(r_home, r_home_sum)

        account_summary = []
        for k, v in r_fv.items():
            account_summary.append({"label": k[2:],
                       "value": v})

        account_summary.append({"label": "Daily Home",
                   "value": r_home_sum})
        account_summary.append({"label": "Daily Travel",
                   "value": r_trav_sum})

        # add the end of month sum:
        # suggested to be zero
        d1sum = sum([v["value"] for v in account_summary])
        account_summary.append({"label": "Savings (EoM)",
                   "value": d1sum})

        if return_df:
            account_summary = pd.DataFrame(account_summary)
            account_summary.sort_values("value", inplace=True, ascending=False)
            account_summary.reset_index(inplace=True, drop=True)


            fixed_variable_details = pd.DataFrame(fixed_variable_details)
            home_daily_details = pd.DataFrame(home_daily_details)
            travel_daily_details = pd.DataFrame(travel_daily_details)

        return period_totals, account_summary, fixed_variable_details, home_daily_details, travel_daily_details
