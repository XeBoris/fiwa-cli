Reports Module
==============

Financial reporting and analytics interfaces for FiWa CLI.

Overview
--------

The reports module provides comprehensive financial reporting capabilities
with period-based filtering, multi-user views, and detailed transaction
breakdowns. Reports help users understand spending patterns, track budgets,
and manage inter-user financial relationships.

Module Structure
----------------

The reports system consists of:

* **reports.py**: Main reports screen with sidebar navigation and period selection
* **reports_basic.py**: Cost Overview report with detailed per-user breakdowns

Main Reports Screen
-------------------

.. automodule:: fiwa_cli.screens.reports
   :members:
   :undoc-members:
   :show-inheritance:

The main reports screen provides:

* **Sidebar navigation** with WeekMonthWidget for period selection
* **Dynamic content area** displaying different report types
* **Real-time period updates** affecting all active reports
* **Consistent UX** matching the settings screen layout

Keyboard Shortcut
~~~~~~~~~~~~~~~~~

Press **R** from any screen to open reports.

Period Selection
~~~~~~~~~~~~~~~~

The WeekMonthWidget in the sidebar allows:

* **Week view**: ISO week numbers (1-52/53)
* **Month view**: Custom month boundaries based on project month_start
* **Navigation**: Previous/next period buttons
* **Reset**: Jump to current week/month
* **Dropdown**: Select specific week/month

Period Boundaries
~~~~~~~~~~~~~~~~~

**Weekly Periods**:
    - Follow ISO 8601 standard
    - Week starts Monday (or Sunday, configurable)
    - Numbered 1-52 (or 53 in long years)

**Monthly Periods**:
    - Respect project's month_start setting
    - Example: month_start=15
      - March: 2026-03-15 to 2026-04-14
      - April: 2026-04-15 to 2026-05-14
    - Example: month_start=1
      - March: 2026-03-01 to 2026-03-31 (standard calendar)

Cost Overview Report
--------------------

.. automodule:: fiwa_cli.screens.reports_basic
   :members:
   :undoc-members:
   :show-inheritance:

The Cost Overview report provides detailed expense analysis:

Per-User Tabs
~~~~~~~~~~~~~

Each project user gets a dedicated tab showing their transactions:

**Fixed & Variable Transactions Table**:
    - Recurring expenses (rent, subscriptions, insurance)
    - Revenue items (salary, income, gifts received)
    - Sorted by date (newest first)
    - Auto-sized height based on row count

**Daily Transactions Table**:
    - Frequent small expenses (groceries, coffee, transport)
    - Sorted by date
    - Separate table for easy visual distinction

**Summary Section**:
    - Total Revenue (green, sum of income)
    - Total Expenses (red, sum of costs)
    - Balance (Revenue - Expenses, colored by sign)
    - Repay button (debt calculation)

Report Features
~~~~~~~~~~~~~~~

**Sortable Tables**:
    - Click column headers to sort
    - Toggle ascending/descending
    - Default: Date descending

**Label Integration**:
    - Shows main category label per transaction
    - Uses ProjectComposer for label mapping
    - Displays label names, not just IDs

**Exchange Rates**:
    - All amounts shown in original currency
    - Final amounts converted to project's main currency
    - Exchange rate displayed per transaction

**Bought By Tracking**:
    - Shows who purchased each item
    - Essential for understanding cost sharing
    - Used in repayment calculations

Repayment Feature
-----------------

Modal Dialog
~~~~~~~~~~~~

.. autoclass:: fiwa_cli.screens.reports_basic.RepayModal
   :members:
   :undoc-members:
   :show-inheritance:

The Repay button opens a modal showing who owes whom:

Calculation Logic
~~~~~~~~~~~~~~~~~

1. Analyze all transactions in current period
2. For each transaction where bought_by ≠ bought_for:
   - Creditor = person who bought (bought_by_id)
   - Debtor = person it was bought for (bought_for_id)
   - Amount = final_price (in main currency)
3. Aggregate by (debtor, creditor) pairs
4. Calculate net amounts (A→B minus B→A)
5. Display only non-zero net debts

Example Output
~~~~~~~~~~~~~~

::

    ☛ Repay Overview
    𝌌 Period: 2026-03-15 to 2026-04-14

    Who owes whom:
    💰 Superman owes Batman: 125.50 USD
    💰 Wonderwoman owes Batman: 45.00 USD

    [OK]

Or if balanced::

    ✅ All settled! No repayments needed.

Transaction Classification
--------------------------

Transactions are classified by label sub_type:

Fixed Transactions
~~~~~~~~~~~~~~~~~~

**Label**: type=1, sub_type=0

**Examples**:
    - Rent
    - Mortgage
    - Subscriptions (Netflix, Spotify)
    - Insurance premiums
    - Loan payments

**Characteristics**:
    - Regular, predictable amounts
    - Same or similar amount each period
    - Essential, non-discretionary

Variable Transactions
~~~~~~~~~~~~~~~~~~~~~

**Label**: type=1, sub_type=1

**Examples**:
    - Utilities (electricity, water, gas)
    - Phone bills
    - Internet service
    - Maintenance costs
    - Medical expenses

