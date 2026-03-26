from abc import ABC, abstractmethod


class ProjectComposer(ABC):
    """
    Abstract base class for project composers.
    Each composer defines the structure and labels for a specific project type.
    """

    # Registry of available composers
    COMPOSERS = {
        "ExpenseTracker": "ProjectExpenseTracker",
        "Vacation": "ProjectVacation"
    }

    def __init__(self, dbh=None, project_id=None, users=[]):
        """
        Initialize the project composer.

        Args:
            dbh: Database handler instance
            project_id: ID of the project
            users: List of users in the project
        """
        self.dbh = dbh
        self.project_id = project_id
        self.users = users
        self.name = None  # To be set by subclass

    @classmethod
    def create(cls, compose_type, dbh=None, project_id=None, users=[]):
        """
        Factory method to create the appropriate composer instance.

        Args:
            compose_type: Type of composer to create (e.g., "ExpenseTracker", "Vacation")
            dbh: Database handler instance
            project_id: ID of the project
            users: List of users in the project

        Returns:
            Instance of the appropriate ProjectComposer subclass

        Raises:
            ValueError: If compose_type is not valid
        """
        if compose_type not in cls.COMPOSERS:
            raise ValueError(f"Invalid compose type: {compose_type}. Valid options are: {list(cls.COMPOSERS.keys())}")

        # Get the class name and instantiate
        if compose_type == "ExpenseTracker":
            return ProjectExpenseTracker(dbh=dbh, project_id=project_id, users=users)
        elif compose_type == "Vacation":
            return ProjectVacation(dbh=dbh, project_id=project_id, users=users)
        else:
            raise ValueError(f"Composer type {compose_type} not implemented")

    def build(self):
        """
        Build all components of the project by calling compose methods.
        This is the main entry point for setting up a project.
        """
        self.compose_labels()

    @abstractmethod
    def compose_labels(self):
        """
        Create action/category labels for the project.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def compose_accounts(self):
        """
        Create account-related labels for the project.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_label_map(self):
        """
        Return a dictionary mapping label type IDs to their group names.
        Must be implemented by subclasses.

        Returns:
            dict: Mapping of type_id (int) to group_name (str)
                  Example: {0: "Balance", 1: "Transaction", 2: "Account", 3: "Main Labels"}
        """
        pass

    def identify_action_cycle(self, label):
        """
        Identify the action cycle/frequency for a given label.
        Can be overridden by subclasses if needed.

        Args:
            label: Label name or ID

        Returns:
            Action cycle information
        """
        return None


