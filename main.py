import os
from fastapi import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from complementary.sql_connectors import *
from functools import wraps
from itsdangerous import Signer
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import aiofiles
from pathlib import Path


# Configuration
SECRET_KEY = "your_secret_key"  # Replace with your own secret key
signer = Signer(SECRET_KEY)

base_path = os.path.dirname(os.path.abspath(__file__))
stat = "static"
stat_path = os.path.join(base_path, stat)
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory=stat_path), name="static")
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    @wraps(f)
    async def wrapper(request: Request, *args, **kwargs):
        if not request.session.get("user"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not logged in"
            )
        return await f(request, *args, **kwargs)
    return wrapper

@app.route("/",methods=["GET", "POST"])
async def home(request: Request):
    user = request.session.get("user")
    if user is None:
        L = [0,0]
    else:
        L = balance_checker(user)
        L = list(L[0])
    return templates.TemplateResponse("home.html", {"request": request, "user": user,"cash":L[0],"cashG":L[1]})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    prompt = 0
    return templates.TemplateResponse("login.html", {"request": request, "prompt": prompt})

@app.post("/login",response_class=[HTMLResponse, RedirectResponse])
async def login_post(request: Request, username: str = Form(), password: str = Form()):
    u = login_verifier(username, password)
    if u is None:
        prompt = 1
        er = "You have given wrong credentials or user does not exist"
        return templates.TemplateResponse("login.html", {"request": request, "prompt": prompt, "Error": er, "user": None})
    else:
        request.session["user"] = u
        return RedirectResponse(url="/")

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/",status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def reg_get(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("register.html", {"request": request, "prompt": 0, "user": user})

@app.post("/register")
async def reg_post(request: Request, username: str = Form(), password: str = Form(), confirmation: str = Form()):
    er = register_helper(username, password, confirmation)
    if len(er) != 0:
        return templates.TemplateResponse("register.html", {"request": request, "prompt": 2, "Error": er, "user": None})
    else:
        request.session["user"] = login_verifier(username, password)
        return RedirectResponse(url="/",status_code=302)
        
categories = ["sword", "axe", "scythe", "shield", "pickaxe", "spear", "potions", "books", "ingredients","gold"]
@app.get("/item/{category}", response_class=HTMLResponse)
async def get_category_items(request: Request, category: str):
    if category not in categories:
        return HTMLResponse(content="Category not found", status_code=404)
    
    user = request.session.get("user")
    items = listed_object_data_generator(category)
    L = balance_checker(user)
    L = list(L[0])
    if category == "gold":
        return RedirectResponse("/gold")
    context = {
        "request": request,
        "items": items,
        "user": user,
        "cash": L[0],
        "cashG": L[1]
    } 
    return templates.TemplateResponse(f"{category}.html", context)

@app.post("/CCart/{ID}/{Type}")
@login_required
async def object_cart(request: Request, ID: int, Type: str):
    user = request.session.get("user")
    t = object_unlister_and_cart_filler(ID, user)
    if t==0:
        return JSONResponse(content={"error": "You cannot buy your own item."}, status_code=status.HTTP_401_UNAUTHORIZED)
    elif t==1:
        return JSONResponse(content={"error": "Carting failed, reload and try again."}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    items = listed_object_data_generator(Type)
    return JSONResponse(content={"items": items, "user": user})


@app.post("/buy", response_class=HTMLResponse)
@login_required
async def buy(request: Request, accountid: str = Form(), password: str = Form(), confirmation: str = Form(), amount: int = Form()):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0]) 
    if not bank_confirm(accountid):
        er = "Wrong Account ID or Account does not exist"
        return templates.TemplateResponse("buy.html", {"request": request, "user": user, "prompt": 1, "Error": er, "cash": L[0], "cashG": L[1]})
    if password != confirmation:
        er = "Password and Confirmation do not match"
        return templates.TemplateResponse("buy.html", {"request": request, "user": user, "prompt": 1, "Error": er, "cash": L[0], "cashG": L[1]})
    if not bank_withdrawer(user, accountid, password, amount):
        er = "Insufficient money in your account"
        return templates.TemplateResponse("buy.html", {"request": request, "user": user, "prompt": 1, "Error": er, "cash": L[0], "cashG": L[1]})
    else:
        er = "Funds added, go to balance to check"
        return templates.TemplateResponse("buy.html", {"request": request, "user": user, "prompt": 2, "Error": er, "cash": L[0], "cashG": L[1]})

