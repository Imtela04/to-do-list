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

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal, get_db
from models import User, Todo

#app initialisation
#create db tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
@app.post("/register")
def register(
    request:Request, 
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.name==username).first(): #matching the first instance of the given username from the db table User, true: returns error (username alr exists)
        return templates.TemplateResponse("register.html", {"request":request, "error":"Username already exists"})
    hashed_password = pwd_context.hash(password) #encrypting password
    user = User(name=username, hashed_password=hashed_password) #creates user instance in the Users table with the given username and hashed password
    db.add(user) #adds instnce to db
    db.commit() #permanently saves instance
    return templates.TemplateResponse("login.html", {"request":request}) #redirects to login page
    

#login routes
@app.get("/login", response_class=HTMLResponse)
def login_page(request:Request):
    return templates.TemplateResponse("login.html", {"request":request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User not found"})
    if not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect password"})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response


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