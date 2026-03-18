from typing import List, Optional
import uuid
import json
import random
import datetime
from datetime import datetime, timedelta
import numpy as np

def generate_superhero_data(dbh):
    """
    We create 4 users:
    - Admin User (Armin Admin) - superuser with admin:write scope
    - Clark Kent (Superman) - regular user with user:write scope
    - Bruce Wayne (Batman) - regular user with user:write scope
    - Peter Parker (Spiderman) - regular user with user:write scope

    :param dbh:
    :return:
    """
    ret = {}

    user_dict = {"first_name": "Armin",
                 "last_name": "Admin",
                 "username": "admin",
                 "birthday": "1980-01-01",
                 "email": "admin@info.com",
                 "password": "admin123",
                 "is_superuser": True,
                 "scope": "admin:write",
                 "activated": True}
    uid0 = dbh.op_user_create(user_dict=user_dict)
    ret["admin"] = uid0

    user_dict = {"first_name": "Clark",
                 "last_name": "Kent",
                 "username": "superman",
                 "birthday": "1976-05-01",
                 "email": "superman@info.com",
                 "password": "abc",
                 "is_superuser": False,
                 "scope": "user:write",
                 "activated": True}
    uid0 = dbh.op_user_create(user_dict=user_dict)
    ret["superman"] = uid0

    user_dict = {"first_name": "Bruce",
                 "last_name": "Wayne",
                 "username": "batman",
                 "birthday": "1979-02-11",
                 "email": "batman@info.com",
                 "password": "abc",
                 "is_superuser": False,
                 "scope": "user:write",
                 "activated": True}
    uid1 = dbh.op_user_create(user_dict=user_dict)
    ret["batman"] = uid1

    user_dict = {"first_name": "Peter",
                 "last_name": "Parker",
                 "username": "spiderman",
                 "birthday": "2001-09-18",
                 "email": "spiderman@info.com",
                 "password": "abc",
                 "is_superuser": False,
                 "scope": "user:write",
                 "activated": True}
    uid2 = dbh.op_user_create(user_dict=user_dict)
    ret["spiderman"] = uid2

    return ret

def generate_superhero_projects(dbh, users={}):


    # Create some projects:
    project_dict = {
        "name": "Bat Cave Expenses",
        "description": "A common project of super heros",
        "currency_main": "USD",
        "currency_list": ["SEK", "EUR", "GBP"],
        "project_style": "ExpenseTracker",
        "project_staged": False,
        "project_activated": True,
        "project_store" : {"month_start": 25}
    }
    p0_id = dbh.op_project_create(project_dict=project_dict,
                          user_id=users["batman"])

    dbh.op_project_stage(project_id=p0_id,
                         users=[{"user_id": users["batman"],
                                 "user_name": "batman"}]
                         )

    project_dict = {
        "name": "Sweden Day Job",
        "description": "Being a friendly neighborhood spiderman is expensive",
        "currency_main": "SEK",
        "currency_list": ["USD", "EUR", "GBP"],
        "project_style": "ExpenseTracker",
        "project_staged": False,
        "project_activated": True,
        "project_store": {"month_start": 1}

    }
    p1_id = dbh.op_project_create(project_dict=project_dict,
                          user_id=users["spiderman"])

    dbh.op_project_stage(project_id=p1_id,
                         users=[{"user_id": users["spiderman"],
                                 "user_name": "spiderman"}]
                         )

    # bruce adds clark to his project:
    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]

    dbh.op_project_add_user(project_id=p_info["project_id"],
                            user_id=users["superman"],
                            project_perm_model='111100',
                            project_primary=False)

    dbh.op_project_stage(project_id=p_info["project_id"],
                         users=[{"user_id": users["superman"],
                                 "user_name": "superman"}]
                         )


    # peter adds bruce to his project:
    p_info = dbh.op_project_get_info(user_id=users["spiderman"])
    p_info = [i for i in p_info if i["project_name"] == "Sweden Day Job"][0]

    dbh.op_project_add_user(project_id=p_info["project_id"],
                            user_id=users["batman"],
                            project_perm_model='111100',
                            project_primary=False)
    dbh.op_project_stage(project_id=p_info["project_id"],
                         users=[{"user_id": users["batman"],
                                 "user_name": "batman"}]
                         )