@app.get("/buy",response_class=HTMLResponse)
@login_required
async def buy_g(request : Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0]) 
    return templates.TemplateResponse("buy.html",{"request":request,"user":user,"prompt":0,"cash":L[0],"cashG":L[1]})
    

# @app.post("/changepassword",response_class=HTMLResponse)
# @login_required
# async def changepassword(request : Request,cpassword : str = Form(),password : str = Form(),confirmation : str = Form()):
#     user = request.session.get("user")
#     L = balance_checker(user)
#     L = list(L[0]) 
#     if password_verifier(user,cpassword) == False:
#         er = "Your password is wrong"
#         return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1,"cash":L[0],"cashG":L[1]})
    
#     if password != confirmation:
#         er = "Password and Confirmation do not match"
#         return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1,"cash":L[0],"cashG":L[1]}) 
    
#     if len(password) == 0 or len(confirmation) == 0:
#         er = "Password and Confirmation are Empty"
#         return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"Error":er,"prompt":1,"cash":L[0],"cashG":L[1]}) 
    
#     password_modifier(user,password)
    
# @app.get("/changepassword",response_class=HTMLResponse)
# @login_required
# async def changepassword_get(request : Request):
#     user = request.session.get("user")
#     L = balance_checker(user)
#     L = list(L[0]) 
#     return templates.TemplateResponse("changepassword.html",{"request":request,"user":user,"prompt":0,"cash":L[0],"cashG":L[1]})

@app.get("/gold",response_class=HTMLResponse)
@login_required
async def gold_get(request : Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0]) 
    modifier = mean_gold()
    print(mean_gold)
    return templates.TemplateResponse("gold.html",{"request":request,"modifier":modifier,"user":user,"prompt":0,"cash":L[0],"cashG":L[1]})
                                        

@app.post("/gold",response_class=HTMLResponse)
@login_required
async def gold_get(request : Request,gold : int = Form()):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0]) 
    c = L[0]
    modifier = mean_gold()
    if gold > c:
        er = "Invalid Amount"
        return templates.TemplateResponse("gold.html",{"request":request,"user":user,"prompt":1,"cash":c,"cashG":L[1],"Error":er,"modifier":modifier})
    
    gold_extractor(user,gold,modifier)
    f = gold*2000
    er = "Successfully added  " + str(f) + "  gold"
    L = balance_checker(user)
    L = list(L[0]) 
    c = L[0]
    return templates.TemplateResponse("gold.html",{"request":request,"user":user,"prompt":2,"cash":c,"Error":er,"cashG":L[1],"modifier":modifier})

class ItemData(BaseModel):
    ID: int
    Type: str

def render_cart_items(items):
    items_html = ""
    for i in items:
        items_html += f"""
        <div class="col-md-6 mb-4">
            <div class="card shadow-sm h-100">
                <img src="{i[3]}" class="card-img-top" alt="{i[1]}">
                <div class="card-body">
                    <h5 class="card-title">{i[1]}</h5>
                    <p class="card-text">
                        <strong>Rating:</strong> {i[4]}<br>
                        <strong>Price:</strong> {i[5]} G
                    </p>
                    <button class="btn btn-danger btn-block uncart-btn" data-id="{i[0]}" data-type="{i[2]}">
                        <i class="fas fa-times"></i> Uncart
                    </button>
                </div>
            </div>
        </div>
        """
    return items_html

@app.post("/checkout", response_class=JSONResponse)
@login_required
async def checkout(request: Request):
    user = request.session.get("user")
    items = cart_lister(user)
    price_G = total_price(items)
    user_balance = balance_checker(user)
    user_balance = list(user_balance[0])
    user_g = user_balance[1]
    if price_G > user_g:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Insufficient Balance"}
        )
    if purchase(user, items, user_g - price_G) == False:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Purchase Failed"}
        )
    items = cart_lister(user)
    price_G = total_price(items)
    return JSONResponse(content={
        "message": "Purchase Successful",
        "items_html": render_cart_items(items),
        "cashg": price_G
    })

