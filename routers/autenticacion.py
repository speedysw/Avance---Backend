from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext

#Importación de módulos
import BD.models as models
import schemas.schemas as schemas
from BD.database import get_db

#Funciones de utilidada
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta

router = APIRouter()

#VARIABLES DE CONFIGURACIÓN
SECRET_KEY="FIRMA_SECRETA"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

oauth2_scheme = OAuth2PasswordBearer("/login")

#Encriptación y validación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#Autenticacion de usuarios
def autenticacion_user(db: Session , password: str, usuario: str):
    user = db.query(models.User).filter(models.User.username == usuario).first()
    if not user:
        return None
    return user

#Creación de tokens para los usuarios
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is None:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    token_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt

#Validación de tokens
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = JWTError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = autenticacion_user(db, username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = autenticacion_user(db, request.username, request.password)
    if not user:
        return {"mensaje": "Usuario o contraseña incorrectos"}
    
    access_token = create_access_token(data={"sub": user.username})
    return {"mensaje": "Usuario autenticado", "token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(request: schemas.User, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == request.username).first()
    if existing_user:
        return {"mensaje": "El usuario ya existe"}

    user = models.User(username=request.username, nombre=request.nombre, password=get_password_hash(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuario creado exitosamente"}
