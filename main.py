import os
from fastapi import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from complementary.sql_connectors import *
from functools import wraps


base_path = os.path.dirname(os.path.abspath(__file__))
stat = "static"
stat_path = os.path.join(base_path,stat) 
app = FastAPI()
app.mount("/static", StaticFiles(directory=stat_path), name="static")
templates = Jinja2Templates(directory="templates")
user = None  #contains an integer ID


@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    
    return response


def login_required(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        global user
        if  login_checker(user) == False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not logged in"
            )
        return await f(*args, **kwargs)
    return wrapper

@app.get("/",response_class=HTMLResponse)
async def home(request : Request):
    return templates.TemplateResponse("home.html",{"request":request,"user":user})


@app.get("/login")
async def login_get(request : Request):
    prompt = 0
    return templates.TemplateResponse("login.html",{"request":request,"prompt":prompt})

@app.post("/login")
async def login_post(request : Request,username : str = Form(), password : str = Form()):
    u = login_verifier(username,password)
    if u == None:
        prompt = 1
        er = "You have given credentials or user does not exist"
        return templates.TemplateResponse("login.html",{"request":request,"prompt":prompt,"Error":er,"user":None})
    else:
        global user
        user = u
        return templates.TemplateResponse("home.html",{"request":request,"user":user})
    
@app.get("/logout")
async def logout(request : Request):
    global user
    user = None
    return RedirectResponse(url="/")


@app.get("/register")
async def reg_get(request : Request):
    
    return templates.TemplateResponse("register.html",{"request":request,"prompt":0,"user":user})

@app.post("/register")
async def reg_get(request : Request,username : str = Form(), password : str = Form(),confirmation : str = Form()):
    er = register_helper(username,password,confirmation)
    global user
    user = login_verifier(username,password)
    if len(er) != 0:
        return templates.TemplateResponse("register.html",{"request":request,"prompt":2,"Error":er,"user":user})
    else:
        return templates.TemplateResponse("home.html",{"request":request,"user":user})
        
        
@app.get("/sword")
@login_required
async def sword(request : Request):
    items = listed_object_data_generator("Sword")
    return templates.TemplateResponse("sword.html",{"request":request,"items":items,"user":user})

@app.get("/axe")
@login_required
async def axe(request : Request):
    items = listed_object_data_generator("Axe")
    return templates.TemplateResponse("axe.html",{"request":request,"items":items,"user":user})

@app.get("/scythe")
@login_required
async def scythe(request : Request):
    items = listed_object_data_generator("Scythe")
    return templates.TemplateResponse("scythe.html",{"request":request,"items":items,"user":user})

@app.get("/shield")
@login_required
async def shield(request : Request):
    items = listed_object_data_generator("Shield")
    return templates.TemplateResponse("shield.html",{"request":request,"items":items,"user":user})

@app.get("/pickaxe")
@login_required
async def pickaxe(request : Request):
    items = listed_object_data_generator("Pickaxe")
    return templates.TemplateResponse("pickaxe.html",{"request":request,"items":items,"user":user})

@app.get("/spear")
@login_required
async def spear(request : Request):
    items = listed_object_data_generator("Spear")
    return templates.TemplateResponse("spear.html",{"request":request,"items":items,"user":user})

@app.get("/potions")
@login_required
async def potions(request : Request):
    items = listed_object_data_generator("Potions")
    return templates.TemplateResponse("potions.html",{"request":request,"items":items,"user":user})

@app.get("/books")
@login_required
async def sword(request : Request):
    items = listed_object_data_generator("Books")
    return templates.TemplateResponse("books.html",{"request":request,"items":items,"user":user})

@app.get("/ingredients")
@login_required
async def ingredients(request : Request):
    items = listed_object_data_generator("Ingredients")
    return templates.TemplateResponse("ingredients.html",{"request":request,"items":items,"user":user})

@app.get("/CCart/{ID}/{Type}")
@login_required
async def object_cart(request : Request, ID : int,Type : str):
    global user
    t = object_unlister_and_cart_filler(ID,user)
    if t == False:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You cannot buy your own item."
            ) 
    items = listed_object_data_generator(Type)
    return templates.TemplateResponse(Type.lower() + ".html",{"request":request,"items":items,"user":user})

@app.get("/cart")
@login_required
async def cart(request : Request):
    global user
    items = cart_lister(user)
    price_G = total_price(items)
    price = price_G//2000    
    return templates.TemplateResponse("cart.html",{"request":request,"items":items,"user":user,"cash":price,"cashg":price_G})


