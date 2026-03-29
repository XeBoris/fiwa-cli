Inputs Module
=============

Expense and transaction input interfaces for FiWa CLI.

Overview
--------

The inputs module provides all interfaces for creating, editing, and managing
expense transactions. It features a centralized screen with sidebar navigation
and multiple specialized forms for different expense operations.

Module Structure
----------------

The inputs system consists of:

* **inputs.py**: Main inputs screen with sidebar navigation
* **inputs_insert_expense.py**: New expense creation wrapper
* **inputs_edit_expense.py**: Expense editing with tabbed DataTables
* **inputs_repl_expenses.py**: Recurring expense replication tool

Main Inputs Screen
------------------

.. automodule:: fiwa_cli.screens.inputs
   :members:
   :undoc-members:
   :show-inheritance:

The main inputs screen provides:

* **Sidebar navigation** with quick action buttons
* **Period selection** via WeekMonthWidget
* **Dynamic content area** for different forms
* **Consistent UX** matching Settings and Reports patterns

Keyboard Shortcut
~~~~~~~~~~~~~~~~~

Press **E** from any screen to open inputs/expenses.

Quick Actions
~~~~~~~~~~~~~

**New**:
    - Opens CreateExpenseForm
    - Launches ItemInputForm modal immediately
    - For adding single new expenses

**Edit**:
    - Opens EditExpenseView
    - Shows tabbed interface with all expenses
    - For viewing and modifying existing expenses

**Replicate**:
    - Opens ReplicateExpensesView
    - For projecting fixed expenses to next month
    - Batch creation of recurring items

Expense Creation
----------------

.. automodule:: fiwa_cli.screens.inputs_insert_expense
   :members:
   :undoc-members:
   :show-inheritance:

Create new expenses with:

* Automatic modal opening on mount
* Full expense details (name, price, date)
* Label/category selection
* Cost sharing between users
* Exchange rate handling
* Validation and confirmation

Creation Workflow
~~~~~~~~~~~~~~~~~

1. User clicks "New" in sidebar
2. CreateExpenseForm mounted
3. ItemInputForm modal opens automatically
4. User fills expense details:
   - Name (required)
   - Price and currency (required)
   - Purchase date (defaults to today)
   - Bought by (defaults to current user)
   - Bought for (defaults to current user, can split costs)
5. User selects labels:
   - Main category (or uses default)
   - Account/bank (or uses default)
   - Secondary tags (optional)
6. User clicks Save
7. Confirmation modal shows all details
8. User confirms
9. Expense written to database
10. ExpenseCreated message posted
11. Edit view refreshes to show new item

Expense Editing
---------------

.. automodule:: fiwa_cli.screens.inputs_edit_expense
   :members:
   :undoc-members:
   :show-inheritance:

Edit existing expenses with:

* Period-filtered display
* Tabbed interface per user
* Sortable DataTables
* Row-click editing
* Real-time refresh

Editing Workflow
~~~~~~~~~~~~~~~~

1. User clicks "Edit" in sidebar
2. EditExpenseView mounted
3. Tabs created for each project user
4. DataTables populated with period expenses
5. User selects their tab
6. User clicks expense row
7. ItemInputForm modal opens in edit mode
8. Form pre-filled with expense data
9. User modifies fields
10. User saves
11. Database updated
12. Table refreshes with new data

Expense Replication
-------------------

.. automodule:: fiwa_cli.screens.inputs_repl_expenses
   :members:
   :undoc-members:
   :show-inheritance:

Replicate recurring expenses:

* Fixed expense identification
* Date projection to next month
* Batch creation workflow
* Duplicate prevention
* Preview before write

Replication Workflow
~~~~~~~~~~~~~~~~~~~~

1. User selects current month in period picker
2. User clicks "Replicate" in sidebar
3. ReplicateExpensesView mounted
4. Tabs show users' fixed expenses
5. User selects their tab
6. Table shows fixed items (rent, subscriptions, etc.)
7. User selects expenses to replicate (all selected by default)
8. User clicks "Update to Next Month"
9. Dates projected forward by one month
10. Preview shown with highlighting
11. User clicks "Write to Database"
12. New expenses created for next month
13. Success notification with count

Period Integration
------------------

Period Selection
~~~~~~~~~~~~~~~~

The WeekMonthWidget in the InputsScreen sidebar controls:

* **Week view**: ISO week numbers (1-52/53)
* **Month view**: Custom boundaries based on month_start
* **Navigation**: Previous/next period buttons
* **Dropdown**: Select specific week/month

Period Effects
~~~~~~~~~~~~~~

**EditExpenseView**:
    - Filtered by selected period
    - Auto-refreshes on period change
    - Shows only expenses in date range

**CreateExpenseForm**:
    - NOT affected by period
    - Can create expenses for any date
    - Defaults to current date

**ReplicateExpensesView**:
    - Requires month mode
    - Shows fixed expenses from selected month
    - Projects to next calendar month

Data Flow
---------