class ProjectExpenseTracker(ProjectComposer):
    """
    Composer for expense tracking projects.
    Manages expenses, revenues, and categorizes them by frequency.
    """

    def __init__(self, dbh=None, project_id=None, users=[]):
        super().__init__(dbh=dbh, project_id=project_id, users=users)
        self.name = "ExpenseTracker"

        self.label_ = [
            {"type": 0, "sub_type": 0, "group": "Balance", "name": "expenses",
             "description": "Expenses label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 0, "sub_type": 1, "group": "Balance", "name": "revenue",
             "description": "Revenue label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 1, "sub_type": 0, "group": "Transaction", "name": "fixed",
             "description": "Fixed transaction label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 1, "sub_type": 1, "group": "Transaction", "name": "variable",
             "description": "Variable transaction label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 1, "sub_type": 2, "group": "Transaction", "name": "daily",
             "description": "Daily transaction label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 2, "sub_type": 0, "group": "Account", "name": "Liability Account",
             "description": "Liability account label", "composite": [],
             "label_owner": -2, "label_status": 2},
            {"type": 3, "sub_type": -1, "group": "Main Labels", "name": "Groceries",
             "description": "Groceries main label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 3, "sub_type": -1, "group": "Main Labels", "name": "Dinner",
             "description": "Dinner main label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 3, "sub_type": -1, "group": "Main Labels", "name": "Books",
             "description": "Books main label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 3, "sub_type": -1, "group": "Main Labels", "name": "Personal Supplies",
             "description": "Personal Supplies main label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 4, "sub_type": -1, "group": "Secondary Labels", "name": "work",
             "description": "Work secondary label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 4, "sub_type": -1, "group": "Secondary Labels", "name": "travel",
             "description": "Travel secondary label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 4, "sub_type": -1, "group": "Secondary Labels", "name": "going-out",
             "description": "Going out secondary label", "composite": [],
             "label_owner": -1, "label_status": 2},
            {"type": 4, "sub_type": -1, "group": "Secondary Labels", "name": "take-away",
             "description": "Take-away secondary label", "composite": [],
             "label_owner": -1, "label_status": 2},
        ]

    def get_label_map(self):
        ret = {}
        for i_group in self.label_:
            if i_group["type"] not in ret:
                ret[i_group["type"]] = i_group["group"]
        return ret

    def get(self):
        pass

    # def get_split(self, items=[], keys=[]):
    #
    #     bl = self.balance_labels["definition"]  # fetch definition
    #     tl = self.transaction_labels["definition"]  # fetch definition
    #     al = self.bank_labels["definition"]
    #     ml = self.labels_main["definition"]
    #     sl = self.labels_secondary["definition"]


    def get_transaction_split(self, items=[], keys=[]):
        """
        Filter items by transaction type (fixed, variable, daily).
        Uses self.label_ to identify transaction type labels.

        Args:
            items: List of items with parsed_tags
            keys: List of transaction types to include (e.g., ["fixed", "variable"])

        Returns:
            Filtered list of items matching the specified transaction types
        """
        # Build transaction label name map from self.label_
        # Transaction labels have type=1
        transaction_map = {}
        for i_entry in self.label_:
            if i_entry["type"] == 1:  # Transaction type
                transaction_map[i_entry["name"]] = i_entry

        items_split = []

        # Filter items by transaction type
        for item in items:
            i_p = item.get("parsed_tags", {}).get("t", None)
            if i_p is None or i_p == '':
                continue
            if len(keys) > 0 and i_p not in keys:
                continue
            items_split.append(item)

        return items_split

    def get_balance_split(self, items=[]):
        """
        Add multiplier to items based on balance type (expenses=-1, revenue=1).
        Uses self.label_ to identify balance type labels.

        Args:
            items: List of items with parsed_tags

        Returns:
            Modified items list with 'multiplier' field added
        """
        # Build balance label map from self.label_
        # Balance labels have type=0
        balance_map = {}
        for i_entry in self.label_:
            if i_entry["type"] == 0:  # Balance type
                balance_map[i_entry["name"]] = i_entry

        # Add multiplier based on balance type
        for item in items:
            i_p = item.get("parsed_tags", {}).get("c", None)
            if i_p == "expenses":
                item["multiplier"] = -1
            elif i_p == "revenue":
                item["multiplier"] = 1

        return items


    def parse_tags_from_string(self, tag_str: str, label_map: dict) -> dict:
        """
        Parse tag string format: id_id_id_id_[id,id,...]
        Example: 3_4_5_6_[7,8]

        Positions:
        - First id: count (c)
        - Second id: transaction (t)
        - Third id: bank (b)
        - Fourth id: main (m)
        - Fifth: list of secondary ids (s) in brackets [id,id,...]

        Args:
            tag_str: String in format "id_id_id_id_[id,id,...]"
            label_map: Dictionary mapping label_id to label info (from op_label_get_all)

        Returns:
            Dictionary with keys: c, t, b, m, s with label names
            Example: {'c': 'Expense', 't': 'Groceries', 'b': 'Credit Card', 'm': 'Food', 's': ['Fresh', 'Dairy']}
        """
        parsed = {
            'c': "",
            't': "",
            'b': "",
            'm': "",
            's': []
        }

        if not tag_str:
            return parsed

        # Split by underscore
        parts = tag_str.split('_')

        if len(parts) < 5:
            # Incomplete tag string, return defaults
            return parsed

        # Parse count (first part): id
        c_part = parts[0].strip()
        if c_part.isdigit():
            label_id = int(c_part)
            label_info = label_map.get(label_id)
            if label_info:
                parsed['c'] = label_info.get('name', '')

        # Parse transaction (second part): id
        t_part = parts[1].strip()
        if t_part.isdigit():
            label_id = int(t_part)
            label_info = label_map.get(label_id)
            if label_info:
                parsed['t'] = label_info.get('name', '')

        # Parse bank (third part): id
        b_part = parts[2].strip()
        if b_part.isdigit():
            label_id = int(b_part)
            label_info = label_map.get(label_id)
            if label_info:
                parsed['b'] = label_info.get('name', '')

        # Parse main (fourth part): id
        m_part = parts[3].strip()
        if m_part.isdigit():
            label_id = int(m_part)
            label_info = label_map.get(label_id)
            if label_info:
                parsed['m'] = label_info.get('name', '')

        # Parse secondary (fifth part): [id,id,...]
        s_part = parts[4].strip()
        if s_part:
            # Remove brackets and split by comma
            s_part_clean = s_part.strip('[]')
            if s_part_clean:
                s_ids = s_part_clean.split(',')
                for s_id in s_ids:
                    s_id_clean = s_id.strip()
                    if s_id_clean.isdigit():
                        label_id = int(s_id_clean)
                        label_info = label_map.get(label_id)
                        if label_info:
                            parsed['s'].append(label_info.get('name', ''))

        return parsed

    def build_tags_string(self, tags_dict: dict) -> str:
        """
        Build tag string from dictionary (inverse of parse_tags_from_string).

        Args:
            tags_dict: Dictionary with keys c, t, b, m, s containing label IDs
                      Example: {'c': 3, 't': 4, 'b': 5, 'm': 6, 's': [7, 8]}

        Returns:
            String in format "id_id_id_id_[id,id,...]"
            Example: "3_4_5_6_[7,8]"
        """
        # Extract IDs with defaults (0 for missing single IDs, empty list for secondary)
        c_id = tags_dict.get('c', 0)
        t_id = tags_dict.get('t', 0)
        b_id = tags_dict.get('b', 0)
        m_id = tags_dict.get('m', 0)
        s_ids = tags_dict.get('s', [])

        # Build the secondary part
        if s_ids:
            # Convert list of IDs to comma-separated string in brackets
            s_part = '[' + ','.join(str(sid) for sid in s_ids) + ']'
        else:
            s_part = '[]'

        # Build complete string
        tag_string = f"{c_id}_{t_id}_{b_id}_{m_id}_{s_part}"

        return tag_string

    def compose_labels(self):
        """
        Based on a hard coded list of labels, we compose the labels here:
        a) label type (ID) is a reference to the grouping of the label (e.g., balance, transaction, account, main labels, secondary labels)
        b) label sub-type (ID) is a reference to the specific label. This is mostly important when label_types are having
           different meanings: e.g. Account: "Savings (label_type=Account)" vs "Liability (label_type=Account)" or Transaction: "Fixed (label_type=Transaction)" vs "Variable (label_type=Transaction)"
        c) The compose labels methods works without any user information.
        """

        for i_entry in self.label_:
            i_label_owner = i_entry["label_owner"]

            if i_label_owner == -2:
                continue

            i_label = {
                "name": i_entry["name"],
                "description": i_entry["description"],
                "composite": i_entry["composite"],
                "label_owner": i_entry["label_owner"],  # Project-wide label or user-specific
                "label_status": i_entry["label_status"],
                "label_type": i_entry["type"],
                "label_sub_type": i_entry["sub_type"]
            }
            self.dbh.op_label_create(label_dict=i_label,
                                     project_id=self.project_id)

    def compose_accounts(self):
        """
        Create liability account labels for each user in the project.
        Uses self.label_ structure to find the account template with label_owner=-2,
        then creates a personalized liability account for each user.
        """
        if not self.users or len(self.users) == 0:
            # No users provided, skip account creation
            return

        # Find the liability account template from self.label_
        account_template = []
        for i_entry in self.label_:
            if i_entry.get("label_owner") == -2:
                account_template.append(i_entry)

        if account_template is None:
            # No account template found, skip
            return

        # Create a liability account for each user
        for i_user in self.users:
            try:
                user_name = i_user.get("username", "Unknown")
                user_id = i_user.get("user_id", -1)

                if user_id <= 0:
                    # Skip invalid user IDs
                    continue
                for i_entry in account_template:
                    # Create personalized account label for this user
                    i_label = {
                        "name": i_entry["name"] + f" - {user_name}",
                        "description": i_entry["description"],
                        "composite": i_entry["composite"],
                        "label_owner": user_id,  # User-specific account
                        "label_status": i_entry["label_status"],
                        "label_type": i_entry["type"],
                        "label_sub_type": i_entry["sub_type"]
                    }
                    self.dbh.op_label_create(label_dict=i_label,
                                             project_id=self.project_id)
            except Exception as e:
                if hasattr(self.dbh, 'log'):
                    self.dbh.log(f"Error preparing account label for user {i_user}: {e}")
                raise Exception(f"Failed to prepare account for user {i_user.get('username', 'unknown')}: {str(e)}")

