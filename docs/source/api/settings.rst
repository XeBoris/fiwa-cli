Settings Module
===============

Configuration and management interfaces for FiWa CLI.

Overview
--------

The settings module provides comprehensive interfaces for managing all
aspects of the FiWa CLI application, including projects, users, and labels.

Module Structure
----------------

The settings system consists of:

* **settings.py**: Main settings screen with sidebar navigation
* **settings_project_new.py**: Project creation form
* **settings_project_modify.py**: Project modification interface
* **settings_label_new.py**: Label creation form
* **settings_label_page.py**: Label management interface
* **settings_user_new.py**: User creation form
* **settings_user_modify.py**: User modification interface

Main Settings Screen
--------------------

.. automodule:: fiwa_cli.screens.settings
   :members:
   :undoc-members:
   :show-inheritance:

The main settings screen provides a two-column layout:

* **Left sidebar**: Menu with category sections
* **Right content area**: Dynamic form displays

Keyboard Shortcut
~~~~~~~~~~~~~~~~~

Press **S** from any screen to open settings.

Project Management
------------------

Project Creation
~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_project_new
   :members:
   :undoc-members:
   :show-inheritance:

Create new projects with:

* Custom names and descriptions
* Currency configuration (main + additional)
* Project style selection (ExpenseTracker, Vacation)
* Month start day for period calculations

Project Modification
~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_project_modify
   :members:
   :undoc-members:
   :show-inheritance:

Modify existing projects:

* Update project details
* Manage project users
* Adjust user permissions
* Add new users to project
* Configure month boundaries

Label Management
----------------

Label Creation
~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_label_new
   :members:
   :undoc-members:
   :show-inheritance:

Create new labels/categories:

* User-owned or common (project-wide) labels
* Multiple label types based on project style
* Status management (draft, active, archived)
* Default label designation

Label Management
~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_label_page
   :members:
   :undoc-members:
   :show-inheritance:

Manage existing labels:

* View all labels in interactive table
* Edit label details via modal
* Change label status
* Set default labels per category per user
* Permission-based access control

User Management
---------------

User Creation
~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_user_new
   :members:
   :undoc-members:
   :show-inheritance:

Create new user accounts:

* Personal information (name, email, birthday)
* Secure password hashing
* Project limit configuration
* Automatic unique identifier generation

User Modification
~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.settings_user_modify
   :members:
   :undoc-members:
   :show-inheritance:

Modify existing users with role-based access:

* **Admin users**: Can modify all users
* **Regular users**: Can only modify own information
* Field-level restrictions
* Password update modal
* Birthday management (admin only)

Password Update
~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.password_update_modal
   :members:
   :undoc-members:
   :show-inheritance:

Secure password updates:

* Three-field validation (current, new, confirm)
* Current password verification via bcrypt
* Minimum 6 character requirement
* Password confirmation to prevent typos
* Masked input fields (password=True)
* No plain text password storage
* Returns boolean result (success/cancel)

Permission System
-----------------

Project Permissions
~~~~~~~~~~~~~~~~~~~

User permissions are stored as 6-character binary strings:

.. code-block:: text

    Position 0: Read   - View expenses and dashboard
    Position 1: Create - Add new expenses
    Position 2: Update - Edit existing expenses
    Position 3: Delete - Remove expenses
    Position 4: Project - Edit project details
    Position 5: Manage - Manage users and permissions

Examples:

* ``100000`` = Read only
* ``110000`` = Read + Create
* ``111100`` = Read + Create + Update + Delete
* ``111111`` = Full permissions

User Scopes
~~~~~~~~~~~

User scopes control application-wide access:

* **admin:full** - Full administrator access
* **admin:read** - Read-only administrator
* **user:write** - Standard user (default)
* **user:read** - Read-only user

Common Workflows
----------------

Create a Project
~~~~~~~~~~~~~~~~

1. Press **S** to open Settings
2. Click **+ Create Project**
3. Fill in project details:
   - Name (required)
   - Description (optional)
   - Main currency (required, 3 letters)
   - Additional currencies (optional)
   - Project style (ExpenseTracker/Vacation)
   - Month start day (1-28)
4. Click **Create**
5. Project created with default structure via ProjectComposer

Modify Project Settings
~~~~~~~~~~~~~~~~~~~~~~~

1. Press **S** to open Settings
2. Click **= Modify Project**
3. Edit desired fields:
   - Project name
   - Description
   - Currencies
   - Month start day
4. Click **Update**
5. Changes take effect immediately (no re-login required)