Period Change → Edit View Refresh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User changes period in WeekMonthWidget
2. Widget posts PeriodChanged message
3. InputsScreen receives message
4. InputsScreen updates app_state
5. InputsScreen calls EditExpenseView.refresh_tables()
6. EditExpenseView queries database with new period
7. All user tabs reload with filtered data

Expense Creation → Display Update
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User creates expense in ItemInputForm
2. ItemInputForm validates and saves to database
3. ItemInputForm closes with result
4. CreateExpenseForm receives result
5. CreateExpenseForm posts ExpenseCreated message
6. InputsScreen receives message
7. InputsScreen refreshes EditExpenseView
8. New expense appears in table

Expense Edit → Table Refresh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User clicks expense row in EditExpenseView
2. ItemInputForm modal opens in edit mode
3. User modifies and saves
4. Database updated
5. Modal closes
6. EditExpenseView.refresh_tables() called
7. Table reloads with updated data

Common Workflows
----------------

Add Single Expense
~~~~~~~~~~~~~~~~~~

1. Press **E** to open Inputs
2. Click **New** button
3. Fill expense details:
   - Name: "Groceries"
   - Price: 85.00
   - Currency: USD
   - Date: today (default)
4. Select labels (or use defaults)
5. Click **Save**
6. Review confirmation
7. Click **Confirm**
8. Expense created

Edit Recent Expense
~~~~~~~~~~~~~~~~~~~

1. Press **E** to open Inputs
2. Click **Edit** button (default view)
3. Select your tab
4. Find expense in table
5. Click row to edit
6. Modify fields
7. Click **Save**
8. Confirm changes
9. Table updates

Share Expense Cost
~~~~~~~~~~~~~~~~~~

1. Create new expense (New button)
2. Fill basic details
3. In "Bought For" section:
   - Adjust percentage sliders
   - Example: Self 50%, Superman 50%
4. Save and confirm
5. Each user sees their share in their tab

Replicate Monthly Fixed Costs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Select current month in period picker
2. Click **Replicate** button
3. Select your tab
4. Review fixed expenses (rent, subscriptions)
5. Select items to replicate (default: all)
6. Click **Update to Next Month**
7. Review preview with new dates
8. Click **Write to Database**
9. Next month's expenses created

Filter by Period
~~~~~~~~~~~~~~~~

1. In Edit view
2. Click WeekMonthWidget in sidebar
3. Select **Week** or **Month**
4. Navigate to desired period
5. Table refreshes with filtered data
6. Only expenses in period shown

Sort Expenses
~~~~~~~~~~~~~

1. In Edit view
2. Select user tab
3. Click column header (e.g., "Date")
4. Table sorts by that column
5. Click again to reverse order
6. Click different column to sort by that

Best Practices
--------------

Expense Entry
~~~~~~~~~~~~~

* Fill all required fields (name, price, currency)
* Use descriptive names for easy identification
* Select appropriate labels/categories
* Set correct purchase date (not today if bought earlier)
* Use cost sharing for shared expenses
* Double-check currency before saving

Label Selection
~~~~~~~~~~~~~~~

* Use default labels when appropriate (saves time)
* Select specific account for tracking
* Add secondary labels for detailed categorization
* Main category is most important for reporting

Cost Sharing
~~~~~~~~~~~~

* Ensure percentages total 100%
* Use liability accounts for shared costs
* Document shared expenses in notes
* Check repayments regularly in Reports

Period Management
~~~~~~~~~~~~~~~~~

* Use weekly view for recent activity
* Use monthly view for budget review
* Match period to your accounting cycle
* Filter before editing to find items quickly

Replication Guidelines
~~~~~~~~~~~~~~~~~~~~~~

* Only replicate truly fixed expenses
* Review dates before writing to database
* Check for duplicates (tool prevents this)
* Update amounts if they changed
* Don't replicate variable or daily expenses

Troubleshooting
---------------

Expense Not Appearing in Edit View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Check period selection includes expense date
* Verify expense exists in database
* Check bought_for_id matches your user_id
* Try "All time" period to find it

Cannot Edit Expense
~~~~~~~~~~~~~~~~~~~

* User must have Update permission (xx1xxx)
* Expense must belong to current project
* Check database connection
* Review logs for errors

Replication Shows No Items
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Ensure month mode selected (not week)
* Verify fixed expenses exist in selected month
* Check transactions have correct label sub_type (0 = fixed)
* Try different month

Duplicates Created
~~~~~~~~~~~~~~~~~~

* Tool checks for duplicates automatically
* If bypassed, check database manually
* Use unique names for easy duplicate detection
* Review logs for warnings

Percentages Don't Total 100%
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* System validates before allowing save
* Check all user percentages
* Ensure no negative values
* Modal shows warning if invalid

See Also
--------

* :doc:`../quickstart`: Getting started with expenses
* :doc:`components`: ItemInputForm documentation
* :doc:`reports`: Viewing expense reports
* :doc:`settings`: Label management
