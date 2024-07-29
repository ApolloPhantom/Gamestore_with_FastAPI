import sqlite3
import os.path
import random
import re 
from datetime import datetime , timedelta
from typing import List, Dict, Any

base = os.path.dirname(os.path.abspath(__file__))
db = "project.db"
db_path = os.path.join(base,db)

# def login_checker(user):
#     conn = sqlite3.connect(db_path)
#     cur = conn.cursor()
#     cur.execute("select id from users where id = ?",(user,))
#     r = cur.fetchall()
#     conn.close()
#     if r == []:
#         return False
#     else:
#         return True


def login_verifier(username,password):
    # Verifies if the provoded username and password are presrent in database
    # Returns user id if credentials are correct, otherwise None.
    # Error handling for empty username and password.
    if username == "" or password == "":
        return None
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("select id from users where Name = ? and Password = ?",(username,password,))
    r = cur.fetchall()
    con.close()
    if r == []:
        return None
    else:
        return r[0][0]

    
def register_helper(username,password,confirmation):
    # Helper function to register user
    # Returns error message or empty string
    error = ""
    if username == "":
        error = "Username Field is empty."
        return error
    if password == "":
        error = "Password field is empty."
        return error
    
    if len(password) >20:
        error = "Password must not exceed 20 characters."
        return error
    
    if confirmation == "":
        error = "You must confirm password."
        return error
    
    if len(password) != len(confirmation):
        error = "Passwword and confirmations must have same length."
        return error
    if password != confirmation:
        error = "Password and confirmation doesnot match."
        return error
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Name from users where Name = ?",(username,))
    r = cur.fetchall()
    if len(r) > 0:
        error = "Username already exists"
        return error
    cur.execute("select Id from users")
    r = cur.fetchall()
    Id = r[-1][0] + 1
    ran = 0 
    while(True):
        ran = random.randint(0,10000)
        cur.execute("select Recovery from users where Recovery = ?",(ran,))
        q = cur.fetchall()
        if len(q) == 0:
            break
    cur.execute("Insert into users values(?,?,?,?,?,?)",(Id,username,password,ran,"","",))
    cur.execute("Insert into user_store values(?,?,?)",(Id,0,10000,))
    conn.commit()
    conn.close()
    return error

def listed_object_data_generator(object_type):
    # Outputs all objects with listing set to "L"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select * from object where Object_type = ? and listing = ?",(object_type,"L",))
    r = cur.fetchall()
    conn.close()
    return r


def object_unlister_and_cart_filler(ObjectID,Buyer_ID):
    # function to handle carting operations
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Id from object_user where Object_ID = ?",(ObjectID,))
    r = cur.fetchall()
    Seller_ID = r[0][0]
    cur.execute("select price from object where Object_ID = ?",(ObjectID,))
    r = cur.fetchall()
    price = r[0][0]
    if Seller_ID == Buyer_ID:
        conn.close()
        return 0
    
    T_ID = 1
    cur.execute("select min(Transaction_ID) from transactions")
    l = cur.fetchone()
    if l is None:
        T_ID = 1
    else:
        l = l[0]
    cur.execute("select max(Transaction_ID) from transactions")
    r = cur.fetchone()
    if r is None:
        T_ID = 1
    else:
        r = r[0]
    
    if l==None or r==None:
        pass
    else:
        T_ID = r+1
        if l > 1: 
            T_ID = l-1
    
    try:
        cur.execute("insert into content values(?,?,?,?,?)",(ObjectID,Buyer_ID,Seller_ID,T_ID,price,))
        cur.execute("update object set listing = ? where Object_ID = ?",("UL",ObjectID,) )
    except:
        conn.rollback()
        conn.close()
        return 1
    
    conn.commit()
    conn.close()
    return 2

def cart_lister(Buyer_ID):
    # Outputs items currently carted by buyer
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Object_ID from content where Buyer_ID = ? ",(Buyer_ID,))
    O_ID = []
    r = cur.fetchall()
    for i in r:
        O_ID.append(i[0])
    
    items = []
    for i in O_ID:
        cur.execute("select * from object where Object_ID = ? and listing = ?",(i,"UL",))
        r = cur.fetchall()
        items.append(r[0])
    
    return items

def total_price(items):
    p = 0
    for i in items:
        p += i[-2]
    return p

def uncarter(Object_ID):
    # uncarts object from cart
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("L",Object_ID,))
    conn.commit()
    cur.execute("delete from content where Object_ID = ?",(Object_ID,))
    conn.commit()
    conn.close()
    


    