def generate_superhero_labels(dbh, users):


    # now we need labels for the bat cave project:
    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]

    #-----------------

    account_labels = []
    i_label = {"name": "Wayne Enterprises", "description": "Revenue from Wayne Enterprises", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)
    i_label = {"name": "Inheritance", "description": "Monthly take out of inhertiance money", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)
    i_label = {"name": "Wayne Enterprises Creditcard", "description": "Credit Card", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)
    i_label = {"name": "Joker Card", "description": "Debit Card", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)
    i_label = {"name": "BM: Savings Account I", "description": "Savings I", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)
    i_label = {"name": "BM: Savings Account II", "description": "Savings II", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["batman"]}
    account_labels.append(i_label)

    i_label = {"name": "Daily Planet Income", "description": "Revenue from day job", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["superman"]}
    account_labels.append(i_label)
    i_label = {"name": "Daily Planet Company Card", "description": "Credit Card", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["superman"]}
    account_labels.append(i_label)
    i_label = {"name": "Gotham Bank Card", "description": "Debit Card", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["superman"]}
    account_labels.append(i_label)
    i_label = {"name": "SM: Savings Account I", "description": "Savings I", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["superman"]}
    account_labels.append(i_label)
    i_label = {"name": "SM: Savings Account II", "description": "Savings II", "composite": None,
               "label_status": 2, "label_type": 2, "label_owner": users["superman"]}
    account_labels.append(i_label)

    for i_label in account_labels:
        dbh.op_label_create(label_dict=i_label, project_id=p_info["project_id"])

    print(f"Created {len(account_labels)} account labels for project {p_info['project_name']}")

    #-------------------
    _labels = []
    i_label = {"name": "Concerts/Festivals", "description": "", "composite": None,
               "label_status": 2, "label_type": 3, "label_owner": -1}
    _labels.append(i_label)
    i_label = {"name": "Sports", "description": "", "composite": None,
               "label_status": 2, "label_type": 3, "label_owner": -1}
    _labels.append(i_label)
    i_label = {"name": "eLearning", "description": "", "composite": None,
               "label_status": 2, "label_type": 3, "label_owner": -1}
    _labels.append(i_label)
    i_label = {"name": "Wages", "description": "", "composite": None,
               "label_status": 2, "label_type": 3, "label_owner": -1}
    _labels.append(i_label)

    for i_label in _labels:
        dbh.op_label_create(label_dict=i_label, project_id=p_info["project_id"])

    print(f"Created {len(_labels)} item labels for project {p_info['project_name']}")

