import sqlite3
from datetime import datetime


# =========================================================
# DATABASE
# =========================================================

DATABASE = "shamba_advisor.db"


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT UNIQUE NOT NULL,

            location TEXT,

            farm_size TEXT,

            crops TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
    """)


    connection.commit()

    connection.close()


# =========================================================
# GET FARMER
# =========================================================

def get_farmer(name):

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            location,
            farm_size,
            crops,
            created_at,
            updated_at

        FROM farmers

        WHERE LOWER(name) = LOWER(?)
    """, (name,))


    row = cursor.fetchone()

    connection.close()


    if row is None:

        return None


    return {

        "id": row[0],

        "name": row[1],

        "location": row[2],

        "farm_size": row[3],

        "crops": row[4],

        "created_at": row[5],

        "updated_at": row[6]
    }


# =========================================================
# CREATE FARMER
# =========================================================

def create_farmer(name):

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    now = datetime.now().isoformat()


    cursor.execute("""
        INSERT INTO farmers (
            name,
            location,
            farm_size,
            crops,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        None,
        None,
        None,
        now,
        now
    ))


    connection.commit()

    connection.close()


    return get_farmer(name)


# =========================================================
# GET OR CREATE FARMER
# =========================================================

def get_or_create_farmer(name):

    farmer = get_farmer(name)


    if farmer:

        return farmer


    return create_farmer(name)


# =========================================================
# UPDATE FARMER PROFILE
# =========================================================

def update_farmer_profile(
    name,
    location=None,
    farm_size=None,
    crop=None
):

    farmer = get_farmer(name)


    if farmer is None:

        create_farmer(name)

        farmer = get_farmer(name)


    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    new_location = (

        location

        if location

        else farmer["location"]
    )


    # -----------------------------------------------------
    # FARM SIZE
    # -----------------------------------------------------

    new_farm_size = (

        farm_size

        if farm_size

        else farmer["farm_size"]
    )


    # -----------------------------------------------------
    # CROPS
    # -----------------------------------------------------

    existing_crops = farmer["crops"]


    crop_list = []


    if existing_crops:

        crop_list = [

            item.strip()

            for item in existing_crops.split(",")

            if item.strip()
        ]


    if crop:

        already_exists = any(

            item.lower() == crop.lower()

            for item in crop_list
        )


        if not already_exists:

            crop_list.append(crop)


    new_crops = ", ".join(
        crop_list
    )


    # -----------------------------------------------------
    # SAVE CHANGES
    # -----------------------------------------------------

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    now = datetime.now().isoformat()


    cursor.execute("""
        UPDATE farmers

        SET
            location = ?,
            farm_size = ?,
            crops = ?,
            updated_at = ?

        WHERE LOWER(name) = LOWER(?)
    """, (
        new_location,
        new_farm_size,
        new_crops or None,
        now,
        name
    ))


    connection.commit()

    connection.close()


    return get_farmer(name)


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    create_database()


    farmer = get_or_create_farmer(
        "John"
    )


    print()
    print("Farmer profile:")
    print(farmer)


    farmer = update_farmer_profile(

        "John",

        location="Nairobi",

        farm_size="2 acres",

        crop="maize"
    )


    print()
    print("Updated profile:")
    print(farmer)