class ProjectVacation(ProjectComposer):
    """
    Composer for vacation/travel planning projects.
    Manages travel expenses, accommodations, activities, and shared costs.
    """

    def __init__(self, dbh=None, project_id=None, users=[]):
        super().__init__(dbh=dbh, project_id=project_id, users=users)
        self.name = "Vacation"

        self.category_labels = {
            "accommodation": -1,
            "transportation": -1,
            "food": -1,
            "activities": -1,
            "shopping": -1
        }

    def compose_labels(self):
        """
        Create action labels for vacation planning.
        These include categories like accommodation, transportation, food, activities, and shopping.
        """
        action_labels = []

        # Travel category labels
        action_labels.append({
            "name": "accommodation",
            "description": "Hotels, hostels, rentals, and lodging",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        action_labels.append({
            "name": "transportation",
            "description": "Flights, trains, buses, taxis, car rentals",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        action_labels.append({
            "name": "food",
            "description": "Restaurants, groceries, snacks",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        action_labels.append({
            "name": "activities",
            "description": "Tours, attractions, entertainment",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        action_labels.append({
            "name": "shopping",
            "description": "Souvenirs, gifts, personal items",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        action_labels.append({
            "name": "miscellaneous",
            "description": "Other vacation-related expenses",
            "composite": None,
            "label_owner": -1,  # Project-wide label
            "label_status": 2,
            "label_type": 0
        })

        # Create all labels in database
        for label in action_labels:
            self.dbh.op_label_create(label_dict=label, project_id=self.project_id)

    def compose_accounts(self):
        """
        Create shared expense account labels for vacation participants.
        """
        if not self.users or len(self.users) == 0:
            # No users provided, skip account creation
            return

        account_labels = []

        for user in self.users:
            try:
                user_name = user.get("username", "Unknown")
                user_id = user.get("user_id", -1)

                if user_id <= 0:
                    # Skip invalid user IDs
                    continue

                account_labels.append({
                    "name": f"[V] Travel Account - {user_name}",
                    "description": f"Vacation expense account for {user_name}",
                    "composite": None,
                    "label_owner": user_id,
                    "label_status": 2,
                    "label_type": 1
                })
            except Exception as e:
                if hasattr(self.dbh, 'log'):
                    self.dbh.log(f"Error preparing account label for user {user}: {e}")
                raise Exception(f"Failed to prepare account for user {user.get('username', 'unknown')}: {str(e)}")

        # Add a shared account for group expenses
        account_labels.append({
            "name": "[V] Shared Expenses",
            "description": "Shared vacation expenses for all travelers",
            "composite": None,
            "label_owner": -1,  # Project-wide shared account
            "label_status": 2,
            "label_type": 1
        })

        # Create all account labels in database
        for label in account_labels:
            try:
                self.dbh.op_label_create(label_dict=label, project_id=self.project_id)
            except Exception as e:
                if hasattr(self.dbh, 'log'):
                    self.dbh.log(f"Error creating account label {label.get('name')}: {e}")
                raise Exception(f"Failed to create account label {label.get('name', 'unknown')}: {str(e)}")

    def get_label_map(self):
        """Return a dictionary mapping label type IDs to their group names."""
        ret = {}
        for i_group in [self.travel_categories,
                        self.travel_accounts,
                        self.travel_labels]:
            ret[i_group["type"]] = i_group["group"]
        return ret

    def get(self):
        """Return the label structure for vacation projects."""
        return {
            "travel_categories": self.travel_categories,
            "travel_accounts": self.travel_accounts,
            "travel_labels": self.travel_labels
        }

    def parse_tags_from_string(self, tag_str: str, label_map: dict) -> dict:
        """
        Parse tag string format for vacation projects.
        Uses same format as ExpenseTracker: id_id_id_id_[id,id,...]

        Positions can be interpreted differently based on vacation context:
        - First id: category (c)
        - Second id: accommodation (a)
        - Third id: transportation (t)
        - Fourth id: activity (ac)
        - Fifth: list of additional tags (s)

        Args:
            tag_str: String in format "id_id_id_id_[id,id,...]"
            label_map: Dictionary mapping label_id to label info

        Returns:
            Dictionary with keys: c, a, t, ac, s with label names
        """
        parsed = {
            'c': "",
            'a': "",
            't': "",
            'ac': "",
            's': []
        }

        if not tag_str:
            return parsed

        parts = tag_str.split('_')

        if len(parts) < 5:
            return parsed

        # Parse category
        if parts[0].strip().isdigit():
            label_id = int(parts[0].strip())
            label_info = label_map.get(label_id)
            if label_info:
                parsed['c'] = label_info.get('name', '')

        # Parse accommodation
        if parts[1].strip().isdigit():
            label_id = int(parts[1].strip())
            label_info = label_map.get(label_id)
            if label_info:
                parsed['a'] = label_info.get('name', '')

        # Parse transportation
        if parts[2].strip().isdigit():
            label_id = int(parts[2].strip())
            label_info = label_map.get(label_id)
            if label_info:
                parsed['t'] = label_info.get('name', '')

        # Parse activity
        if parts[3].strip().isdigit():
            label_id = int(parts[3].strip())
            label_info = label_map.get(label_id)
            if label_info:
                parsed['ac'] = label_info.get('name', '')

        # Parse secondary tags
        s_part = parts[4].strip().strip('[]')
        if s_part:
            for s_id in s_part.split(','):
                s_id_clean = s_id.strip()
                if s_id_clean.isdigit():
                    label_id = int(s_id_clean)
                    label_info = label_map.get(label_id)
                    if label_info:
                        parsed['s'].append(label_info.get('name', ''))

        return parsed

    def build_tags_string(self, tags_dict: dict) -> str:
        """
        Build tag string from dictionary for vacation projects.

        Args:
            tags_dict: Dictionary with keys c, a, t, ac, s containing label IDs
                      Example: {'c': 1, 'a': 2, 't': 3, 'ac': 4, 's': [5, 6]}

        Returns:
            String in format "id_id_id_id_[id,id,...]"
        """
        c_id = tags_dict.get('c', 0)
        a_id = tags_dict.get('a', 0)
        t_id = tags_dict.get('t', 0)
        ac_id = tags_dict.get('ac', 0)
        s_ids = tags_dict.get('s', [])

        s_part = '[' + ','.join(str(sid) for sid in s_ids) + ']' if s_ids else '[]'

        return f"{c_id}_{a_id}_{t_id}_{ac_id}_{s_part}"