def generate_data(
    dbh,
    project_id: int,
    user_id: int,
    bought_for_id: int,
    names: list = [],
    labels: list = [],
    start_date_str: str = "2024-11-01",
    end_date: Optional[datetime] = None,
    currency: str = "USD",
    poisson_exp: float = 2.5,
    avg_weekly_spend: float = 100.0,
    max_weekly_spend: float = 150.0
) -> List[int]:
    """
    Generate realistic grocery shopping transaction data with Poisson-distributed shopping frequency.

    Creates shopping entries from a start date to today (or specified end date) with:
    - 1-8 shopping trips per week (Poisson distribution, mean ~3)
    - Average weekly spend of ~100 (with variance)
    - Individual trip amounts using clipped Poisson distribution (max 150)
    - Realistic grocery store names

    Args:
        dbh: Database handler instance with op_item_create method
        project_id (int): The project ID to associate items with
        user_id (int): User ID who bought and added the items
        bought_for_id (int): User ID for whom items were bought
        start_date_str (str): Start date in format "YYYY-MM-DD" (default: "2024-11-01")
        end_date (datetime, optional): End date for generation. Defaults to today.
        currency (str): Currency code (default: "USD")
        avg_weekly_spend (float): Average total spending per week (default: 100.0)
        max_weekly_spend (float): Maximum allowed weekly spend (default: 150.0)

    Returns:
        List[int]: List of created item IDs

    Example:
        >>> item_ids = generate_grocery_shopping_data(
        ...     dbh=database_handler,
        ...     project_id=1,
        ...     user_id=123,
        ...     bought_for_id=123,
        ...     start_date_str="2024-11-01"
        ... )
        >>> print(f"Created {len(item_ids)} grocery transactions")
    """

    # Grocery store names (mix of real chains from different regions)
    # grocery_stores =

    # Parse dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now()

    # Calculate number of weeks
    total_days = (end_date - start_date).days
    num_weeks = total_days / 7.0

    created_items = []
    current_date = start_date

    # Process week by week
    week_num = 0
    while current_date <= end_date:
        week_num += 1
        week_start = current_date
        week_end = min(current_date + timedelta(days=6), end_date)

        # Determine number of shopping trips this week (1-8, Poisson with mean 3)
        # Using Poisson lambda=2.5 gives good distribution between 1-8
        # poisson_exp = 2.5
        trips_this_week = min(8, max(1, int(np.random.poisson(poisson_exp) + 1)))

        # Generate random shopping days within the week
        week_days_range = (week_end - week_start).days + 1
        shopping_days = sorted(random.sample(range(week_days_range), min(trips_this_week, week_days_range)))

        # Calculate target weekly spend with some variance (±20%)
        weekly_variance = random.uniform(0.8, 1.2)
        target_weekly_spend = min(avg_weekly_spend * weekly_variance, max_weekly_spend)

        # Distribute the weekly spend across trips (with random variation)
        trip_weights = [random.uniform(0.5, 1.5) for _ in range(trips_this_week)]
        total_weight = sum(trip_weights)
        trip_amounts = [target_weekly_spend * (w / total_weight) for w in trip_weights]

        # Create shopping transactions for this week
        for day_offset, trip_amount in zip(shopping_days, trip_amounts):
            shopping_date = week_start + timedelta(days=day_offset)

            # Add some time variation (morning to evening)
            shopping_hour = random.randint(8, 20)
            shopping_minute = random.randint(0, 59)
            shopping_datetime = shopping_date.replace(hour=shopping_hour, minute=shopping_minute)

            # Clip amount to max (simulating Poisson-like distribution with cap)
            # Add Poisson-like variance to the amount
            amount_variance = np.random.poisson(10) - 10  # Centers around 0
            final_amount = max(5.0, min(trip_amount + amount_variance, max_weekly_spend))
            final_amount = round(final_amount, 2)

            # Select random store
            store_name = random.choice(names)

            # Create item dictionary
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": f"{store_name}",
                "note": f"Weekly shopping at {store_name}",
                "price": final_amount,
                "price_final": final_amount,
                "currency": currency,
                "currency_final": currency,
                "bought_date": shopping_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": user_id,
                "bought_for_id": bought_for_id,
                "added_by_id": user_id,
                "project_id": project_id,
                "exchange_rate": 1.0,
                "exchange_rate_date": shopping_date.strftime("%Y-%m-%d"),
                "tags": json.dumps(labels)  # Empty tags for now, can be populated with label IDs
            }

            # Create item in database
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create item for {shopping_date}: {e}")

        # Move to next week
        current_date = week_end + timedelta(days=1)

    print(f"Generated {len(created_items)} grocery shopping transactions")
    print(f"Period: {start_date_str} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Average trips per week: {len(created_items) / num_weeks:.1f}")

    return created_items


