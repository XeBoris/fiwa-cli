# FiWa CLI - Financial Tracking Application

**FiWa** (Financial Wallet) is a terminal-based financial tracking application built with [Textual](https://textual.textualize.io/), providing a rich TUI (Text User Interface) for managing personal finances, projects, and transactions.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Guide](#user-guide)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Development](#development)
- [Project Structure](#project-structure)

---

## ✨ Features

### 🔐 User Management
- **Multi-user support** with secure password hashing (SHA-256)
- **Session management** with UUID-based tracking
- **User login/logout** with reactive state updates
- **User creation** with configurable project limits
- **Role-based permissions** (regular users and superusers)

### 📊 Project Management
- **Multiple projects per user** (configurable limit, default: 3)
- **Project creation** with name, description, and currency settings
- **Project modification** with real-time updates
- **Primary project selection** for active context
- **Multi-currency support** with main and additional currencies
- **Project switching** via integrated selector

### 🏷️ Label Management
- **Hierarchical labels** for categorizing transactions
- **Label types**: Action, Account, Label (3 levels)
- **Label status**: Active, Deactivated, Mark for Deletion
- **Batch operations** for efficient label management
- **Interactive editor** with click-to-edit functionality
- **Label creation** with validation and uniqueness checks

### 📅 Calendar Widget
- **Interactive date picker** with month navigation
- **Configurable week start** (Monday/Sunday)
- **Today highlighting** with quick jump
- **Keyboard shortcuts** (ESC to close)
- **Compact design** positioned near trigger button

### 🎨 User Interface
- **Reactive header** showing user, project, and date
- **Menu system** with contextual options
- **Settings panel** with sidebar navigation
- **Dark/Light theme** toggle (Ctrl+D)
- **Responsive layout** with grid-based components
- **Modal screens** for focused interactions

### 🔄 State Management
- **Reactive app_state** for real-time UI updates
- **Automatic screen refresh** on state changes
- **Session persistence** across app lifecycle
- **Clean logout** with complete state reset
- **Fallback to main screen** after logout

---

## 🏗️ Architecture

### Technology Stack

- **Framework**: [Textual](https://textual.textualize.io/) - Modern TUI framework
- **Language**: Python 3.12+
- **Database**: SQLite (local storage)
- **Password Hashing**: SHA-256 with salt
- **State Management**: Reactive variables with watchers

### Design Patterns

- **Screen-based navigation** with modal overlays
- **Message passing** for component communication
- **Reactive programming** for state synchronization
- **Database handler pattern** with `op_*` methods
- **Component-based architecture** with reusable widgets

### Key Components

```
FiWa CLI Application
│
├── Main App (main.py)
│   ├── Reactive app_state
│   ├── Watch callbacks
│   └── Screen stack management
│
├── Components (components/)
│   ├── FiwaHeader - Top navigation bar
│   └── CalendarWidget - Date picker modal
│
├── Screens (screens/)
│   ├── Base - Login/Logout functionality
│   ├── Menu - Navigation menu
│   ├── Settings - Configuration hub
│   ├── Project Selector - Switch projects
│   ├── Reports - (Placeholder)
│   ├── Dashboard - (Placeholder)
│   └── Inputs - (Placeholder)
│
├── Functions (functions/)
│   ├── handler_sqllite.py - Database operations
│   ├── loader.py - Configuration loading
│   └── db_faker.py - Test data generation
│
└── Database
    ├── Users
    ├── Projects
    ├── Labels
    ├── User-Project mapping
    └── Session tracking
```

---

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Terminal with Unicode support

### Install Dependencies

```bash
# Clone the repository
cd /home/koenig/Projects/00_fiwa_work/fiwa-cli

# Create virtual environment (optional but recommended)
conda create -n fiwa-cli python=3.12
conda activate fiwa-cli

# Install dependencies
pip install textual bcrypt pyyaml faker
```

### Database Setup

The application automatically initializes the SQLite database on first run using the schema defined in `schema.sql`.

---

## 🚀 Quick Start

### Run the Application

```bash
# From the project directory
python main.py
```

### First Time Setup

1. **Create a User** (if database is empty)
   - Navigate: Menu → Settings → + Create User
   - Fill in: First name, Last name, Username, Email, Password
   - Click "Create"

2. **Login**
   - Click: Menu → Login
   - Enter credentials
   - Click "Login"

3. **Create a Project**
   - Navigate: Settings → + Create Project
   - Fill in: Name, Description, Currencies
   - Click "Create"

4. **Create Labels**
   - Navigate: Settings → + Create Label
   - Fill in: Name, Description, Type, Status
   - Click "Create"

---

## 📖 User Guide

### Navigation

#### Header Bar
```
┌─────────────────────────────────────────────────┐
│ FiWa [☰ Menu] [📅 Calendar]  User | Project    │
└─────────────────────────────────────────────────┘
```

- **FiWa** - Application title
- **☰ Menu** - Opens main menu
- **📅 Calendar** - Opens date picker
- **User** - Current logged-in user
- **Project** - Active project

#### Main Menu

- **Inputs** - Add transactions (Coming soon)
- **Reports** - View financial reports (Coming soon)
- **Dashboard** - Overview (Coming soon)
- **Settings** - Configure application
- **Select Project** - Switch active project
- **Login/Logout** - Manage session
- **Exit** - Close application

### User Management

#### Creating a User

1. **Navigate to Settings** → + Create User
2. **Fill in the form**:
   - First Name (required)
   - Last Name (required)
   - Username (required)
   - Email (required, unique)
   - Password (required, will be hashed)
   - Birthday (optional)
   - Max Projects (default: 3)
3. **Click Create**
4. User is created and saved to database

#### Login/Logout

**Login:**
1. Click Menu → Login
2. Enter username/email and password
3. Click "Login"
4. Session starts, app_state updates with user data

**Logout:**
1. Click Menu → Logout
2. Confirm logout
3. Session ends, returns to main screen
4. All user data cleared from app_state

### Project Management

#### Creating a Project

1. **Settings** → + Create Project
2. **Check project limit** (displayed at top)
3. **Fill in**:
   - Name (required, max 24 chars)
   - Description (optional)
   - Main Currency (3-letter code, e.g., USD)
   - Additional Currencies (comma-separated)
4. **Click Create**
5. Project added to database and app_state

#### Modifying a Project

1. **Settings** → = Modify Project
2. **Current project shown** (selected from app_state)
3. **Edit fields**:
   - Name
   - Description
   - Main Currency
   - Additional Currencies
4. **Click Update**
5. Changes saved, app_state updated

#### Switching Projects

1. **Menu** → Select Project
2. **Choose from list** of your projects
3. **Project changes immediately**
4. Header updates to show new project

### Label Management

#### Creating Labels

1. **Settings** → + Create Label
2. **Fill in**:
   - Name (required)
   - Description (optional)
   - Action Type: Account / Action / Label
   - Status: Active / Inactive
3. **Click Create**
4. Label saved to database

#### Managing Labels

1. **Settings** → = Manage Labels
2. **View table** of all labels
3. **Click any row** to edit:
   - Edit name
   - Edit description
   - Change status (Active/Deactivated/Deleted)
4. **Click Save All Changes** to persist

**Label Status:**
- **Active (2)** - Label is in use
- **Deactivated (1)** - Label is hidden but preserved
- **Mark for Deletion (0)** - Flagged for removal

### Calendar Usage

1. **Click 📅 Calendar** in header
2. **Navigate**:
   - **◀** Previous month
   - **Today** Jump to current month
   - **▶** Next month
3. **Select date** by clicking any day
4. **ESC** to close without selecting

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE pstand_users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    birthday DATE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated BOOLEAN DEFAULT 1,
    is_superuser BOOLEAN DEFAULT 0,
    scope VARCHAR(255) DEFAULT 'user:write',
    max_projects INTEGER DEFAULT 3,
    unique_identifier VARCHAR(36) NOT NULL
);
```

### Projects Table
```sql
CREATE TABLE pstand_projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    currency_main VARCHAR(3),
    currency_list TEXT,
    project_hash VARCHAR(64) UNIQUE
);
```

### Labels Table
```sql
CREATE TABLE pstand_labels (
    label_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(36) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    project_id INTEGER NOT NULL,
    composite TEXT NOT NULL,
    label_status INTEGER DEFAULT 2,
    label_type INTEGER DEFAULT 1,
    FOREIGN KEY (project_id) REFERENCES pstand_projects(project_id),
    UNIQUE (name, project_id)
);
```

### User-Project Mapping
```sql
CREATE TABLE pstand_user_project_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    project_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_perm_model VARCHAR(6) DEFAULT '000000',
    project_primary BOOLEAN DEFAULT 0,
    excluded_tags TEXT,
    FOREIGN KEY (user_id) REFERENCES pstand_users(user_id),
    FOREIGN KEY (project_id) REFERENCES pstand_projects(project_id)
);
```

### Session Table
```sql
CREATE TABLE pstand_session_table (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_uuid VARCHAR(36) UNIQUE NOT NULL,
    session_type VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES pstand_users(user_id)
);
```

---

## ⚙️ Configuration

### config.yml

```yaml
database:
  path: "./fiwa_data.db"
  salt: "fiwa_default_salt_2026"
  partition: "stand"