@app.post("/uncart", response_class=JSONResponse)
@login_required
async def uncart(request: Request, item_data: ItemData):
    uncarter(item_data.ID)
    user = request.session.get("user")
    items = cart_lister(user)
    price_G = total_price(items)
    return JSONResponse(content={
        "message": "Uncarted Successfully",
        "items_html": render_cart_items(items),
        "cashg": price_G
    })

@app.get("/cart", response_class=HTMLResponse)
@login_required
async def cart(request: Request):
    user = request.session.get("user")
    items = cart_lister(user)
    price_G = total_price(items)
    user_balance = balance_checker(user)
    user_balance = list(user_balance[0])
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "items": items,
        "cashg": price_G,
        "cash": user_balance[0],
        "cashG": user_balance[1],
        "user": user
    })

@app.get("/cart-data", response_class=JSONResponse)
@login_required
async def cart_data(request: Request):
    user = request.session.get("user")
    items = cart_lister(user)
    price_G = total_price(items)
    return JSONResponse(content={
        "items_html": render_cart_items(items),
        "cashg": price_G
    })

@app.get("/objs")
@login_required
async def my_items_get(request: Request):
    user = request.session.get("user")
    items = my_unlisted_objects(user)
    L = balance_checker(user)
    L = list(L[0])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JSONResponse({"items": items, "cash": L[0], "cashG": L[1]})
    
    return templates.TemplateResponse("MyItems.html", {"request": request, "user": user, "items": items, "cash": L[0], "cashG": L[1]})

@app.post("/list/{ID}")
@login_required
async def lister_user(request: Request, ID: int):
    user = request.session.get("user")
    lister_pro_max(ID)
    items = my_unlisted_objects(user)
    L = balance_checker(user)
    L = list(L[0])

    return JSONResponse({"items": items, "cash": L[0], "cashG": L[1]})

@app.post("/unlist/{ID}")
@login_required
async def unlister_user(request: Request, ID: int):
    user = request.session.get("user")
    unlister_pro_max(ID)
    items = my_unlisted_objects(user)
    L = balance_checker(user)
    L = list(L[0])

    return JSONResponse({"items": items, "cash": L[0], "cashG": L[1]})

@app.post("/scatter/{ID}")
@login_required
async def scatter_purge(request: Request, ID: int):
    u_id = request.session.get("user")
    if u_id == 1:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Admin should not purge items"}
        )
    purger(ID, u_id)
    items = my_unlisted_objects(u_id)
    L = balance_checker(u_id)
    L = list(L[0])

    return JSONResponse({"items": items, "cash": L[0], "cashG": L[1]})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user, "cash": L[0], "cashG": L[1]})

@app.post("/admin/execute-sql")
async def execute_sql(request: Request):
    body = await request.json()
    command = body.get("command")
    if not command:
        return JSONResponse({"status": "error", "result": "No SQL command provided"}, status_code=400)
    try:
        result = execute(command)
        return JSONResponse({"status": "success", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "result": str(e)}, status_code=500)

@app.get("/admin/items-per-rating")
async def items_per_rating(request: Request):
    data = get_items_per_rating_data()
    print(data)
    ratings = [row["rating"] for row in data]
    counts = [row["count"] for row in data]
    return {"ratings": ratings, "counts": counts}

@app.get("/admin/avg-price-per-rating")
async def avg_price_per_rating(request: Request):
    data = get_avg_price_per_rating_data()
    ratings = [row["rating"] for row in data]
    avgPrices = [row["avg_price"] for row in data]
    return {"ratings": ratings, "avgPrices": avgPrices}

@app.get("/admin/avg-price-per-category")
async def avg_price_per_category(request: Request):
    data = get_avg_price_per_category_data()
    categories = [row["Object_type"] for row in data]
    avgPrices = [row["avg_price"] for row in data]
    return {"categories": categories, "avgPrices": avgPrices}

@app.get("/admin/player-wealth-leaderboard")
async def player_wealth_leaderboard(request: Request):
    data = get_player_wealth_leaderboard_data()
    players = [row["Name"] for row in data]
    wealth = [row["wealth"] for row in data]
    return {"players": players, "wealth": wealth}