def generate_personal_supplies_data(dbh, users, start_date_str="2024-11-01"):

    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]
    print(p_info)

    # Generate grocery shopping data with realistic patterns
    label_id_person = dbh.op_label_get_by_name("Personal Supplies", p_info["project_id"])

    label_id_daily = dbh.op_label_get_by_name("daily", p_info["project_id"])
    label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])

    label_id_spending_bm1 = dbh.op_label_get_by_name("Wayne Enterprises Creditcard", p_info["project_id"])
    label_id_spending_bm2 = dbh.op_label_get_by_name("Joker Card", p_info["project_id"])

    label_id_spending_sm1 = dbh.op_label_get_by_name("Daily Planet Company Card", p_info["project_id"])
    label_id_spending_sm2 = dbh.op_label_get_by_name("Gotham Bank Card", p_info["project_id"])

    label_id_liability_bm = dbh.op_label_get_by_name("Liability Account Batman", p_info["project_id"])
    label_id_liability_sm = dbh.op_label_get_by_name("Liability Account Superman", p_info["project_id"])

    grocery_store_names = [
        "Normal", "Haargummies", "Duschsachen", "Zahncreme", "Rasierklingen", "Deo", "Shampoo",
        "DM", "Rossmann", "Müller", "Boots", "CVS", "Walgreens", "Superdrug",
        "DVD"
    ]

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_bm1}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=2,
        avg_weekly_spend=10.0,
        max_weekly_spend=15.0
    )
    print(f"ID: ({label_id_person}), generating sample data: Batman for Batman: {len(item_ids)}")

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_sm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.4,
        avg_weekly_spend=3.0,
        max_weekly_spend=5.0
    )
    print(f"ID: ({label_id_person}), generating sample data Batman for Clark: {len(item_ids)}")

    #
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_sm2}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=1.7,
        avg_weekly_spend=9.0,
        max_weekly_spend=12.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Clark: {len(item_ids)}")

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_bm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.5,
        avg_weekly_spend=2.0,
        max_weekly_spend=5.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Batman: {len(item_ids)}")

def generate_groceries_data(dbh, users, start_date_str="2024-11-01"):

    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]
    print(p_info)

    # Generate grocery shopping data with realistic patterns
    label_id_person = dbh.op_label_get_by_name("Groceries", p_info["project_id"])

    label_id_daily = dbh.op_label_get_by_name("daily", p_info["project_id"])
    label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])

    label_id_spending_bm1 = dbh.op_label_get_by_name("Wayne Enterprises Creditcard", p_info["project_id"])
    label_id_spending_bm2 = dbh.op_label_get_by_name("Joker Card", p_info["project_id"])

    label_id_spending_sm1 = dbh.op_label_get_by_name("Daily Planet Company Card", p_info["project_id"])
    label_id_spending_sm2 = dbh.op_label_get_by_name("Gotham Bank Card", p_info["project_id"])

    label_id_liability_bm = dbh.op_label_get_by_name("Liability Account Batman", p_info["project_id"])
    label_id_liability_sm = dbh.op_label_get_by_name("Liability Account Superman", p_info["project_id"])

    grocery_store_names = [
        "Lidl", "Aldi", "Coop", "Netto", "Walmart", "Target", "Kroger",
        "Tesco", "Carrefour", "Whole Foods", "Trader Joe's", "Safeway",
        "ICA", "Rewe", "Edeka", "Albert Heijn", "Costco", "Sam's Club"
    ]
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_bm1}_{label_id_person}_[]"

    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=2.5,
        avg_weekly_spend=10.0,
        max_weekly_spend=15.0
    )
    print(f"ID: ({label_id_person}), generating sample data: Batman for Batman: {len(item_ids)}")

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_sm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=1.5,
        avg_weekly_spend=3.0,
        max_weekly_spend=5.0
    )

    print(f"ID: ({label_id_person}), generating sample data Batman for Clark: {len(item_ids)}")
    #
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_sm1}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=2.1,
        avg_weekly_spend=9.0,
        max_weekly_spend=12.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Clark: {len(item_ids)}")

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_bm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.5,
        avg_weekly_spend=2.0,
        max_weekly_spend=5.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Batman: {len(item_ids)}")