Manage Project Users
~~~~~~~~~~~~~~~~~~~~

1. Press **S** → **= Modify Project**
2. Scroll to "Project Users" table
3. Click permission button next to user
4. Select new permission level
5. Click **OK**
6. Or click **Add Users** to add new members

Create Labels
~~~~~~~~~~~~~

1. Press **S** → **+ Create Label**
2. Fill in label details:
   - Name (required)
   - Type (from dropdown based on project style)
   - Owner (user or common)
   - Status (draft/active/archived)
   - Default checkbox
3. Click **Create**

Manage Labels
~~~~~~~~~~~~~

1. Press **S** → **= Manage Labels**
2. View all labels in table
3. Click row to edit label
4. Or click star to set as default
5. Changes save immediately

Create User
~~~~~~~~~~~

1. Press **S** → **+ Create User** (admin only)
2. Fill in user details:
   - First name, last name (required)
   - Username (required, unique)
   - Email (required)
   - Birthday (optional)
   - Password (required, min 6 chars)
   - Max projects (default: 3)
3. Click **Create**

Modify User
~~~~~~~~~~~

Admin users:

1. Press **S** → **= Modify User**
2. Select user from dropdown
3. Edit fields
4. Click **Update**

Regular users:

1. Press **S** → **= Modify User**
2. Own data loads automatically
3. Edit allowed fields
4. Click **Update**

Update Password
~~~~~~~~~~~~~~~

Secure password change process:

1. Press **S** → **= Modify User**
2. Click **Update Password** button
3. PasswordUpdateModal opens
4. Enter **current password** (for verification)
5. Enter **new password** (min 6 chars, masked)
6. **Confirm** new password (must match)
7. Click **✓ Update Password**
8. System verifies current password
9. System hashes new password with bcrypt
10. Database updated
11. Success notification shown
12. Modal closes

Security Notes:
    * All password fields are masked (shown as bullets)
    * Current password verified before allowing change
    * Passwords hashed with bcrypt (never stored as plain text)
    * Modal stays open on validation failure (allows retry)
    * Escape key to cancel without changes

Common Errors:
    * "New passwords do not match!" - Retype confirm field
    * "Current password is incorrect" - Verify your current password
    * "Must be at least 6 characters long" - Use stronger password

Best Practices
--------------

Project Setup
~~~~~~~~~~~~~

* Use descriptive project names (max 24 characters)
* Set appropriate month start day for your accounting period
* Add all currencies you'll use to avoid manual entry later
* Choose correct project style (affects available labels)

Label Organization
~~~~~~~~~~~~~~~~~~

* Create common labels for shared categories
* Use user-owned labels for personal accounts
* Set one default per category per user
* Mark labels as archived instead of deleting

User Management
~~~~~~~~~~~~~~~

* Use strong passwords (min 6 characters)
* Assign appropriate scopes (don't give admin unnecessarily)
* Set realistic project limits per user
* Review permissions regularly

Permission Assignment
~~~~~~~~~~~~~~~~~~~~~

* Start with Read-only for new project members
* Grant Create permission for expense entry
* Reserve Manage permission for trusted users
* Use Project permission carefully (can modify settings)

Troubleshooting
---------------

Cannot Create Project
~~~~~~~~~~~~~~~~~~~~~

* Check if project limit reached (shown in form)
* Verify all required fields are filled
* Ensure main currency is exactly 3 letters
* Check month_start is between 1-28

Cannot Modify Project
~~~~~~~~~~~~~~~~~~~~~

* User must have "Project" permission (position 4)
* Or "Manage" permission (position 5)
* Verify project is loaded in app_state

Cannot Set Default Label
~~~~~~~~~~~~~~~~~~~~~~~~

* User must have "Manage" permission
* Only one default per label type per user
* Label must be active (status = 2)

User Not in Dropdown
~~~~~~~~~~~~~~~~~~~~

* Only admins see user dropdown
* Regular users only see own data
* Check user scope starts with "admin:"

Password Update Fails
~~~~~~~~~~~~~~~~~~~~~~

* Verify current password is correct
* Ensure new password is at least 6 characters
* Check new password matches confirm field
* Try typing passwords in text editor first (avoid typos)
* Ensure database connection available
* Check logs for detailed error messages

Password Requirements:
    * Minimum length: 6 characters
    * Must match confirmation
    * Current password must be verified
    * Cannot be empty

See Also
--------

* :doc:`../quickstart`: Getting started guide
* :doc:`main`: Main application documentation
* :doc:`../api/database`: Database schema and operations
