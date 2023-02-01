import os

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from database import engine, SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv('.env') 

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
	return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
	user = db.query(models.User).filter(models.User.email == username).first()

	if not user:
		return False
	if not verify_password(password, user.hashed_password):
		return False
	return user

def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
	encode = {"sub": username, "id": user_id }
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=1000)
	encode.update({"exp": expire})
	return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is not None:
        return user
    raise http_exception()

async def get_current_user(token: str = Depends(oauth2_bearer)):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		user_id = payload.get("id")
		if username is None or user_id is None:
			raise get_user_exception()
		return {"username": username, "id": user_id}
	except JWTError:
		raise get_user_exception()


@app.post("/users/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": 201, "transaction": "successful" }


@app.post("/users/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session =  Depends(get_db)):
	user = authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise token_exception()
	token_expires = timedelta(minutes=20)
	token = create_access_token(user.email, user.id, expires_delta=token_expires)
	return {"token": token}


@app.put("/users/{user_id}")
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    user_to_update = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user_to_update is None:
        raise http_exception()
    
    user_to_update.email = user.email
    user_to_update.hashed_password = user.password
    db.add(user_to_update)
    db.commit()
    return {"status": 201, "transaction": "successful" }


def get_user_exception():
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"})
	return credentials_exception

def token_exception():
	token_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Incorrect email or password",
		headers={"WWW-Authenticate": "Bearer"})
	return token_exception

def http_exception():
    return HTTPException(status_code=404, detail="User not found")

