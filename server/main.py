from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from models import models
from schemas import schemas
from config.db import engine, database
from typing import List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from cryptography.fernet import Fernet
from jose import jwt
import os
import bcrypt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from google.oauth2 import id_token
# from google.auth.transport import requests
import requests
from sqlalchemy import text

#giving access to the front end server
app = FastAPI()

app.add_middleware(
     CORSMiddleware,
     allow_origins=["http://localhost:3000"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

@app.middleware("http")
async def add_x_frame_options_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.middleware("http")
async def remove_date_header(request, call_next):
    response = await call_next(request)
    del response.headers["Date"]
    return response

JWT_SECRET = os.getenv("JWT_SECRET")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID")
facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")
# Facebook OAuth settings
facebook_redirect_uri = os.getenv("facebook_redirect_uri")
redirect_uri = os.getenv("redirect_uri")

# In-memory cache to store issued tokens
token_cache = {}

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Login route
@app.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, form_data: schemas.UserLogin):
    # Verify username and password
    query = models.User.select().where(models.User.c.username == form_data.username)
    user = await database.fetch_one(query)
    if user:
        # Verify password using bcrypt
        if bcrypt.checkpw(form_data.password.encode('utf-8'), user.password.encode('utf-8')):
            # Generate access token and refresh token
            access_token = jwt.encode({"sub": user.id, "exp": 900}, key=JWT_SECRET, algorithm="HS256")
            refresh_token = jwt.encode({"sub": user.id, "exp": 3600}, key=REFRESH_TOKEN_SECRET, algorithm="HS256")
            # Store tokens in cache
            token_cache[access_token] = user.id
            return {"access_token": access_token, "refresh_token": refresh_token}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

# Logout route
@app.post("/logout")
async def logout(request: Request):
    # Get the token from the Authorization header
    token = request.headers.get('Authorization')
    if token:
        # Remove the 'Bearer ' prefix
        token = token.replace('Bearer ', '')
        # Check if token is valid
        if token in token_cache:
            # Revoke token
            del token_cache[token]
            return {"message": "Logged out successfully"}
    raise HTTPException(status_code=401, detail="Invalid token")

# Refresh token route
@app.post("/refresh-token")
async def refresh_token(request: Request, refresh_token: OAuth2PasswordBearer = Depends()):
    # Check if refresh token is valid
    for access_token, stored_refresh_token in token_cache.items():
        if stored_refresh_token == refresh_token:
            # Generate new access token
            user_id = jwt.decode(refresh_token, key=REFRESH_TOKEN_SECRET, algorithms=["HS256"])["sub"]
            new_access_token = jwt.encode({"sub": user_id, "exp": 900}, key=JWT_SECRET, algorithm="HS256")
            # Update token cache
            token_cache[new_access_token] = refresh_token
            return {"access_token": new_access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid refresh token")

# Protected route
@app.get("/protected")
async def protected(request: Request, access_token: OAuth2PasswordBearer = Depends()):
    # Check if token is valid
    if access_token not in token_cache:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"message": "Hello, protected world!"}

@app.post("/users/")
async def create_user(user: schemas.UserCreate):
    # Check if the username already exists
    query = models.User.select().where(models.User.c.username == user.username)
    existing_user = await database.fetch_one(query)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    query = models.User.insert().values(username=user.username, email=user.email, password=hashed_password)
    last_record_id = await database.execute(query)

    return {"message": "User created successfully", "id": last_record_id}

###customers crud

@app.get("/customers/", response_model=List[schemas.Customer])
async def read_notes():
    query = models.customers.select()
    return await database.fetch_all(query)


@app.post("/customers/")
async def create_user(customer: schemas.Customer):
    query = text("INSERT INTO customers (cusName, cusEmail, cusNum, cusPassword) VALUES (:cusName, :cusEmail, :cusNum, :cusPassword)")
    query = query.bindparams(
        cusName=customer.cusName,
        cusEmail=customer.cusEmail,
        cusNum=customer.cusNum,
        cusPassword=customer.cusPassword
    )
    last_record_id = await database.execute(query)
    return {**customer.dict(), "cusId": last_record_id}

@app.put("/customers/{cusId}", response_model=schemas.Customer)
async def update_user(customer: schemas.Customer, cusId: int):
    query = models.customers.update().values(cusName=customer.cusName,cusEmail=customer.cusEmail,cusNum=customer.cusNum,cusPassword=customer.cusPassword).where(models.customers.c.cusId == cusId)
    last_record_id = await database.execute(query)
    return {**customer.dict(), "cusId": last_record_id}

@app.delete("/customers/{cusId}")
async def delete_user(cusId: int):
    query = text("DELETE FROM customers WHERE cusId = :cusId")
    query = query.bindparams(cusId=cusId)
    last_record_id = await database.execute(query)
    return {"cusId": last_record_id}

#card details
@app.get("/cards/", response_model=List[schemas.Card])
async def read_cards():
    query = models.cards.select()
    return await database.fetch_all(query)

@app.post("/cards/", response_model=schemas.Card)
async def create_card(card: schemas.Card):
    query = models.cards.insert().values(cardtype=card.cardtype,cardnum=card.cardnum, exdate=card.exdate, cvv=card.cvv, cardname=card.cardname, billaddress=card.billaddress)
    last_record_id = await database.execute(query)
    return {**card.dict(), "cardId": last_record_id}

@app.put("/cards/{cardId}", response_model=schemas.Card)
async def update_card(card: schemas.Card, cardId: int):
    query = models.cards.update().values(cardtype=card.cardtype,cardnum=card.cardnum, exdate=card.exdate, cvv=card.cvv, cardname=card.cardname, billaddress=card.billaddress).where(models.cards.c.cardId == cardId)
    last_record_id = await database.execute(query)
    return {**card.dict(), "cardId": last_record_id}

@app.delete("/cards/{cardId}")
async def delete_card(cardId: int):
    query = models.cards.delete().where(models.cards.c.cardId == cardId)
    last_record_id = await database.execute(query)
    return {"cardId": last_record_id}

#orders 
@app.get("/orders/", response_model=List[schemas.Order])
async def read_notes():
    query = models.orders.select()
    return await database.fetch_all(query)

@app.post("/orders/", response_model=schemas.Order)
async def create_user(order: schemas.OrderIn):
    query = models.orders.insert().values(cusName=order.cusName,orderType=order.orderType, orderDateTime=order.orderDateTime, fooditems=order.fooditems, quantity=order.quantity, orderTotal=order.orderTotal, status=order.status)
    last_record_id = await database.execute(query)
    return {**order.dict(), "orderId": last_record_id}

@app.delete("/orders/{orderId}")
async def delete_order(orderId: int):
    query = models.orders.delete().where(models.orders.c.orderId == orderId)
    last_record_id = await database.execute(query)
    return {"orderId": last_record_id}


#feedbacks
@app.get("/feedbacks/", response_model=List[schemas.Feedback])
async def read_feedbacks():
    query = models.feedbacks.select()
    return await database.fetch_all(query)

@app.post("/feedbacks/", response_model=schemas.Feedback)
async def create_feedbacks(feedback: schemas.Feedback):
    query = models.feedbacks.insert().values(feedbackCustName=feedback.feedbackCustName, feedbackCustEmail=feedback.feedbackCustEmail, feedback=feedback.feedback)
    last_record_id = await database.execute(query)
    return {**feedback.dict(), "feedbackId": last_record_id}

@app.put("/feedbacks/{feedbackId}", response_model=schemas.Feedback)
async def update_feedbacks(feedback: schemas.Feedback, feedbackId: int):
    query = models.feedbacks.update().values(feedbackCustName=feedback.feedbackCustName, feedbackCustEmail=feedback.feedbackCustEmail, feedback=feedback.feedback)
    last_record_id = await database.execute(query)
    return {**feedback.dict(), "feedbackId": last_record_id}

@app.delete("/feedbacks/{feedbackId}")
async def delete_feedbacks(feedbackId: int):
    query = models.feedbacks.delete().where(models.feedbacks.c.feedbackId == feedbackId)
    last_record_id = await database.execute(query)
    return {"feedbackId": last_record_id}


##############navo
@app.get("/schedules/", response_model=List[schemas.Schedule])
async def read_notes():
    query = models.schedules.select()
    return await database.fetch_all(query)

@app.post("/schedules/", response_model=schemas.Schedule)
async def create_user(schedule: schemas.ScheduleIn):
    query = models.schedules.insert().values(scheduleName=schedule.scheduleName,scheduleAddress=schedule.scheduleAddress,scheduleMobilenumber=schedule.scheduleMobilenumber,scheduleDate=schedule.scheduleDate,scheduleTime=schedule.scheduleTime,scheduleOrderdetails=schedule.scheduleOrderdetails)
    last_record_id = await database.execute(query)
    return {**schedule.dict(), "scheduleId": last_record_id}

@app.put("/schedules/{scheduleId}", response_model=schemas.Schedule)
async def update_user(schedule: schemas.ScheduleIn, scheduleId: int):
    query = models.schedules.update().values(scheduleName=schedule.scheduleName,scheduleAddress=schedule.scheduleAddress,scheduleMobilenumber=schedule.scheduleMobilenumber,scheduleDate=schedule.scheduleDate,scheduleTime=schedule.scheduleTime,scheduleOrderdetails=schedule.scheduleOrderdetails).where(models.schedules.c.scheduleId == scheduleId)
    last_record_id = await database.execute(query)
    return {**schedule.dict(), "scheduleId": last_record_id}

@app.delete("/schedules/{scheduleId}")
async def delete_card(scheduleId: int):
    query = models.schedules.delete().where(models.schedules.c.scheduleId == scheduleId)
    last_record_id = await database.execute(query)
    return {"scheduleId": last_record_id}


#########employee

@app.get("/employee/{empemail},{emppass}", response_model=List[schemas.Employee])
async def read_notes( empemail: str, emppass: str):
    query = models.employee.select().where(models.employee.c.empemail == empemail, models.employee.c.emppass == emppass)
    return await database.fetch_all(query)

@app.get("/employee/", response_model=List[schemas.Employee])
async def read_notes():
    query = models.employee.select()
    return await database.fetch_all(query)


@app.post("/employee/", response_model=schemas.Employee)
async def create_user(employee: schemas.Employee):
    query = models.employee.insert().values(efirstname = employee.efirstname,elastname = employee.elastname,eaddress = employee.eaddress,empemail=employee.empemail,hireddate = employee.hireddate,salary = employee.salary,role = employee.role,noofleaves = employee.noofleaves,emppass=employee.emppass)
    last_record_id = await database.execute(query)
    return {**employee.dict(), "eid": last_record_id}

@app.put("/employee/{eid}", response_model=schemas.Employee)
async def update_user(employee: schemas.Employee, eid: int):
    query = models.employee.update().values(efirstname = employee.efirstname,elastname = employee.elastname,eaddress = employee.eaddress,empemail=employee.empemail,hireddate = employee.hireddate,salary = employee.salary,role = employee.role,noofleaves = employee.noofleaves,emppass=employee.emppass).where(models.employee.c.eid == eid)
    last_record_id = await database.execute(query)
    return {**employee.dict(), "eid": last_record_id}

@app.delete("/employee/{eid}")
async def delete_user(eid: int):
    query = models.employee.delete().where(models.employee.c.eid == eid)
    last_record_id = await database.execute(query)
    return {"eid": last_record_id}

@app.get("/request/", response_model=List[schemas.Request])
async def read_notes():
    query = models.cards.select()
    return await database.fetch_all(query)

@app.post("/request/", response_model=schemas.Request)
async def create_user(request: schemas.Request):
    query = models.request.insert().values(reqdate = request.ereqdate, etitle = request.etitle, emessage = request.emessage)
    last_record_id = await database.execute(query)
    return {**request.dict(), "reqid": last_record_id}

#############vendors
@app.get("/vendors/", response_model=List[schemas.Vendor])
async def read_notes():
    query = models.vendors.select()
    return await database.fetch_all(query)

@app.post("/vendors/", response_model=schemas.Vendor)
async def create_vendor(vendor: schemas.Vendor):
    query = models.vendors.insert().values(vid=vendor.vid,vname=vendor.vname,vcontact=vendor.vcontact,vtype=vendor.vtype,vemail=vendor.vemail,vzip=vendor.vzip,vaddress=vendor.vaddress)
    last_record_id = await database.execute(query)
    return {**vendor.dict(), "vid": last_record_id}

@app.put("/vendors/{vid}", response_model=schemas.Vendor)
async def update_vendor(vendor: schemas.Vendor, vid: int):
    query = models.vendors.update().values(vid=vendor.vid,vname=vendor.vname,vcontact=vendor.vcontact,vtype=vendor.vtype,vemail=vendor.vemail,vzip=vendor.vzip,vaddress=vendor.vaddress).where(models.vendors.c.vid == vid)
    last_record_id = await database.execute(query)
    return {**vendor.dict(), "vid": last_record_id}

@app.delete("/vendors/{vid}")
async def delete_vendor(vid: int):
    query = models.vendors.delete().where(models.vendors.c.vid == vid)
    last_record_id = await database.execute(query)
    return {"vid": last_record_id}

    #############

@app.get("/transac/", response_model=List[schemas.Transac])
async def read_notes():
    query = models.transac.select()
    return await database.fetch_all(query)

@app.post("/transac/", response_model=schemas.Transac)
async def create_strans(trans: schemas.Transac):
    query = models.transac.insert().values(stcname=trans.stcname,stdate=trans.stdate,stitem=trans.stitem,stquantity=trans.stquantity,stamount=trans.stamount)
    last_record_id = await database.execute(query)
    return {**trans.dict(), "stid": last_record_id}

@app.put("/transac/{stid}", response_model=schemas.Transac)
async def update_strans(trans: schemas.Transac, stid: int):
    query = models.transac.update().values(stcname=trans.stcname,stdate=trans.stdate,stitem=trans.stitem,stquantity=trans.stquantity,stamount=trans.stamount).where(models.transac.c.stid==stid)
    last_record_id = await database.execute(query)
    return {**trans.dict(), "stid": last_record_id}

@app.delete("/transac/{stid}")
async def delete_strans(stid: int):
    query = models.transac.delete().where(models.transac.c.stid == stid)
    last_record_id = await database.execute(query)
    return {"stid": last_record_id}

#########stocks
@app.get("/stocks/", response_model=List[schemas.Stock])
async def read_notes():
    query = models.stocks.select()
    return await database.fetch_all(query)


@app.post("/stocks/", response_model=schemas.Stock)
async def create_stock(stock: schemas.Stock):
    query = models.stocks.insert().values(itemCategory=stock.itemCategory,itemName=stock.itemName,itemBrand=stock.itemBrand,itemQuantity=stock.itemQuantity,storage=stock.storage,requiredQ=stock.requiredQ)
    last_record_id = await database.execute(query)
    return {**stock.dict(), "itemCode": last_record_id}

@app.put("/stocks/{itemCode}", response_model=schemas.Stock)
async def update_stock(stock: schemas.Stock, itemCode: int):
    query = models.stocks.update().values(itemCategory=stock.itemCategory,itemName=stock.itemName,itemBrand=stock.itemBrand,itemQuantity=stock.itemQuantity,storage=stock.storage,requiredQ=stock.requiredQ).where(models.stocks.c.itemCode == itemCode)
    last_record_id = await database.execute(query)
    return {**stock.dict(), "itemCode": last_record_id}

@app.delete("/stocks/{itemCode}")
async def delete_stock(itemCode: int):
    query = models.stocks.delete().where(models.stocks.c.itemCode == itemCode)
    last_record_id = await database.execute(query)
    return {"itemCode": last_record_id}


###########incomes
@app.get("/incomes/", response_model=List[schemas.Income])
async def read_incomes():
    query = models.incomes.select()
    return await database.fetch_all(query)

@app.post("/incomes/", response_model=schemas.Income)
async def create_incomes(income: schemas.Income):
    query = models.incomes.insert().values(iDescription=income.iDescription, iValue=income.iValue, iDate=income.iDate)
    last_record_id = await database.execute(query)
    return {**income.dict(), "iTransID": last_record_id}

@app.put("/incomes/{iTransID}", response_model=schemas.Income)
async def update_incomes(income: schemas.Income, iTransID: int):
    query = models.incomes.update().values(iDescription=income.iDescription, iValue=income.iValue, iDate=income.iDate).where(models.incomes.c.iTransID == iTransID)
    last_record_id = await database.execute(query)
    return {**income.dict(), "iTransID": last_record_id}

@app.delete("/incomes/{iTransID}")
async def delete_incomes(iTransID: int):
    query = models.incomes.delete().where(models.incomes.c.iTransID == iTransID)
    last_record_id = await database.execute(query)
    return {"iTransID": last_record_id}



#expenses
@app.get("/expenses/", response_model=List[schemas.Expense])
async def read_expenses():
    query = models.expenses.select()
    return await database.fetch_all(query)

@app.post("/expenses/", response_model=schemas.Expense)
async def create_expenses(expense: schemas.Expense):
    query = models.expenses.insert().values(eDescription=expense.eDescription, eValue=expense.eValue, eDate=expense.eDate)
    last_record_id = await database.execute(query)
    return {**expense.dict(), "eTransID": last_record_id}

@app.put("/expenses/{eTransID}", response_model=schemas.Expense)
async def update_expenses(expense: schemas.Expense, eTransID: int):
    query = models.expenses.update().values(eDescription=expense.eDescription, eValue=expense.eValue, eDate=expense.eDate).where(models.expenses.c.eTransID == eTransID)
    last_record_id = await database.execute(query)
    return {**expense.dict(), "eTransID": last_record_id}

@app.delete("/expenses/{eTransID}")
async def delete_expenses(eTransID: int):
    query = models.expenses.delete().where(models.expenses.c.eTransID == eTransID)
    last_record_id = await database.execute(query)
    return {"eTransID": last_record_id}


@app.get("/menu/", response_model=List[schemas.Menu])
async def read_notes():
    query = models.menu.select()
    return await database.fetch_all(query)


@app.post("/menu/", response_model=schemas.Menu)
async def create_user(menu: schemas.Menu):
    query = models.menu.insert().values(mItemName = menu.mItemName, mItemPrice = menu.mItemPrice, mItemPhotoLink = menu.mItemPhotoLink,)
    last_record_id = await database.execute(query)
    return {**menu.dict(), "menuItemID": last_record_id}

@app.put("/menu/{mItemID}", response_model=schemas.Menu)
async def update_user(menu: schemas.Menu, mItemID: int):
    query = models.menu.update().values(mItemName = menu.mItemName, mItemPrice = menu.mItemPrice, mItemPhotoLink = menu.mItemPhotoLink).where(models.menu.c.mItemID == mItemID)
    last_record_id = await database.execute(query)
    return {**menu.dict(), "mItemID": last_record_id}

@app.delete("/menu/{mItemID}")
async def delete_user(mItemID: int):
    query = models.menu.delete().where(models.menu.c.mItemID == mItemID)
    last_record_id = await database.execute(query)
    return {"mItemID": last_record_id}

@app.post("/google-auth")
async def google_auth(request: Request):
    # Get the authorization code from the request
    code = request.query_params.get("code")

    # Exchange the authorization code for an access token
    token_url = "https://accounts.google.com/o/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:3000/google-auth",
        "client_id": google_client_id,
        "client_secret": google_client_secret,
    }
    response = requests.post(token_url, headers=headers, data=data)

    # Get the access token from the response
    access_token = response.json().get("access_token")

    # Use the access token to get the user's profile information
    user_info_url = "https://www.googleapis.com/userinfo/v2/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(user_info_url, headers=headers)

    # Get the user's profile information from the response
    user_info = response.json()

    # Create a JWT token for the user
    user_id = user_info.get("id")
    user_name = user_info.get("name")
    user_email = user_info.get("email")
    user_picture = user_info.get("picture")

    # Store the user's information in the token cache
    token_cache[user_id] = {
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "user_picture": user_picture,
    }

    # Return a JWT token for the user
    return {"access_token": create_access_token(user_id)}


# Define a route for Facebook OAuth
@app.get('/facebook-auth')
async def facebook_auth(request: Request):
    if request.method == 'GET':
        code = request.query_params.get('code')
        if code:
            # Exchange the authorization code for an access token
            token_url = 'https://graph.facebook.com/v2.12/oauth/access_token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'client_id': facebook_client_id,
                'redirect_uri': facebook_redirect_uri,
                'client_secret': facebook_client_secret,
                'code': code
            }
            response = requests.post(token_url, headers=headers, data=data)
            access_token = response.json().get('access_token')
            # Use the access token to get the user's profile information
            user_info_url = 'https://graph.facebook.com/v2.12/me'
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(user_info_url, headers=headers)
            user_info = response.json()
            username = user_info.get('name')
            # Store the username in the user store
            # user_store[username] = {'username': username}
            # Redirect the user to the /orders page
            return Response(status_code=status.HTTP_302_FOUND, headers={"Location": redirect_uri})