def bank_confirm(accountid):
    # confirmation function for bank confirmation
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    pattern = re.compile(r'\d{4}-\d{4}-\d{4}-\d{4}$')
    if pattern.match(accountid) == None:
        return False
    
    cur.execute("select * from user_bank where Acc_ID = ?",(accountid,))
    r = cur.fetchall()
    if r == []:
        return False
    
    conn.close()
    return True

def bank_withdrawer(user,accountid,password,amount):
    # function to withdraw funds from bank
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select USD from user_bank where Acc_ID = ? and Acc_Password = ?",(accountid,password,))
    r = cur.fetchall()
    if r == []:
        return False
    U = r[0][0]
    if U<amount:
        return False
    else:
        cur.execute("update user_bank set USD = ? where Acc_ID = ?",(U-amount,accountid,))
        conn.commit()
        cur.execute("update user_store set Funds = ? where ID = ?",(amount,user,))
        conn.commit()
        conn.close()
        return True

def balance_checker(Id):
    # generates user store balance
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Funds,Gold from user_store where Id = ?",(Id,))
    r = cur.fetchall()
    return r


def password_verifier(Id,password):
    # password verification for the user
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select * from users where Id = ? and Password = ?",(Id,password,))
    r = cur.fetchall()
    if r==[]:
        return False
    conn.close()    
    return True

def password_modifier(Id,password):
    # password_modifier
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update users set Password = ? where Id = ?",(password,Id,))
    cur.commit()
    conn.close()
    

def gold_extractor(Id,gold,modifier):
    # gold extracter function
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Funds from user_store where ID = ?",(Id,))
    r = cur.fetchall()
    F = r[0][0]
    F = F - gold
    cur.execute("update user_store set Funds = ? where ID = ?",(F,Id,))
    conn.commit()
    cur.execute("update user_store set Gold = ? where ID = ?",(gold*modifier,Id,))
    conn.commit()
    conn.close()
    
def purchase(user,items,update_G):
    # buy items from cart
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    purchase_date = datetime.now().strftime("%Y-%m-%d")
    T_ID = 1
    cur.execute("select min(Transaction_ID) from transactions")
    l = cur.fetchone()
    if l is None:
        T_ID = 1
    else:
        l = l[0]
    cur.execute("select max(Transaction_ID) from transactions")
    r = cur.fetchone()
    if r is None:
        T_ID = 1
    else:
        r = r[0]
    
    if l==None or r==None:
        pass
    else:
        T_ID = r+1
        if l > 1: 
            T_ID = l-1
    
    totalprice = total_price(items)
    try:
        cur.execute("insert into transaction values(?,?,?)",(T_ID,totalprice,purchase_date,))
    except:
        conn.rollback()
        return False
    try:
        cur.execute("update user_store set Gold = ? where ID = ?",(update_G,user,))
    except:
        conn.rollback()
        return False
    
    try:
        for i in items:
            cur.execute("update object_user set Id = ? where Object_ID = ?",(user,i[0],))
            cur.execute("update object set listing = ? where Object_ID = ?",("UL",user,))
            cur.execute("delete from content where Buyer_Id = ? and Object_ID = ?",(user,i[0],))
    except:
        conn.rollback()
        return False
    
    conn.commit()
    conn.close()
    return True
    
def my_unlisted_objects(user):
    # shows objects in possession
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Object_ID from object_user where Id = ?",(user,))
    r = cur.fetchall()
    L = []
    for i in r:
        cur.execute("select * from object where Object_ID = ?",(i[0],))
        p = cur.fetchall()
        if p != []:
            L.append(p[0])
    
    conn.close()
    return L

def lister_pro_max(ID):
    # sets object to listing stat
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("L",ID,))
    conn.commit()

def unlister_pro_max(ID):
    # unlists object 
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("UL",ID,))
    conn.commit()


# def generate_objects(count):
#     # generator function for objects
#     object_types = ["sword", "axe", "scythe", "shield", "pickaxe", "spear", "potions", "books", "ingredients"]
#     ratings = ["S", "A", "B", "C", "D"]
#     adjectives = [
#         "Mighty", "Ancient", "Shiny", "Mystic", "Enchanted", "Legendary", "Cursed", "Divine", "Forgotten", 
#         "Arcane", "Vengeful", "Sacred", "Ethereal", "Infernal", "Blessed", "Demonic", "Mythical", "Phantom", 
#         "Celestial", "Shadowed", "Radiant", "Stormforged", "Ironclad", "Crystalline", "Eldritch", "Gilded", 
#         "Frostbitten", "Bloodthirsty", "Spectral"
#     ]
#     nouns = [
#         "Blade", "Protector", "Reaper", "Defender", "Miner", "Hunter", "Elixir", "Tome", "Component", "Amulet", 
#         "Ring", "Staff", "Cloak", "Gauntlet", "Shield", "Helm", "Armor", "Potion", "Relic", "Scepter", 
#         "Sword", "Bow", "Spear", "Dagger", "Orb", "Grimoire", "Phylactery", "Chalice", "Crown", "Scroll"
#     ]
    
