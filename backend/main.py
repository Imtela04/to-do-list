from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse,FileResponse
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from backend.database import engine, Base, get_db
from backend.models import User, Todo
from backend.schemas import UserPublic, Token
from backend.auth import hash_password, create_access_token, authenticate_user, get_current_user, create_user, get_username_from_header, get_username_from_cookie
 

#app initialisation
#create db tables
Base.metadata.create_all(bind=engine)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # ✅ creates all tables from models
    yield

app = FastAPI(title="FastAPI To-Do App", lifespan=lifespan)  # ✅ one app

#homepage route
#current user route
@app.get("/api/me", response_model=UserPublic)
def read_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user

#registration routes
logged_in = ''
@app.post("/api/register", status_code=201)
def register(
    # request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    hashed = hash_password(password)
    try:
        create_user(db, username, hashed)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Username already taken") 
    user = authenticate_user(db, username, password)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "Bearer"}

#login routes
@app.post("/api/login", response_model=Token)
def login(username: str = Form(...), password:str = Form(...),db: Session=Depends(get_db)):
    #print(request,username,password)
    user = authenticate_user(db, username, password)  # ✅ pass db
    #print(user)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }


#logout route
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response


#task management routes
@app.get("/api/tasks")
def get_tasks(current_user: UserPublic = Depends(get_current_user), db:Session=Depends(get_db)):
    user = db.query(User).filter(User.username==current_user.username).first()
    return user.todos
@app.post("/api/tasks")
def add_task(current_user:UserPublic=Depends(get_current_user), title:str=Form(...), db:Session=Depends(get_db)):
    user = db.query(User).filter(User.username==current_user.username).first()
    task = Todo(title=title,owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/tasks/{task_id}")
def delete(task_id:int, current_user:UserPublic=Depends(get_current_user), db:Session=Depends(get_db)):
    
    user = db.query(User).filter(User.username==current_user.username).first()
    task = db.query(Todo).filter(Todo.id==task_id,Todo.owner_id==user.id).first()
    if not task:
        raise HTTPException(status_code=404,detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok":True}

# main.py

@app.patch("/api/tasks/{task_id}/title")
def update_task_title(
    task_id: int,
    title: str = Form(...),
    current_user: UserPublic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user.username).first()
    task = db.query(Todo).filter(Todo.id == task_id, Todo.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.title = title
    db.commit()
    db.refresh(task)
    return task

@app.patch("/api/tasks/{task_id}/toggle")
def toggle_task(
    task_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user.username).first()
    task = db.query(Todo).filter(Todo.id == task_id, Todo.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = not task.completed   # backend handles the flip, no bool parsing needed
    db.commit()
    db.refresh(task)
    return task

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# Explicit routes for HTML pages — BEFORE the static catch-all
@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

@app.get("/login.html")
def serve_login():
    return FileResponse("frontend/login.html")

@app.get("/register.html")
def serve_register():
    return FileResponse("frontend/register.html")
# templates = Jinja2Templates(directory="frontend/templates")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")  # ✅ serve frontend from root