**Characteristics**:
    - Recurring but amount varies
    - Essential services
    - Some predictability

Daily Transactions
~~~~~~~~~~~~~~~~~~

**Label**: type=1, sub_type=2

**Examples**:
    - Groceries
    - Coffee/dining
    - Transport/fuel
    - Entertainment
    - Personal supplies

**Characteristics**:
    - Frequent, small amounts
    - High volume of transactions
    - Discretionary or semi-discretionary

Revenue Transactions
~~~~~~~~~~~~~~~~~~~~

**Label**: type=1, sub_type≥3

**Examples**:
    - Salary/wages
    - Freelance income
    - Investment returns
    - Gifts received
    - Refunds

**Characteristics**:
    - Positive multiplier (+1)
    - Increases balance
    - Shown in Fixed & Variable table

Data Flow
---------

Period Selection → Data Refresh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User changes period in WeekMonthWidget
2. Widget posts PeriodChanged message
3. ReportsScreen receives message
4. ReportsScreen updates app_state with new period_start/period_end
5. ReportsScreen calls BasicReportForm.refresh_data()
6. BasicReportForm queries database with new period
7. All tables update with new data
8. Totals recalculated and displayed

Database Query → Display
~~~~~~~~~~~~~~~~~~~~~~~~

1. BasicReportForm calls _get_user_items(user_id, project_id)
2. Query filters by:
   - bought_for_id = user_id
   - project_id = current project
   - bought_date >= period_start AND < period_end
3. Results include label details via tag parsing
4. Items classified by label sub_type
5. Fixed/Variable items → Table 1
6. Daily items → Table 2
7. Tables sorted by date descending
8. Totals calculated using multiplier

Common Workflows
----------------

View Current Week Expenses
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Press **R** to open Reports
2. Default: Current week automatically selected
3. View Cost Overview (default report)
4. Click user tabs to see individual breakdowns
5. Review totals at bottom of each tab

Change to Monthly View
~~~~~~~~~~~~~~~~~~~~~~~

1. In reports sidebar, click WeekMonthWidget
2. Select "Month" from dropdown
3. Select desired month (e.g., "March")
4. Report automatically refreshes with monthly data
5. Totals show entire month (based on month_start setting)

Check Who Owes Money
~~~~~~~~~~~~~~~~~~~~

1. Open Cost Overview report
2. Select appropriate period (week/month)
3. Click "Repay" button under totals
4. Modal shows all outstanding debts
5. Example: "Superman owes Batman: 50.00 USD"
6. Click OK to close

Compare User Spending
~~~~~~~~~~~~~~~~~~~~~

1. Open Cost Overview
2. Click through user tabs
3. Compare totals:
   - Batman: Revenue $5000, Expenses $1500, Balance +$3500
   - Superman: Revenue $4500, Expenses $2000, Balance +$2500
4. Identify high spenders or unusual patterns

Sort by Transaction Type
~~~~~~~~~~~~~~~~~~~~~~~~

1. Navigate to user's tab
2. Click "Name" column header
3. Transactions sort alphabetically
4. Click again to reverse order
5. Click "Date" to sort by date
6. Click "Final" to sort by amount

Best Practices
--------------

Period Selection
~~~~~~~~~~~~~~~~

* Use weekly view for detailed recent activity
* Use monthly view for budget tracking
* Respect month_start setting for accounting consistency
* Reset to current period before analyzing "latest" data

Data Interpretation
~~~~~~~~~~~~~~~~~~~

* Balance = Revenue - Expenses (can be negative)
* Fixed expenses should be relatively constant month-to-month
* Daily expenses show spending habits
* Compare across users to identify cost-sharing opportunities

Repayment Management
~~~~~~~~~~~~~~~~~~~~

* Check repayments at end of each period
* Settle debts before starting new period
* Use repay feature to avoid disputes
* Document settlements in notes

Performance Tips
~~~~~~~~~~~~~~~~

* Limit period to current week/month for faster loading
* Avoid querying entire year at once
* Use archived labels to hide old categories
* Vacuum database periodically if slow

Troubleshooting
---------------

No Data Showing
~~~~~~~~~~~~~~~

* Check period selection includes transaction dates
* Verify user has Read permission (100000+)
* Ensure transactions exist in database
* Check bought_for_id matches user in tab

Repay Shows Unexpected Debts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Review bought_by vs. bought_for in transactions
* Check exchange rates are applied correctly
* Verify transactions in selected period only
* Look for duplicated entries

Tables Not Sorting
~~~~~~~~~~~~~~~~~~

* Ensure clicking column header, not cell
* Check table has data (empty tables don't sort visibly)
* Try different columns (some may have same values)

Totals Don't Match
~~~~~~~~~~~~~~~~~~

* Verify all transactions have labels assigned
* Check multiplier logic (revenue=+1, expense=-1)
* Ensure exchange rates calculated correctly
* Review label sub_type assignments

See Also
--------

* :doc:`../quickstart`: Getting started with reports
* :doc:`settings`: Settings module for project configuration
* :doc:`main`: Main application documentation
* :doc:`../api/components`: WeekMonthWidget documentation