app:
  mode: "terminal"  # or "web"
  theme: "textual-dark"

calendar:
  week_starts_monday: true
```

### Configuration Options

- **database.path** - SQLite database file location
- **database.salt** - Password hashing salt
- **database.partition** - Database table prefix
- **app.mode** - Terminal or web mode
- **app.theme** - UI theme (dark/light)
- **calendar.week_starts_monday** - Week start day

---

## 🛠️ Development

### Project Structure

```
fiwa-cli/
├── main.py                 # Application entry point
├── main.css                # Global styles
├── config.yml              # Configuration file
├── schema.sql              # Database schema
├── README.md               # This file
│
├── components/             # Reusable UI components
│   ├── __init__.py
│   ├── header.py          # FiwaHeader component
│   └── calendar_display.py # Calendar widget
│
├── screens/                # Application screens
│   ├── __init__.py
│   ├── base.py            # Base screen + Login/Logout
│   ├── menu.py            # Main menu
│   ├── settings.py        # Settings screen
│   ├── project_selector.py # Project selector
│   ├── settings_project_new.py
│   ├── settings_project_modify.py
│   ├── settings_user_new.py
│   ├── settings_label_new.py
│   ├── settings_label_page.py
│   ├── reports.py         # Reports screen
│   ├── dashboard.py       # Dashboard screen
│   └── inputs.py          # Inputs screen
│
└── functions/              # Business logic
    ├── __init__.py
    ├── handler_sqllite.py  # Database operations
    ├── loader.py           # Config loader
    └── db_faker.py         # Test data generator