#     # Define the probabilities for each rating
#     rating_probabilities = [0.01, 0.05, 0.1, 0.25, 0.50]  # S, A, B, C, D

#     objects = []
#     for i in range(count):
#         object_id = i + 1
#         object_name = f"{random.choice(adjectives)} {random.choice(nouns)}"
#         object_type = random.choice(object_types)
#         object_name += " " + object_type
#         listing = "UL"
        
#         # Choose a rating based on the defined probabilities
#         rating = random.choices(ratings, weights=rating_probabilities, k=1)[0]

#         price_ranges = {
#             "S": (20000000, 10000000),
#             "A": (9999999, 5000000),
#             "B": (4999999, 1000000),
#             "C": (999999, 500000),
#             "D": (499999, 2000)
#         }
#         p = price_ranges[rating]
#         price = random.randint(p[1], p[0])
        
#         obj = {
#             "Object_ID": object_id,
#             "Object_Name": object_name,
#             "Object_Type": object_type,
#             "Listing": listing,
#             "Rating": rating,
#             "Price": price
#         }
#         objects.append(obj)
    
#     return objects


# def insert_object_and_user(obj, user_id):
#     # objects are created and inserted to the database
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT 1 FROM object WHERE Object_ID = ?", (obj["Object_ID"],))
#     if cursor.fetchone() is not None:
#         cursor.execute("select max(Object_ID) from object")
#         r = cursor.fetchone()
#         cursor.execute("select min(Object_ID) from object")
#         l = cursor.fetchone()
#         if l[0]>1:
#             obj["Object_ID"] = l[0]-1
#         else:        
#             obj["Object_ID"] = r[0]+1
    
    
            
#     cursor.execute(
#         "INSERT INTO object (Object_ID, Object_Name, Object_type, listing, rating, price) VALUES (?, ?, ?, ?, ?, ?)",
#         (obj["Object_ID"], obj["Object_Name"], obj["Object_Type"], obj["Listing"], obj["Rating"], obj["Price"])
#     )
#     cursor.execute(
#         "INSERT INTO object_user (Object_ID, Id) VALUES (?, ?)",
#         (obj["Object_ID"], user_id)
#     )

#     conn.commit()
#     conn.close()

def mean_gold():
    # mean gold
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(price) FROM object")
    r = cursor.fetchone()
    r =  r[0]//100
    r = int(r)
    return r

def purger(Object_Id,ID):
    # sets object possession back to admin
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM object where Object_ID = ? and listing = ?",(Object_Id,"UL",))
    l = cursor.fetchone()
    cursor.execute("SELECT * from object_user where Object_ID = ? and Id = ?",(Object_Id,ID,))
    r = cursor.fetchone()
    if len(l) == 0:
        return False
    if len(r) == 0:
        return False
    price = l[0]
    cursor.execute("update object_user set listing = ? where Object_ID = ? and Id = ?",("UL",Object_Id,ID,))
    cursor.execute("update object set Id = ? where Object_ID = ?",(1,Object_Id,))
    cursor.execute("update user_store set Gold = (Gold + ((?)*(0.2))) where ID = ?",(price,ID,))
    conn.commit()
    conn.close()
    return True


def get_db_connection():
    conn = sqlite3.connect(db_path)
    return conn

def execute_sql_command(command):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(command)
        conn.commit()
        if cursor.description:
            result = cursor.fetchall()
            conn.close()
            return {"status": "success", "result": [dict(row) for row in result]}
        else:
            conn.close()
            return {"status": "success", "result": "Command executed successfully"}
    except Exception as e:
        conn.close()
        return {"status": "error", "result": str(e)}

def get_category_count_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Object_type, COUNT(*) as count FROM object GROUP BY Object_type')
    data = cursor.fetchall()
    conn.close()
    return data

def get_cumulative_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Purchase_Date, Total_Price FROM transactions ORDER BY Purchase_Date')
    data = cursor.fetchall()
    conn.close()
    return data

