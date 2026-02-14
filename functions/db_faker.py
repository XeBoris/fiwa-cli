

def faker_users(dbh, num_users=10):
    """Populate the database with fake users for testing purposes."""
    from faker import Faker
    fake = Faker()

    for i in range(num_users):
        if i == 0:
            _superu = True
        else:
            _superu = False

        _f = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "username": f"user{str(i).zfill(1)}",
            "email": f"user{str(i).zfill(1)}@fiwa.com",
            "password": f"u{i}",  # Use a common password for testing
            "birthday": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%Y-%m-%d"),
            "max_projects": fake.random_int(min=1, max=3),
            "is_superuser": _superu,  # 10% chance to be superuser
            "scope": "user:write",
            "activated": True
        }
        print(_f)
        dbh.op_user_create(_f)

    print(f"Created {num_users} fake users.")

def faker_user_login(user, password, dbh):
    """Test login for a fake user."""
    try:
        user_session = dbh.op_user_login(username=user, password=password)
        if user_session:
            print(f"Login successful for {user}! Session info: {user_session}")
        else:
            print(f"Login failed for {user}: Invalid credentials")
    except Exception as e:
        print(f"Error during login for {user}: {str(e)}")

def faker_projects(dbh):
    """Populate the database with fake projects for testing purposes.
    Creates one project for each user in the database.
    Additionally:
    - User 1 gets 2 more projects (to reach their max)
    - User 2 gets 1 more project
    - User 2 is added to user 1's second project
    """
    from faker import Faker
    import random
    fake = Faker()

    # Get all user IDs from the database
    user_ids = dbh.op_user_get_all_ids()

    if not user_ids:
        print("No users found in database. Please create users first.")
        return

    # Phase 1: Create one project for each user
    print("\n=== Phase 1: Creating one project per user ===")
    project_count = 0
    user_projects = {}  # Track projects for each user

    for user_id in user_ids:
        # Generate random currency data
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
        main_currency = random.choice(currencies)
        currency_list = random.sample(currencies, k=random.randint(1, 3))

        project_data = {
            "name": f"Project {fake.word().capitalize()} {fake.word().capitalize()}",
            "description": fake.sentence(),
            "currency_main": main_currency,
            "currency_list": currency_list
        }

        try:
            project_id = dbh.op_project_create(project_data, user_id)
            print(f"Created project {project_id} for user {user_id}: {project_data['name']}")

            # Track projects for each user
            if user_id not in user_projects:
                user_projects[user_id] = []
            user_projects[user_id].append(project_id)

            project_count += 1
        except ValueError as e:
            print(f"Could not create project for user {user_id}: {e}")
        except Exception as e:
            print(f"Error creating project for user {user_id}: {e}")

    print(f"\nCreated {project_count} initial projects for {len(user_ids)} users.")

    # Phase 2: Add additional projects for user 1 (2 more projects)
    print("\n=== Phase 2: Adding 2 more projects for user 1 ===")
    if 1 in user_projects:
        for i in range(2):
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
            main_currency = random.choice(currencies)
            currency_list = random.sample(currencies, k=random.randint(1, 3))

            project_data = {
                "name": f"Project {fake.word().capitalize()} {fake.word().capitalize()}",
                "description": fake.sentence(),
                "currency_main": main_currency,
                "currency_list": currency_list
            }

            try:
                project_id = dbh.op_project_create(project_data, 1)
                print(f"Created additional project {project_id} for user 1: {project_data['name']}")
                user_projects[1].append(project_id)
                project_count += 1
            except ValueError as e:
                print(f"Could not create additional project for user 1: {e}")
                break
            except Exception as e:
                print(f"Error creating additional project for user 1: {e}")
                break

    # Phase 3: Add one more project for user 2
    print("\n=== Phase 3: Adding 1 more project for user 2 ===")
    if 2 in user_projects:
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
        main_currency = random.choice(currencies)
        currency_list = random.sample(currencies, k=random.randint(1, 3))

        project_data = {
            "name": f"Project {fake.word().capitalize()} {fake.word().capitalize()}",
            "description": fake.sentence(),
            "currency_main": main_currency,
            "currency_list": currency_list
        }

        try:
            project_id = dbh.op_project_create(project_data, 2)
            print(f"Created additional project {project_id} for user 2: {project_data['name']}")
            user_projects[2].append(project_id)
            project_count += 1
        except ValueError as e:
            print(f"Could not create additional project for user 2: {e}")
        except Exception as e:
            print(f"Error creating additional project for user 2: {e}")

    # Phase 4: Add user 2 to user 1's second project
    print("\n=== Phase 4: Adding user 2 to user 1's second project ===")
    if 1 in user_projects and len(user_projects[1]) >= 2 and 2 in user_ids:
        second_project_of_user1 = user_projects[1][1]  # Index 1 is the second project
        try:
            dbh.op_project_add_user(project_id=second_project_of_user1, user_id=2, project_perm_model='000000', project_primary=False)
            print(f"Successfully added user 2 to project {second_project_of_user1} (user 1's second project)")
        except ValueError as e:
            print(f"Could not add user 2 to project {second_project_of_user1}: {e}")
        except Exception as e:
            print(f"Error adding user 2 to project: {e}")

    print(f"\n=== Summary ===")
    print(f"Total projects created: {project_count}")
    for user_id, projects in user_projects.items():
        print(f"User {user_id}: {len(projects)} project(s) - IDs: {projects}")