```

### Database Handler Pattern

All database operations use the `op_*` naming convention:

```python
# User operations
op_user_create(user_dict)
op_user_login(username, password)
op_user_logout(session_uuid)
op_user_get_info(user_id)

# Project operations
op_project_create(project_dict, user_id)
op_project_update(project_dict)
op_project_get_info(user_id)
op_get_max_projects(user_id)

# Label operations
op_label_create(label_dict, project_id)
op_label_update(label_id, label_dict)
op_label_get_all(project_id)
op_label_delete(label_id, hard_delete)
```

### Generating Test Data

```python
from functions.db_faker import faker_users, faker_projects, faker_labels

# Create fake users
dbh = SQLLiteHandler(db_path="./test.db")
user_ids = faker_users(dbh, n=5)

# Create fake projects
project_ids = faker_projects(dbh)

# Create fake labels
faker_labels(dbh, project_ids)
```

### Key Bindings

- **Ctrl+C** - Quit application
- **D** - Toggle dark/light mode
- **ESC** - Close modals/dialogs
- **Tab** - Navigate between inputs
- **Enter** - Activate buttons

---

## 🔮 Roadmap

### Planned Features

- **Inputs Screen**
  - Add transactions (income/expenses)
  - Quick entry mode
  - Bulk import from CSV/Excel
  - Receipt attachment

- **Reports Screen**
  - Monthly summaries
  - Category breakdowns
  - Trend analysis
  - Export to PDF/Excel

- **Dashboard Screen**
  - Budget overview
  - Spending charts
  - Account balances
  - Savings goals

- **Items Table**
  - Transaction details
  - Label associations
  - Currency conversion
  - Exchange rate tracking

- **Advanced Features**
  - Multi-currency conversion
  - Recurring transactions
  - Budget alerts
  - Data export/import
  - API integration

---

## 📝 License

This project is part of a private financial tracking system.

---

## 👥 Contributors

- **Boris Bauermeister** - Lead Developer

---

## 🐛 Known Issues

- Calendar widget positioning may vary on different terminal sizes
- Label table scrolling requires keyboard navigation
- Some placeholder screens (Inputs, Reports, Dashboard) are not yet implemented

---

## 📞 Support

For issues, questions, or contributions, please contact the development team.

---

## 🎯 Getting Help

### Common Issues

**Q: Database not found**
- A: Run the app once to auto-create the database, or check `config.yml` path

**Q: Can't login**
- A: Ensure you created a user first (Settings → + Create User)

**Q: Project limit reached**
- A: Check user's `max_projects` setting in database

**Q: Labels not saving**
- A: Click "Save All Changes" button after editing labels

**Q: Screen not updating after login**
- A: This is a known issue; logout and login again

---

## 📚 Additional Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Python SQLite Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Rich Text Markup](https://rich.readthedocs.io/en/stable/markup.html)

---

**Version:** 0.1.0-alpha  
**Last Updated:** February 15, 2026  
**Status:** Active Development