def get_last7days_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    seven_days_ago = datetime.now() - timedelta(days=7)
    cursor.execute('SELECT Purchase_Date, Total_Price FROM transactions WHERE Purchase_Date >= ?', (seven_days_ago,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_connection():
    return sqlite3.connect(db_path)

def insert_object_and_user(obj, user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM object WHERE Object_ID = ?", (obj["Object_ID"],))
        if cursor.fetchone() is not None:
            cursor.execute("SELECT max(Object_ID) FROM object")
            r = cursor.fetchone()
            cursor.execute("SELECT min(Object_ID) FROM object")
            l = cursor.fetchone()
            if l[0] > 1:
                obj["Object_ID"] = l[0] - 1
            else:
                obj["Object_ID"] = r[0] + 1

        cursor.execute(
            "INSERT INTO object (Object_ID, Object_Name, Object_type, listing, rating, price) VALUES (?, ?, ?, ?, ?, ?)",
            (obj["Object_ID"], obj["Object_Name"], obj["Object_type"], obj["listing"], obj["rating"], obj["price"])
        )
        cursor.execute(
            "INSERT INTO object_user (Object_ID, Id) VALUES (?, ?)",
            (obj["Object_ID"], user_id)
        )

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def generate_objects(count):
    # generator function for objects
    object_types = ["sword", "axe", "scythe", "shield", "pickaxe", "spear", "potions", "books", "ingredients"]
    ratings = ["S", "A", "B", "C", "D"]
    adjectives = [
        "Mighty", "Ancient", "Shiny", "Mystic", "Enchanted", "Legendary", "Cursed", "Divine", "Forgotten",
        "Arcane", "Vengeful", "Sacred", "Ethereal", "Infernal", "Blessed", "Demonic", "Mythical", "Phantom",
        "Celestial", "Shadowed", "Radiant", "Stormforged", "Ironclad", "Crystalline", "Eldritch", "Gilded",
        "Frostbitten", "Bloodthirsty", "Spectral"
    ]
    nouns = [
        "Blade", "Protector", "Reaper", "Defender", "Miner", "Hunter", "Elixir", "Tome", "Component", "Amulet",
        "Ring", "Staff", "Cloak", "Gauntlet", "Shield", "Helm", "Armor", "Potion", "Relic", "Scepter",
        "Sword", "Bow", "Spear", "Dagger", "Orb", "Grimoire", "Phylactery", "Chalice", "Crown", "Scroll"
    ]

    # Define the probabilities for each rating
    rating_probabilities = [0.01, 0.05, 0.1, 0.25, 0.50]  # S, A, B, C, D

    objects = []
    for i in range(count):
        object_id = i + 1
        object_name = f"{random.choice(adjectives)} {random.choice(nouns)}"
        object_type = random.choice(object_types)
        object_name += " " + object_type
        listing = "UL"

        # Choose a rating based on the defined probabilities
        rating = random.choices(ratings, weights=rating_probabilities, k=1)[0]

        price_ranges = {
            "S": (20000000, 10000000),
            "A": (9999999, 5000000),
            "B": (4999999, 1000000),
            "C": (999999, 500000),
            "D": (499999, 2000)
        }
        p = price_ranges[rating]
        price = random.randint(p[1], p[0])

        obj = {
            "Object_ID": object_id,
            "Object_Name": object_name,
            "Object_Type": object_type,
            "Listing": listing,
            "Rating": rating,
            "Price": price
        }
        objects.append(obj)

    return objects



def get_items_per_rating_data():
    query = """
    SELECT rating, COUNT(*) as count
    FROM object
    GROUP BY rating
    """
    return execute_sql_query(query)

def get_avg_price_per_rating_data():
    query = """
    SELECT rating, AVG(price) as avg_price
    FROM object
    GROUP BY rating
    """
    return execute_sql_query(query)

def get_avg_price_per_category_data():
    query = """
    SELECT Object_type, AVG(price) as avg_price
    FROM object
    GROUP BY Object_type
    """
    return execute_sql_query(query)

def get_player_wealth_leaderboard_data():
    query = """
    SELECT users.Name, (user_store.Funds + user_store.Gold) as wealth
    FROM users
    JOIN user_store ON users.Id = user_store.ID
    ORDER BY wealth DESC
    """
    return execute_sql_query(query)


def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(db_path) 
        cursor = conn.cursor()
        cursor.execute(query)
        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in rows]
        cursor.close()
        conn.close()
        return result

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return ["Error"]
    except Exception as e:
        print(f"Error: {e}")
        return ["Error"]

def execute(command):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(command)
    res = cursor.fetchall()
    conn.commit()  # Ensure any changes made by the command are saved
    cursor.close()
    conn.close()
    return  res