@app.get("/lottery-wheel", response_class=HTMLResponse)
async def read_root(request: Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    modifier = mean_gold()
    return templates.TemplateResponse("wheel.html", {"request": request, "user": user, "cash": L[0], "cashG": L[1],"modifier": modifier})

@app.post("/select_random")
async def select_random(request: Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    objects = generate_objects(10)
    selected_object = random.choice(objects)
    modifier = mean_gold()
    if L[1] < modifier:
        return JSONResponse(content={"error": "Insufficient Gold","selected_object": None, "objects": None})
    conn = get_db_connection()
    conn.execute("update user_store set Gold = Gold - ? where ID = ? ",(modifier,user))
    conn.commit()
    conn.close()
    insert_object_and_user(selected_object,user)
    L = balance_checker(user)
    L = list(L[0])
    return {"selected_object": selected_object, "objects": objects,"cash": L[0], "cashG": L[1]}

@app.post("/select_random_10")
async def select_random_10(request: Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    objects = generate_objects(100)
    selected_objects = random.sample(objects, 10)
    modifier = mean_gold()*9
    if L[1] < modifier:
        return JSONResponse(content={"error": "Insufficient Gold","selected_objects": None, "objects": None})
    conn = get_db_connection()
    conn.execute("update user_store set Gold = Gold - ? where ID = ? ",(modifier,user))
    conn.commit()
    conn.close()
    for selected_object in selected_objects:
        insert_object_and_user(selected_object,user)
    L = balance_checker(user)
    L = list(L[0])
    return {"selected_objects": selected_objects, "objects": objects,"cash": L[0], "cashG": L[1]}


@app.post("/select_random_free")
async def select_random_free(request: Request):
    today = datetime.now().date()
    now = datetime.now()

    # Check session for stored selected object and date
    selected_data = request.session.get('selected_data', {})
    
    if selected_data.get("date") == str(today):
        selected_object = selected_data["selected_object"]
        time_until_next_day = (datetime.combine(today + timedelta(days=1), datetime.min.time()) - now).total_seconds()
        return JSONResponse(content={
            "message": "Free select has already been used today.",
            "selected_object": selected_object,
            "time_left": time_until_next_day
        })
    else:
        objects = generate_objects(10)
        selected_object = random.choice(objects)
        insert_object_and_user(selected_object,request.session.get["user"])
        request.session['selected_data'] = {
            "selected_object": selected_object,
            "date": str(today)
        }
        return {"selected_object": selected_object,"objects":objects}
    


@app.post("/profile", response_class=HTMLResponse)
@login_required
async def update_profile(request: Request, description: str = Form(...), password: str = Form(None), confirmation: str = Form(None), file: UploadFile = File(None)):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    if password and confirmation:
        if password != confirmation:
            er = "Password and Confirmation do not match"
            return templates.TemplateResponse("profile.html", {"request": request, "user": user, "Error": er, "prompt": 1, "cash": L[0], "cashG": L[1]})

        if not password or not confirmation:
            er = "Password and Confirmation are Empty"
            return templates.TemplateResponse("profile.html", {"request": request, "user": user, "Error": er, "prompt": 1, "cash": L[0], "cashG": L[1]})

        password_modifier(user, password)

    if file:
        file_location = f"static/{user}.jpg"
        async with aiofiles.open(file_location, 'wb') as f:
            content = await file.read()
            await f.write(content)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_pic = ? WHERE Id = ?", (file_location, user))
        conn.commit()
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET description = ? WHERE Id = ?", (description, user))
    conn.commit()
    conn.close()

    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "prompt": 0, "cash": L[0], "cashG": L[1]})

@app.get("/profile", response_class=HTMLResponse)
@login_required
async def profile_get(request: Request):
    user = request.session.get("user")
    L = balance_checker(user)
    L = list(L[0])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, profile_pic, Recovery FROM users WHERE Id = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    description = result[0]
    profile_pic = result[1]
    recovery = result[2]

    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "description": description, "profile_pic": profile_pic, "recovery": recovery, "prompt": 0, "cash": L[0], "cashG": L[1]})