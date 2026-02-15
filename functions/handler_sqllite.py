import sqlite3
from typing import Dict, Optional
from pathlib import Path
import os
import hashlib
import uuid
from datetime import datetime
from datetime import timedelta

class SQLLiteHandler:
    def __init__(self, db_path=":memory:"):
        self._pw_salt = "fiwa_default_salt_2026"
        self._db_salt = "stand"
        self._db_path = db_path
        self._connection = None
        self._cursor = None

    def set_path(self, db_path):
        self._db_path = db_path

    def set_pw_salt(self, pw_salt):
        self._pw_salt = pw_salt

    def set_db_salt(self, db_salt):
        self._db_salt = db_salt

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        """
        Hash a password using SHA-256 with an optional salt.

        Args:
            password: The plain text password to hash
            salt: Optional salt to add to the password. If not provided, uses default salt.

        Returns:
            The hashed password as a hexadecimal string
        """
        if salt is None:
            raise ValueError("Salt must be provided for password hashing")

        # Combine password with salt
        salted_password = f"{password}{salt}"

        # Create SHA-256 hash
        hash_object = hashlib.sha256(salted_password.encode('utf-8'))

        return hash_object.hexdigest()

    def initialize_database(self, schema_path=None):

        if os.path.exists(self._db_path):
            return 2  # Database already exists, no need to initialize

        self.load()

        # Read and execute schema file
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema_sql = schema_file.read_text(encoding='utf-8')
        self._cursor.executescript(schema_sql)
        self._connection.commit()

        self.close()

        return 1

    def load(self):
        self._connection = sqlite3.connect(self._db_path)
        self._cursor = self._connection.cursor()

    def execute_query(self, query, params=None):
        if params is None:
            params = []
        self._cursor.execute(query, params)
        self._connection.commit()
        return self._cursor.fetchall()

    def close(self):
        self._connection.close()

    def op_total_number_of_users(self):
        """
        This is database operation (op_) to get the total number of users from the database.
        :return:
        """
        self.load()
        result = self.execute_query(f"SELECT COUNT(*) FROM p{self._db_salt}_users")
        self.close()
        return result[0][0] if result else 0

    def op_user_create(self, user_dict: Dict) -> Optional[int]:
        """
        Create a user in the database based on the schema.

        Args:
            user_dict: Dictionary containing user information with keys:
                - first_name (required): User's first name
                - last_name (required): User's last name
                - username (required): Username
                - email (required): Email address (must be unique)
                - password (required): Plain text password (will be hashed)
                - birthday (optional): Date of birth in 'YYYY-MM-DD' format
                - max_projects (optional): Maximum number of projects allowed (default: 3)
                - is_superuser (optional): Whether user is a superuser (default: False)
                - scope (optional): User scope (default: 'user:write')
                - activated (optional): Whether user is activated (default: True)

        Returns:
            The user_id of the created user, or None if creation failed
        """
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'username', 'email', 'password']
        for field in required_fields:
            if not user_dict.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        # Hash the password
        password_hash = self.hash_password(user_dict['password'],
                                           salt=self._pw_salt)

        # Generate unique identifier
        unique_identifier = str(uuid.uuid4())

        # Prepare values with defaults
        first_name = user_dict['first_name']
        last_name = user_dict['last_name']
        username = user_dict['username']
        email = user_dict['email']
        birthday = user_dict.get('birthday', None)
        max_projects = user_dict.get('max_projects', 3)
        is_superuser = 1 if user_dict.get('is_superuser', False) else 0
        scope = user_dict.get('scope', 'user:write')
        activated = 1 if user_dict.get('activated', True) else 0

        # Construct query
        query = f"""
            INSERT INTO p{self._db_salt}_users 
            (first_name, last_name, username, birthday, email, password_hash, 
             activated, is_superuser, scope, max_projects, unique_identifier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            first_name, last_name, username, birthday, email, password_hash,
            activated, is_superuser, scope, max_projects, unique_identifier
        ]

        try:
            self.load()
            self.execute_query(query, params)
            # Get the last inserted row id
            user_id = self._cursor.lastrowid
            self.close()
            return user_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                if "email" in str(e):
                    raise ValueError(f"Email '{email}' already exists in the database")
                else:
                    raise ValueError(f"User with this information already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create user: {str(e)}")

    def op_user_login(self, username, password):
        """
        This is database operation (op_) to login a user from the database.
        1) A login consists out of checking username & password.
        2) Check all projects of that user (and their permissions in those projects).

        Args:
            username: Username or email of the user
            password: Plain text password (will be hashed for comparison)

        Returns:
            user_id if login successful, None otherwise
        """
        # Hash the provided password
        password_hash = self.hash_password(password=password,
                                           salt=self._pw_salt)

        self.load()
        # Check against both username and email fields
        result = self.execute_query(
            f"""SELECT user_id FROM p{self._db_salt}_users 
                WHERE (username = ? OR email = ?) AND password_hash = ? AND activated = 1""",
            [username, username, password_hash]
        )

        # If no matching user is found, return None
        if not result:
            self.close()
            return None

        # Register the user to the session_table: each user can
        # only have one active session, so we delete old sessions and insert a new one
        user_id = result[0][0]
        now = datetime.utcnow().isoformat()
        session_uuid = str(uuid.uuid4())
        session_type = "local_login"

        # Delete any existing sessions for this user (enforce single session)
        self.execute_query(
            f"DELETE FROM p{self._db_salt}_session_table WHERE user_id = ?",
            [user_id]
        )

        # Insert new session
        self.execute_query(
            f"""INSERT INTO p{self._db_salt}_session_table 
                (user_id, session_start, session_uuid, session_type) 
                VALUES (?, ?, ?, ?)""",
            [user_id, now, session_uuid, session_type]
        )

        self.close()

        # Return session information as a dictionary
        return {
            "user_id": user_id,
            "session_uuid": session_uuid,
            "session_start": now,
            "session_type": session_type
        }

    def op_user_logout(self, session_uuid):
        """
        This is database operation (op_) to logout a user from the database.
        1) A logout consists out of deleting the session from the session table.

        Args:
            session_uuid: The UUID of the session to delete
        Returns:
            True if logout successful, False otherwise
        """
        self.load()
        # Delete the session with the given UUID
        try:
            self.execute_query(
                f"DELETE FROM p{self._db_salt}_session_table WHERE session_uuid = ?",
                [session_uuid]
            )
            self.close()
            return True
        except Exception as e:
            self.close()
            return False

    def op_get_user_sessions(self) -> Dict:
        """
        This is database operation (op_) to get all active sessions for a user from the database.

        Args:
            user_id: The ID of the user to retrieve sessions for
        Returns:
            A dictionary containing session information for the user
        """
        dt_now = datetime.utcnow()

        self.load()
        result = self.execute_query(
            f"""SELECT * FROM p{self._db_salt}_session_table"""
        )

        if len(result) != 1:
            print("Not allowed to have multiple sessions for one user, but found multiple sessions in the database. This should not happen.")
            self.close()
            return {}

        elif len(result) == 1:
            # we use the first session, extract the user_id and session_uuid and session_start and session_type
            result = result[0]
            user_id = result[1]
            session_uuid = result[3]
            session_start = result[2]
            session_type = result[4]
            session_start = datetime.fromisoformat(session_start)

            self.close()

            if dt_now - session_start > timedelta(minutes=30):
                # session expired, delete it and return empty
                self.op_user_logout(session_uuid)
                return {}

            # Fetch user info and project info
            user_info = self.op_user_get_info(user_id)
            project_info = self.op_project_get_info(user_id)

            return {
                "user_id": user_info["user_id"],
                "session_info": {
                    "session_uuid": session_uuid,
                    "session_start": session_start,
                    "session_type": session_type,
                    "is_logged_in": True
                },
                "user_info": user_info,
                "project_info": project_info
            }

        return True

    def op_user_get_info(self, user_id):
        """
        This is database operation (op_) to get user information from the database.
        :return:
        """
        self.load()
        result = self.execute_query(
            f"""SELECT user_id, first_name, last_name, username, email, birthday, 
                activated, is_superuser, scope, max_projects, unique_identifier 
                FROM p{self._db_salt}_users WHERE user_id = ?""",
            [user_id]
        )
        self.close()
        if not result:
            return None

        row = result[0]
        user_info = {
            "user_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "username": row[3],
            "email": row[4],
            "birthday": row[5],
            "activated": bool(row[6]),
            "is_superuser": bool(row[7]),
            "scope": row[8],
            "max_projects": row[9],
            "unique_identifier": row[10]
        }
        return user_info

    def op_get_max_projects(self, user_id: int) -> int:
        """
        Get the maximum number of projects allowed for a user.

        Args:
            user_id: The user ID to query

        Returns:
            The max_projects value for the user, or 3 (default) if not found
        """
        self.load()
        result = self.execute_query(
            f"""SELECT max_projects FROM p{self._db_salt}_users WHERE user_id = ?""",
            [user_id]
        )
        self.close()

        if result and len(result) > 0:
            return result[0][0]
        return 3  # Default

    def op_project_get_info(self, user_id):
        """
        This is database operation (op_) to get project information for a user from the database.
        :return:
        """
        self.load()
        result = self.execute_query(
            f"""SELECT p.project_id, p.name, p.description, p.created_at, 
                p.currency_main, p.currency_list, p.project_hash, 
                upm.project_primary, upm.project_perm_model
                FROM p{self._db_salt}_projects p 
                JOIN p{self._db_salt}_user_project_map upm ON p.project_id = upm.project_id 
                WHERE upm.user_id = ?""",
            [user_id]
        )
        self.close()
        if not result:
            return []

        project_list = []
        for row in result:
            project_info = {
                "project_id": row[0],
                "project_name": row[1],  # Column is 'name' in DB, but we return as 'project_name'
                "description": row[2],
                "created_at": row[3],
                "currency_main": row[4],
                "currency_list": row[5],
                "project_hash": row[6],
                "project_primary": bool(row[7]),
                "project_perm_model": row[8]
            }
            project_list.append(project_info)
        return project_list

    def op_user_get_all_ids(self):
        """
        This is database operation (op_) to get all user IDs from the database.
        :return: List of user_ids
        """
        self.load()
        result = self.execute_query(
            f"""SELECT user_id FROM p{self._db_salt}_users"""
        )
        self.close()
        return [row[0] for row in result] if result else []

    def op_project_create(self, project_dict: Dict, user_id: int) -> Optional[int]:
        """
        Create a project in the database and link it to a user.

        Args:
            project_dict: Dictionary containing project information with keys:
                - name (required): Project name
                - description (optional): Project description
                - currency_main (optional): Main currency (3-letter code)
                - currency_list (optional): List of currencies
            user_id: The ID of the user creating/owning the project

        Returns:
            The project_id of the created project, or None if creation failed
        """
        import json

        # Validate required fields
        if not project_dict.get('name'):
            raise ValueError("Project name is required")

        # Prepare values with defaults
        name = project_dict['name']
        description = project_dict.get('description', '')
        created_at = project_dict.get('created_at', datetime.utcnow().isoformat())
        currency_main = project_dict.get('currency_main', None)
        currency_list = project_dict.get('currency_list', [])

        # Convert currency_list to JSON string for storage
        currency_list_str = json.dumps(currency_list) if currency_list else '[]'

        # Generate project hash from name, description, and currency_main
        hash_input = f"{name}|{description}|{currency_main or ''}"
        project_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

        # Check if user exists and get max_projects
        self.load()
        user_result = self.execute_query(
            f"""SELECT user_id, max_projects FROM p{self._db_salt}_users 
                WHERE user_id = ?""",
            [user_id]
        )

        if not user_result:
            self.close()
            raise ValueError(f"User with ID {user_id} not found")

        max_projects = user_result[0][1]

        # Count current projects for this user
        current_projects = self.execute_query(
            f"""SELECT COUNT(*) FROM p{self._db_salt}_user_project_map 
                WHERE user_id = ?""",
            [user_id]
        )
        project_count = current_projects[0][0] if current_projects else 0

        if project_count >= max_projects:
            self.close()
            raise ValueError(f"User {user_id} has reached the maximum number of projects ({max_projects})")

        # Insert project
        query = f"""
            INSERT INTO p{self._db_salt}_projects 
            (name, description, created_at, currency_main, currency_list, project_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        params = [
            name, description, created_at, currency_main, currency_list_str, project_hash
        ]

        try:
            self.execute_query(query, params)
            project_id = self._cursor.lastrowid

            # Determine if this is the user's first/primary project
            is_primary = 1 if project_count == 0 else 0

            # Link project to user in user_project_map
            map_query = f"""
                INSERT INTO p{self._db_salt}_user_project_map
                (user_id, project_id, created_at, project_perm_model, project_primary)
                VALUES (?, ?, ?, ?, ?)
            """
            map_params = [
                user_id, project_id, datetime.utcnow().isoformat(), '000000', is_primary
            ]
            self.execute_query(map_query, map_params)

            self.close()
            return project_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                if "project_hash" in str(e):
                    raise ValueError(f"A project with similar attributes already exists")
                else:
                    raise ValueError(f"Project with this information already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create project: {str(e)}")

    def op_project_update(self, project_dict: Dict) -> bool:
        """
        Update an existing project in the database.

        Args:
            project_dict: Dictionary containing project information with keys:
                - project_id (required): The ID of the project to update
                - name (optional): Updated project name
                - description (optional): Updated description
                - currency_main (optional): Updated main currency
                - currency_list (optional): Updated list of currencies

        Returns:
            True if successful, raises exception otherwise
        """
        import json

        # Validate required fields
        project_id = project_dict.get('project_id')
        if not project_id:
            raise ValueError("Project ID is required for update")

        self.load()

        # Check if project exists
        existing = self.execute_query(
            f"""SELECT project_id FROM p{self._db_salt}_projects WHERE project_id = ?""",
            [project_id]
        )
        if not existing:
            self.close()
            raise ValueError(f"Project with ID {project_id} not found")

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if 'name' in project_dict and project_dict['name']:
            update_fields.append("name = ?")
            params.append(project_dict['name'])

        if 'description' in project_dict:
            update_fields.append("description = ?")
            params.append(project_dict['description'] if project_dict['description'] else '')

        if 'currency_main' in project_dict:
            update_fields.append("currency_main = ?")
            params.append(project_dict['currency_main'])

        if 'currency_list' in project_dict:
            currency_list_str = json.dumps(project_dict['currency_list']) if project_dict['currency_list'] else '[]'
            update_fields.append("currency_list = ?")
            params.append(currency_list_str)

        if not update_fields:
            self.close()
            raise ValueError("No fields to update")

        # Generate new project hash if name, description, or currency_main changed
        if any(k in project_dict for k in ['name', 'description', 'currency_main']):
            # Get current values for hash calculation
            current_data = self.execute_query(
                f"""SELECT name, description, currency_main FROM p{self._db_salt}_projects 
                    WHERE project_id = ?""",
                [project_id]
            )
            if current_data:
                current_name = project_dict.get('name', current_data[0][0])
                current_desc = project_dict.get('description', current_data[0][1] or '')
                current_curr = project_dict.get('currency_main', current_data[0][2] or '')

                hash_input = f"{current_name}|{current_desc}|{current_curr}"
                project_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

                update_fields.append("project_hash = ?")
                params.append(project_hash)

        # Add project_id for WHERE clause
        params.append(project_id)

        # Execute update
        query = f"""
            UPDATE p{self._db_salt}_projects
            SET {', '.join(update_fields)}
            WHERE project_id = ?
        """

        try:
            self.execute_query(query, params)
            self.close()
            return True
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"A project with similar attributes already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to update project: {str(e)}")

    def op_project_add_user(self, project_id: int, user_id: int, project_perm_model: str = '000000', project_primary: bool = False) -> bool:
        """
        Add a user to an existing project.

        Args:
            project_id: The ID of the project
            user_id: The ID of the user to add to the project
            project_perm_model: Permission model for the user (default: '000000')
            project_primary: Whether this is the user's primary project (default: False)

        Returns:
            True if successful, raises exception otherwise
        """
        self.load()

        # Check if project exists
        project_check = self.execute_query(
            f"""SELECT project_id FROM p{self._db_salt}_projects WHERE project_id = ?""",
            [project_id]
        )
        if not project_check:
            self.close()
            raise ValueError(f"Project with ID {project_id} not found")

        # Check if user exists
        user_check = self.execute_query(
            f"""SELECT user_id FROM p{self._db_salt}_users WHERE user_id = ?""",
            [user_id]
        )
        if not user_check:
            self.close()
            raise ValueError(f"User with ID {user_id} not found")

        # Check if user is already in the project
        existing = self.execute_query(
            f"""SELECT id FROM p{self._db_salt}_user_project_map 
                WHERE user_id = ? AND project_id = ?""",
            [user_id, project_id]
        )
        if existing:
            self.close()
            raise ValueError(f"User {user_id} is already a member of project {project_id}")

        # Add user to project
        try:
            map_query = f"""
                INSERT INTO p{self._db_salt}_user_project_map
                (user_id, project_id, created_at, project_perm_model, project_primary)
                VALUES (?, ?, ?, ?, ?)
            """
            map_params = [
                user_id, project_id, datetime.utcnow().isoformat(),
                project_perm_model, 1 if project_primary else 0
            ]
            self.execute_query(map_query, map_params)
            self.close()
            return True
        except Exception as e:
            self.close()
            raise Exception(f"Failed to add user to project: {str(e)}")

    def op_label_get_all(self, project_id: int) -> list:
        """
        Get all labels for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of label dictionaries
        """
        self.load()
        result = self.execute_query(
            f"""SELECT label_id, name, description, created_at, composite, 
                label_status, label_type
                FROM p{self._db_salt}_labels 
                WHERE project_id = ?
                ORDER BY name""",
            [project_id]
        )
        self.close()

        if not result:
            return []

        labels = []
        for row in result:
            import json
            try:
                composite = json.loads(row[4]) if row[4] else []
            except:
                composite = []

            label = {
                "label_id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "composite": composite,
                "label_status": row[5],  # 0=deleted, 1=deactivated, 2=active
                "label_type": row[6]
            }
            labels.append(label)

        return labels

    def op_label_create(self, label_dict: Dict, project_id: int) -> Optional[int]:
        """
        Create a new label for a project.

        Args:
            label_dict: Dictionary containing label information with keys:
                - name (required): Label name
                - description (optional): Label description
                - composite (optional): List of composite elements
                - label_status (optional): Status (0=deleted, 1=deactivated, 2=active)
                - label_type (optional): Type (default: 1)
            project_id: The ID of the project

        Returns:
            The label_id of the created label, or None if creation failed
        """
        import json

        # Validate required fields
        if not label_dict.get('name'):
            raise ValueError("Label name is required")

        # Prepare values with defaults
        name = label_dict['name']
        description = label_dict.get('description', '')
        composite = label_dict.get('composite', [])
        composite_str = json.dumps(composite)
        label_status = label_dict.get('label_status', 2)  # Default: active
        label_type = label_dict.get('label_type', 1)
        created_at = datetime.utcnow().isoformat()

        self.load()

        # Check if label with same name exists in this project
        existing = self.execute_query(
            f"""SELECT label_id FROM p{self._db_salt}_labels 
                WHERE name = ? AND project_id = ?""",
            [name, project_id]
        )

        if existing:
            self.close()
            raise ValueError(f"Label '{name}' already exists in this project")

        # Insert label
        query = f"""
            INSERT INTO p{self._db_salt}_labels 
            (name, description, created_at, project_id, composite, label_status, label_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = [name, description, created_at, project_id, composite_str, label_status, label_type]

        try:
            self.execute_query(query, params)
            label_id = self._cursor.lastrowid
            self.close()
            return label_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Label '{name}' already exists in this project")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create label: {str(e)}")

    def op_label_update(self, label_id: int, label_dict: Dict) -> bool:
        """
        Update an existing label.

        Args:
            label_id: The ID of the label to update
            label_dict: Dictionary containing label information with keys:
                - name (optional): Updated label name
                - description (optional): Updated description
                - composite (optional): Updated composite list
                - label_status (optional): Updated status
                - label_type (optional): Updated type

        Returns:
            True if successful, raises exception otherwise
        """
        import json

        self.load()

        # Check if label exists
        existing = self.execute_query(
            f"""SELECT label_id FROM p{self._db_salt}_labels WHERE label_id = ?""",
            [label_id]
        )

        if not existing:
            self.close()
            raise ValueError(f"Label with ID {label_id} not found")

        # Build update query dynamically
        update_fields = []
        params = []

        if 'name' in label_dict and label_dict['name']:
            update_fields.append("name = ?")
            params.append(label_dict['name'])

        if 'description' in label_dict:
            update_fields.append("description = ?")
            params.append(label_dict['description'])

        if 'composite' in label_dict:
            update_fields.append("composite = ?")
            params.append(json.dumps(label_dict['composite']))

        if 'label_status' in label_dict:
            update_fields.append("label_status = ?")
            params.append(label_dict['label_status'])

        if 'label_type' in label_dict:
            update_fields.append("label_type = ?")
            params.append(label_dict['label_type'])

        if not update_fields:
            self.close()
            raise ValueError("No fields to update")

        # Add label_id for WHERE clause
        params.append(label_id)

        # Execute update
        query = f"""
            UPDATE p{self._db_salt}_labels
            SET {', '.join(update_fields)}
            WHERE label_id = ?
        """

        try:
            self.execute_query(query, params)
            self.close()
            return True
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Label name must be unique within the project")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to update label: {str(e)}")

    def op_label_delete(self, label_id: int, hard_delete: bool = False) -> bool:
        """
        Delete a label (soft or hard delete).

        Args:
            label_id: The ID of the label to delete
            hard_delete: If True, permanently delete. If False, mark as deleted (status=0)

        Returns:
            True if successful, raises exception otherwise
        """
        self.load()

        if hard_delete:
            # Permanently delete the label
            query = f"""DELETE FROM p{self._db_salt}_labels WHERE label_id = ?"""
        else:
            # Soft delete - mark as deleted (status = 0)
            query = f"""UPDATE p{self._db_salt}_labels SET label_status = 0 WHERE label_id = ?"""

        try:
            self.execute_query(query, [label_id])
            self.close()
            return True
        except Exception as e:
            self.close()
            raise Exception(f"Failed to delete label: {str(e)}")

    def op_get_current_user(self):
        """
        This is database operation (op_) to get the current user from the database.
        :return:
        """
        u = {
            "username": "Guest",
            "user_id": 0,
        }
        p = [{
            "project_id": 0,
            "project_name": "Default Project",
            "is_primary": True,
            "users_in_project": [u],
            "permissions": "",
            "labels": []
        }]


        return {"users": u, "projects": p}