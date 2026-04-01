from fastapi import FastAPI, Depends, HTTPException, Request, Form,status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal, get_db, init_db, create_user
from models import User, Todo
from schemas import UserPublic, Token, UserCreate, TaskCreate, TaskResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta,timezone
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import hash_password, verify_password, create_access_token, authenticate_user, get_current_user, oauth2_scheme, pwd_context


#app initialisation
#create db tables
Base.metadata.create_all(bind=engine)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # ✅ creates all tables from models
    yield

app = FastAPI(title="FastAPI To-Do App", lifespan=lifespan)  # ✅ one app
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

    
#homepage route
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id") #use cookies for logged in users
    if user_id: #if user id exists in cookies, query db for user and their tasks, render homepage with task
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            todos = db.query(Todo).filter(Todo.owner_id == user.id).all()
            return templates.TemplateResponse("index.html", {"request": request, "todos": todos, "user": user})
    return RedirectResponse(url="/login") #if not logged in, redirect to login page

#registration routes
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.post("/register", status_code=201, summary="Create a new user")
def register(body: UserCreate, request: Request):
    hashed = hash_password(body.password)
    create_user(body.username, hashed, body.full_name or "")
    return templates.TemplateResponse("login.html", {"request":request}) #redirects to login page
    

#login routes
@app.get("/login", response_class=HTMLResponse)
def login_page(request:Request):
    return templates.TemplateResponse("login.html", {"request":request})

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


#current user route
@app.get("/me", response_model=UserPublic, summary="Get my profile (protected)")
def read_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user

#logout route
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response


#task management routes
@app.post("/tasks")
def add_task(request:Request, title:str=Form(...), db:Session=Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    task = Todo(title=title,owner_id=int(user_id))
    db.add(task)
    db.commit()
    return RedirectResponse(url="/",status_code=303)
@app.post("/tasks/{task_id}/toggle")    
def toggle(task_id:int, request:Request,db:Session=Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    task = db.query(Todo).filter(Todo.id==task_id, Todo.owner_id==int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404,detail="Task not found")
    task.completed = not task.completed
    db.commit()
    return RedirectResponse(url="/",status_code=303)

@app.post("/tasks/{task_id}/delete")
def delete(task_id:int, request:Request,db:Session=Depends(get_db)):
    user_id=request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    task = db.query(Todo).filter(Todo.id==task_id,Todo.owner_id==int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404,detail="Task not found")
    db.delete(task)
    db.commit()
    return RedirectResponse(url="/",status_code=303)

@app.post("/tasks/{task_id}/update")
def update(task_id:int, request:Request, title:str=Form(...), db:Session=Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    task = db.query(Todo).filter(Todo.id==task_id,Todo.owner_id==int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404,detail="Task not found")
    task.title = title
    db.commit()
    return RedirectResponse(url="/",status_code=303)

@app.get("/add", response_class=HTMLResponse)
def add_task_page(request:Request, db:Session=Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    user = db.query(User).filter(User.id==int(user_id)).first()
    if not user:
        return  RedirectResponse(url="/login",status_code=303)
    return templates.TemplateResponse("add_task_page.html",{"request":request, "user":user})

#handles all server side logic, db interactions, user authentication, CRUD operations for tasks, and rendering of HTML templates for the frontend

# -app initialisation -> creates db+tables, ✅
#                         fastapi+jinja2 templates, ✅
#                         sets password hashing context ✅
# -✅registration routes -> GET/register; POST/register
# -✅login routes -> GET/login, login form; POST/login, verify pass, set cookie
# -✅logout route -> GET/logout; delete session cookie, redirect to login
# -✅homepage -> GET/, display tasks, use cookies for logged in users, redirect to login if not logged in
# -task management routes -> ✅POST/tasks, new task;
#                          ✅POST/tasks/{task_id}/toggle, mark task as un/completed; 
#                         ✅POST/tasks/{task_id}/delete, delete task, 
#                         ✅POST/tasks/{task_id}/update, update task title
#✅ -add task (template)-> GET/add, show form