def generate_books_data(dbh, users, start_date_str="2024-11-01"):

    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]
    print(p_info)

    # Generate grocery shopping data with realistic patterns
    label_id_person = dbh.op_label_get_by_name("Books", p_info["project_id"])

    label_id_daily = dbh.op_label_get_by_name("daily", p_info["project_id"])
    label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])

    label_id_spending_bm1 = dbh.op_label_get_by_name("Wayne Enterprises Creditcard", p_info["project_id"])
    label_id_spending_bm2 = dbh.op_label_get_by_name("Joker Card", p_info["project_id"])

    label_id_spending_sm1 = dbh.op_label_get_by_name("Daily Planet Company Card", p_info["project_id"])
    label_id_spending_sm2 = dbh.op_label_get_by_name("Gotham Bank Card", p_info["project_id"])

    label_id_liability_bm = dbh.op_label_get_by_name("Liability Account Batman", p_info["project_id"])
    label_id_liability_sm = dbh.op_label_get_by_name("Liability Account Superman", p_info["project_id"])

    grocery_store_names = [
        "Amazon Books", "Barnes & Noble", "Waterstones", "Thalia",
        "Books-A-Million", "Powell's Books", "Strand Bookstore",
        "Book Depository", "Audible", "Kindle Store",
        "Akademibokhandeln", "WHSmith", "Hugendubel", "Fnac"
    ]
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_bm1}_{label_id_person}_[]"

    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=1.5,
        avg_weekly_spend=10.0,
        max_weekly_spend=15.0
    )
    print(f"ID: ({label_id_person}), generating sample data: Batman for Batman: {len(item_ids)}")
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_sm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id=users["batman"],
        bought_for_id=users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.5,
        avg_weekly_spend=3.0,
        max_weekly_spend=5.0
    )

    print(f"ID: ({label_id_person}), generating sample data Batman for Clark: {len(item_ids)}")
    #
    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_spending_sm2}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["superman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.5,
        avg_weekly_spend=9.0,
        max_weekly_spend=12.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Clark: {len(item_ids)}")

    llb = f"{label_id_expenses}_{label_id_daily}_{label_id_liability_bm}_{label_id_person}_[]"
    item_ids = generate_data(
        dbh=dbh,
        project_id=p_info["project_id"],
        user_id = users["superman"],
        bought_for_id = users["batman"],
        names=grocery_store_names,
        labels=llb,
        start_date_str=start_date_str,
        currency="USD",
        poisson_exp=0.5,
        avg_weekly_spend=2.0,
        max_weekly_spend=5.0
    )
    print(f"ID: ({label_id_person}), generating sample data Clark for Batman: {len(item_ids)}")


def generate_income_data(dbh, users, start_date_str="2024-11-01"):
    """
    Generate monthly income streams for Batman and Superman.

    Batman receives:
    - Wayne Enterprises income on the 25th of each month
    - Inheritance income on the 26th of each month

    Superman receives:
    - Daily Planet Income on the 26th of each month

    Income is generated from November 2024 to today (March 2026).
    Note: Income transactions are NEGATIVE (bought_for gets money, so price is negative).
    """
    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]
    print(p_info)

    # Get label IDs for income sources
    label_id_revenue = dbh.op_label_get_by_name("revenue", p_info["project_id"])
    label_id_fixed = dbh.op_label_get_by_name("fixed", p_info["project_id"])

    label_id_person = dbh.op_label_get_by_name("Wages", p_info["project_id"])

    label_id_income_bm1 = dbh.op_label_get_by_name("Wayne Enterprises", p_info["project_id"])
    label_id_income_bm2 = dbh.op_label_get_by_name("Inheritance", p_info["project_id"])
    label_id_income_sm1 = dbh.op_label_get_by_name("Daily Planet Income", p_info["project_id"])

    label_id_liability_bm = dbh.op_label_get_by_name("Liability Account Batman", p_info["project_id"])
    label_id_liability_sm = dbh.op_label_get_by_name("Liability Account Superman", p_info["project_id"])

    # Define start and end dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.now()

    # Generate list of months to process
    current_date = start_date
    created_items = []

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month

        # Batman: Wayne Enterprises income on the 25th
        income_date_bm1 = datetime(year, month, 25, 9, 0, 0)  # 9 AM
        if income_date_bm1 <= end_date:
            llb = f"{label_id_revenue}_{label_id_fixed}_{label_id_income_bm1}_{label_id_person}_[]"
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Wayne Enterprises Monthly Income",
                "note": f"Monthly salary/dividend from Wayne Enterprises - {year}-{month:02d}",
                "price": 15000.00,  # Negative for income
                "price_final": 15000.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": income_date_bm1.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["batman"],
                "bought_for_id": users["batman"],
                "added_by_id": users["batman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": income_date_bm1.strftime("%Y-%m-%d"),
                "tags": llb
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Wayne Enterprises income for {year}-{month:02d}: {e}")

        # Batman: Inheritance income on the 26th
        income_date_bm2 = datetime(year, month, 26, 10, 0, 0)  # 10 AM
        if income_date_bm2 <= end_date:
            llb = f"{label_id_revenue}_{label_id_fixed}_{label_id_income_bm2}_{label_id_person}_[]"
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Inheritance Monthly Distribution",
                "note": f"Monthly trust fund distribution - {year}-{month:02d}",
                "price": 8000.00,  # Negative for income
                "price_final": 8000.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": income_date_bm2.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["batman"],
                "bought_for_id": users["batman"],
                "added_by_id": users["batman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": income_date_bm2.strftime("%Y-%m-%d"),
                "tags": llb
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Inheritance income for {year}-{month:02d}: {e}")

        # Superman: Daily Planet income on the 26th
        income_date_sm = datetime(year, month, 26, 15, 0, 0)  # 3 PM
        if income_date_sm <= end_date:
            llb = f"{label_id_revenue}_{label_id_fixed}_{label_id_income_sm1}_{label_id_person}_[]"
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Daily Planet Monthly Salary",
                "note": f"Journalist salary - {year}-{month:02d}",
                "price": 5500.00,  # Negative for income
                "price_final": 5500.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": income_date_sm.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["superman"],
                "bought_for_id": users["superman"],
                "added_by_id": users["superman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": income_date_sm.strftime("%Y-%m-%d"),
                "tags": llb
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Daily Planet income for {year}-{month:02d}: {e}")

        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)

    print(f"✓ Generated {len(created_items)} income transactions for Batman and Superman")
    print(f"  - Batman: Wayne Enterprises + Inheritance (2 per month)")
    print(f"  - Superman: Daily Planet (1 per month)")
    print(f"  - Period: 2024-11-01 to {end_date.strftime('%Y-%m-%d')}")


def generate_savings_data(dbh, users):
    """
    Generate monthly savings transactions for Batman and Superman.

    Both users responsibly put money aside after receiving their income.
    Savings are deposited on the 27th of each month (after income on 25th/26th).

    Batman saves to:
    - BM: Savings Account I (primary savings)
    - BM: Savings Account II (emergency fund)

    Superman saves to:
    - SM: Savings Account I (primary savings)
    - SM: Savings Account II (emergency fund)

    Savings are generated from November 2024 to today (March 2026).
    Note: Savings are expenses (money going out), so prices are POSITIVE.
    """
    p_info = dbh.op_project_get_info(user_id=users["batman"])
    p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]

    # Get label IDs for savings accounts
    label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])
    label_id_fixed = dbh.op_label_get_by_name("fixed", p_info["project_id"])

    label_id_savings_bm1 = dbh.op_label_get_by_name("BM: Savings Account I", p_info["project_id"])
    label_id_savings_bm2 = dbh.op_label_get_by_name("BM: Savings Account II", p_info["project_id"])
    label_id_savings_sm1 = dbh.op_label_get_by_name("SM: Savings Account I", p_info["project_id"])
    label_id_savings_sm2 = dbh.op_label_get_by_name("SM: Savings Account II", p_info["project_id"])

    label_id_liability_bm = dbh.op_label_get_by_name("Liability Account Batman", p_info["project_id"])
    label_id_liability_sm = dbh.op_label_get_by_name("Liability Account Superman", p_info["project_id"])

    # Define start and end dates
    start_date = datetime(2024, 11, 1)
    end_date = datetime.now()

    # Generate list of months to process
    current_date = start_date
    created_items = []

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month

        # Savings happen on the 27th (after income on 25th/26th)
        savings_date = datetime(year, month, 27, 14, 0, 0)  # 2 PM

        # Only create savings if the 27th is not in the future
        if savings_date <= end_date:
            # Batman: Savings Account I (primary - 20% of income)
            # Batman's monthly income: $23,000, so 20% = $4,600
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Monthly Savings Transfer - Primary",
                "note": f"Regular savings deposit to Account I - {year}-{month:02d}",
                "price": 4600.00,  # Positive for expense (money going out)
                "price_final": 4600.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": savings_date.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["batman"],
                "bought_for_id": users["batman"],
                "added_by_id": users["batman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": savings_date.strftime("%Y-%m-%d"),
                "tags": json.dumps([label_id_savings_bm1, label_id_expenses,
                                    label_id_fixed])
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Batman Savings I for {year}-{month:02d}: {e}")

            # Batman: Savings Account II (emergency fund - 10% of income)
            # 10% of $23,000 = $2,300
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Monthly Savings Transfer - Emergency Fund",
                "note": f"Emergency fund deposit to Account II - {year}-{month:02d}",
                "price": 2300.00,  # Positive for expense
                "price_final": 2300.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": savings_date.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["batman"],
                "bought_for_id": users["batman"],
                "added_by_id": users["batman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": savings_date.strftime("%Y-%m-%d"),
                "tags": json.dumps([label_id_savings_bm2, label_id_expenses,
                                   label_id_fixed])
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Batman Savings II for {year}-{month:02d}: {e}")

            # Superman: Savings Account I (primary - 15% of income)
            # Superman's monthly income: $5,500, so 15% = $825
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Monthly Savings Transfer - Primary",
                "note": f"Regular savings deposit to Account I - {year}-{month:02d}",
                "price": 825.00,  # Positive for expense
                "price_final": 825.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": savings_date.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["superman"],
                "bought_for_id": users["superman"],
                "added_by_id": users["superman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": savings_date.strftime("%Y-%m-%d"),
                "tags": json.dumps([label_id_savings_sm1, label_id_expenses,
                                   label_id_fixed])
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Superman Savings I for {year}-{month:02d}: {e}")

            # Superman: Savings Account II (emergency fund - 10% of income)
            # 10% of $5,500 = $550
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": "Monthly Savings Transfer - Emergency Fund",
                "note": f"Emergency fund deposit to Account II - {year}-{month:02d}",
                "price": 550.00,  # Positive for expense
                "price_final": 550.00,
                "currency": "USD",
                "currency_final": "USD",
                "bought_date": savings_date.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": users["superman"],
                "bought_for_id": users["superman"],
                "added_by_id": users["superman"],
                "project_id": p_info["project_id"],
                "exchange_rate": 1.0,
                "exchange_rate_date": savings_date.strftime("%Y-%m-%d"),
                "tags": json.dumps([label_id_savings_sm2, label_id_expenses,
                                   label_id_fixed])
            }
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create Superman Savings II for {year}-{month:02d}: {e}")

        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)

    print(f"✓ Generated {len(created_items)} savings transactions for Batman and Superman")
    print(f"  - Batman: 30% of income → Savings I ($4,600) + Savings II ($2,300) = $6,900/month")
    print(f"  - Superman: 25% of income → Savings I ($825) + Savings II ($550) = $1,375/month")
    print(f"  - Total monthly savings: $8,275")
    print(f"  - Period: 2024-11-01 to {end_date.strftime('%Y-%m-%d')}")

