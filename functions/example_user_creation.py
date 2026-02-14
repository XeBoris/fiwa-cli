"""
Example usage of SQLLiteHandler user creation functionality.
This file demonstrates how to use the op_user_create method.
"""

from functions.handler_sqllite import SQLLiteHandler

# Example 1: Create a basic user with required fields only
def example_basic_user():
    db_handler = SQLLiteHandler(db_path="./test.db")

    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "password": "securepassword123"  # Will be hashed automatically
    }

    try:
        user_id = db_handler.op_user_create(user_data)
        print(f"User created successfully with ID: {user_id}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Error creating user: {e}")


# Example 2: Create a user with all optional fields
def example_full_user():
    db_handler = SQLLiteHandler(db_path="./test.db")

    user_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "username": "janesmith",
        "email": "jane.smith@example.com",
        "password": "anotherpassword456",
        "birthday": "1990-05-15",  # Optional: YYYY-MM-DD format
        "max_projects": 5,  # Optional: default is 3
        "is_superuser": True,  # Optional: default is False
        "scope": "admin:full",  # Optional: default is 'user:write'
        "activated": True  # Optional: default is True
    }

    try:
        user_id = db_handler.op_user_create(user_data)
        print(f"User created successfully with ID: {user_id}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Error creating user: {e}")


# Example 3: Login with the created user
def example_login():
    db_handler = SQLLiteHandler(db_path="./test.db")

    # Try to login with username
    user_id = db_handler.op_user_login("johndoe", "securepassword123")
    if user_id:
        print(f"Login successful! User ID: {user_id}")
    else:
        print("Login failed: Invalid credentials")

    # Try to login with email
    user_id = db_handler.op_user_login("john.doe@example.com", "securepassword123")
    if user_id:
        print(f"Login successful with email! User ID: {user_id}")
    else:
        print("Login failed: Invalid credentials")


# Example 4: Handle duplicate email error
def example_duplicate_email():
    db_handler = SQLLiteHandler(db_path="./test.db")

    user_data = {
        "first_name": "Duplicate",
        "last_name": "User",
        "username": "duplicate",
        "email": "john.doe@example.com",  # Same email as example 1
        "password": "password"
    }

    try:
        user_id = db_handler.op_user_create(user_data)
        print(f"User created successfully with ID: {user_id}")
    except ValueError as e:
        print(f"Expected error - {e}")


# Example 5: Usage from CreateUserForm in Textual app
def example_from_textual_form(form_data):
    """
    This is how you would use it from the CreateUserForm widget.
    form_data comes from the UserCreated message.
    """
    db_handler = SQLLiteHandler(db_path="./fiwa_app.db")

    # The form_data already has the structure we need
    try:
        user_id = db_handler.op_user_create(form_data)
        return {"success": True, "user_id": user_id, "message": "User created successfully"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}


if __name__ == "__main__":
    print("Example 1: Basic user creation")
    example_basic_user()

    print("\nExample 2: Full user creation with optional fields")
    example_full_user()

    print("\nExample 3: User login")
    example_login()

    print("\nExample 4: Duplicate email handling")
    example_duplicate_email()
