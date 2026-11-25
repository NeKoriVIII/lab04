from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import engine, Base, get_db
import models
from schemas import UserRegister, UserRead, Token, TaskCreate, TaskRead
from auth import hash_password, verify_password, create_access_token, get_current_user

# Tworzy tabele w bazie automatycznie
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lab 3 FastAPI Security")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.scalar(select(models.User).where(models.User.email == data.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = models.User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/tasks", response_model=list[TaskRead])
def get_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tasks = db.scalars(select(models.Task).where(models.Task.user_id == current_user.id)).all()
    return tasks

@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = models.Task(
        title=data.title,
        completed=data.completed,
        priority=data.priority,
        user_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    task = db.scalar(select(models.Task).where(models.Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Weryfikacja właściciela zasobu – zwraca 403, jeśli próbujesz usunąć cudze zadanie
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this task")
        
    db.delete(task)
    db.commit()
    return None

import logging
import os
import time
from fastapi import Request

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("api")


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        ms,
    )
    return response
