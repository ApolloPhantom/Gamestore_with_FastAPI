import sqlite3
import os.path
import random
import re 


base = os.path.dirname(os.path.abspath(__file__))
db = "project.db"
db_path = os.path.join(base,db)

def login_checker(user):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select id from users where id = ?",(user,))
    r = cur.fetchall()
    conn.close()
    if r == []:
        return False
    else:
        return True

def login_verifier(username,password):
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
    cur.execute("Insert into users values(?,?,?,?)",(Id,username,password,ran,))
    cur.execute("Insert into user_store values(?,?,?)",(Id,0,0,))
    conn.commit()
    conn.close()
    return error

def listed_object_data_generator(object_type):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select * from object where Object_type = ? and listing = ?",(object_type,"L",))
    r = cur.fetchall()
    conn.close()
    return r


def object_unlister_and_cart_filler(ObjectID,Buyer_ID):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Id from object_user where Object_ID = ?",(ObjectID,))
    r = cur.fetchall()
    Seller_ID = r[0][0]
    if Seller_ID == Buyer_ID:
        conn.close()
        return False
    cur.execute("update object set listing = ? where Object_ID = ?",("UL",ObjectID,) )
    conn.commit()
    cur.execute("select Transaction_ID from cart")
    r = cur.fetchall()
    T_ID = 0
    if r == []:
        T_ID = 1
    else:
        T_ID = r[-1][0] + 1
    cur.execute("insert into cart values(?,?,?,?,?)",(T_ID,Buyer_ID,Seller_ID,ObjectID,"N",))
    conn.commit()
    conn.close()
    return True

def cart_lister(Buyer_ID):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Object_ID from cart where Buyer_ID = ? and Purchase_Status = ?",(Buyer_ID,"N",))
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
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("L",Object_ID,))
    conn.commit()
    cur.execute("delete from cart where Object_ID = ?",(Object_ID,))
    conn.commit()
    conn.close()
    



    
def bank_confirm(accountid):
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
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Funds,Gold from user_store where Id = ?",(Id,))
    r = cur.fetchall()
    return [r[0][0],r[0][1]]


def password_verifier(Id,password):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select * from users where Id = ? and Password = ?",(Id,password,))
    r = cur.fetchall()
    if r==[]:
        return False
    conn.close()    
    return True

def password_modifier(Id,password):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update users set Password = ? where Id = ?",(password,Id,))
    cur.commit()
    conn.close()
    

def gold_extractor(Id,gold):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("select Funds from user_store where ID = ?",(Id,))
    r = cur.fetchall()
    F = r[0][0]
    F = F - gold
    cur.execute("update user_store set Funds = ? where ID = ?",(F,Id,))
    conn.commit()
    cur.execute("update user_store set Gold = ? where ID = ?",(gold*2000,Id,))
    conn.commit()
    conn.close()
    
def purchase(user,items,update_G):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update user_store set Gold = ? where ID = ?",(update_G,user,))
    conn.commit()
    for i in items:
        cur.execute("update object_user set Id = ? where Object_ID = ?",(user,i[0],))
        conn.commit()
        cur.execute("update object set listing = ? where Object_ID = ?",("UL",user,))
        conn.commit()
        cur.execute("update cart set Purchase_Status = ? where Buyer_Id = ? and Object_ID = ?",("Y",user,i[0],))
        conn.commit()
    
    conn.close()
    
def my_unlisted_objects(user):
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
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("L",ID,))
    conn.commit()

def unlister_pro_max(ID):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("update object set listing = ? where Object_ID = ?",("UL",ID,))
    conn.commit()
       
    
    
    

    
    
    
    
    
    
    

    
    
    