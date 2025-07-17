from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, schemas, utils
from database import SessionLocal, engine
import os
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, initData: str = None, db: Session = Depends(get_db)):
    if not initData:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "No initData provided"
        })
    
    if not utils.validate_init_data(initData):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Invalid initData"
        })
    
    user_data = utils.extract_user_data(initData)
    telegram_id = user_data['telegram_id']
    
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    
    if db_user:
        # User exists - show profile
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": db_user
        })
    else:
        # New user - show registration form
        return templates.TemplateResponse("register.html", {
            "request": request,
            "telegram_id": telegram_id,
            "telegram_username": user_data.get('username', ''),
            "first_name": user_data.get('first_name', '')
        })

@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    telegram_id: int = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Validate input data
        user_data = schemas.UserCreate(username=username, email=email, password=password)
    except ValidationError as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": str(e),
            "telegram_id": telegram_id,
            "username": username,
            "email": email
        })
    
    # Check if username or email already exists
    db_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username or email already registered",
            "telegram_id": telegram_id,
            "username": username,
            "email": email
        })
    
    # Create new user (in real app password should be hashed)
    db_user = models.User(
        telegram_id=telegram_id,
        username=username,
        email=email,
        hashed_password=password,  # In production, hash the password properly
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": db_user
    })