@app.post("/uncart",response_class= HTMLResponse)
@login_required
async def uncart(request : Request,ID : int = Form() , Type : str =  Form()):
    uncarter(ID)
    global user
    items = cart_lister(user)
    price_G = total_price(items)
    price = price_G//2000
    er = "Uncarted Successfully"    
    return templates.TemplateResponse("cart.html",{"request":request,"items":items,"user":user,"cash":price,"cashG":price_G,"prompt":2,"Error":er})
    

@app.post("/buy",response_class=HTMLResponse)
@login_required
async def buy(request : Request,accountid : str = Form(),password : str = Form(),confirmation : str = Form(),amount : int = Form()):
    global user
    if bank_confirm(accountid) == False:
        er = "Wrong Account ID or Account does not exist"
        return templates.TemplateResponse("buy.html",{"request":request,"user":user,"prompt":1,"Error":er})
    
    if bank_withdrawer(user,accountid,password,amount) == False:
         er = "Insufficient money in your account"
         return templates.TemplateResponse("buy.html",{"request":request,"user":user,"prompt":1,"Error":er})
    else:
        er = "Funds added , go to balance to check"
        return templates.TemplateResponse("buy.html",{"request":request,"user":user,"prompt":2,"Error":er})

@app.get("/buy",response_class=HTMLResponse)
@login_required
async def buy_g(request : Request):
    global user
    return templates.TemplateResponse("buy.html",{"request":request,"user":user,"prompt":0})
    

@app.get("/balance")
@login_required
async def balance(request : Request):
    global user
    L = balance_checker(user)
    return templates.TemplateResponse("balance.html",{"request":request,"user":user,"cash":L[0],"cashG":L[1]})


@app.post("/changepassword",response_class=HTMLResponse)
@login_required
async def changepassword(request : Request,cpassword : str = Form(),password : str = Form(),confirmation : str = Form()):
    global user
    if password_verifier(user,cpassword) == False:
        er = "Your password is wrong"
        return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1})
    
    if password != confirmation:
        er = "Password and Confirmation do not match"
        return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1}) 
    
    if len(password) == 0 or len(confirmation) == 0:
        er = "Password and Confirmation are Empty"
        return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1}) 
    
    password_modifier(user,password)
    
@app.get("/changepassword",response_class=HTMLResponse)
@login_required
async def changepassword_get(request : Request):
    global user
    return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"prompt":0})


@app.get("/gold",response_class=HTMLResponse)
@login_required
async def gold_get(request : Request):
    global user
    c = balance_checker(user)
    return templates.TemplateResponse("gold.html",{"request":request,"user":user,"prompt":0,"cash":c[0]})
                                        

@app.post("/gold",response_class=HTMLResponse)
@login_required
async def gold_get(request : Request,gold : int = Form()):
    global user
    c = balance_checker(user)
    c = c[0]
    if gold > c:
        er = "Invalid Amount"
        return templates.TemplateResponse("gold.html",{"request":request,"user":user,"prompt":1,"cash":c,"Error":er})
        
    gold_extractor(user,gold)
    f = gold*2000
    er = "Successfully added" + str(f) + "gold"
    c = balance_checker(user)
    c = c[0]
    return templates.TemplateResponse("gold.html",{"request":request,"user":user,"prompt":2,"cash":c,"Error":er})


@app.post("/checkout",response_class=HTMLResponse)
@login_required
async def checkout(request : Request):
    global user
    items = cart_lister(user)
    price_G = total_price(items)
    price = price_G//2000  
    L = balance_checker(user)
    user_g = L[1]
    user_c = L[0]
    if price_G > user_g:
        er = "Insufficient Balance"
        return templates.TemplateResponse("cart.html",{"request":request,"items":items,"user":user,"cash":price,"cashG":price_G,"prompt":1,"Error":er})
    purchase(user,items,user_g - price_G)
    items = cart_lister(user)
    er = "Purchase Successful"
    price_G = total_price(items)
    price = price_G//2000  
    return templates.TemplateResponse("cart.html",{"request":request,"items":items,"user":user,"cash":price,"cashG":price_G,"prompt":2,"Error":er})


@app.get("/objs")
@login_required
async def my_items_get(request : Request):
    global user
    items = my_unlisted_objects(user)
    return templates.TemplateResponse("MyItems.html",{"request":request,"user":user,"items":items})


@app.get("/list/{ID}")
@login_required
async def unlister_user(request : Request,ID :int):
    global user
    lister_pro_max(ID)
    items = my_unlisted_objects(user)
    return templates.TemplateResponse("MyItems.html",{"request":request,"user":user,"items":items})

