from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
bearer_scheme = HTTPBearer()


#Importación de módulos
import BD.models as models
import schemas.schemas as schemas
from BD.database import get_db

#Funciones de utilidada
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta

router = APIRouter()

#MANEJO DE ERRORES
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas",
    headers={"WWW-Authenticate": "Bearer"},
)

#VARIABLES DE CONFIGURACIÓN
SECRET_KEY="0Sy-uWGUBFlZZTSynJ4LGhscSx-NKfO5oRoXEcbHYi8"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES= 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#Encriptación y validación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#Autenticacion de usuarios
def autenticacion_user(db: Session, usuario: str, password: str):
    user = db.query(models.User).filter(models.User.username == usuario).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def get_user_by_username(db: Session, usuario: str):
    return db.query(models.User).filter(models.User.username == usuario).first()


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

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is None:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.utcnow() + expires_delta
    # Agrega el tiempo de expiración y un identificador del tipo de token
    to_encode.update({"exp": expire, "type": "refresh"})
    refresh_token = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token

#Validación de tokens
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no contiene el usuario"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    return user

# Dependencia para verificar roles
def require_role(required_role: int):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.rol < required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción"
            )
        return current_user
    return role_checker



@router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = autenticacion_user(db, request.username, request.password)
    if not user:
        return {"mensaje": "Usuario o contraseña incorrectos"}
    
    access_token = create_access_token(data={"sub": user.username, "rol": user.rol, "type": "access"})
    refresh_token = create_refresh_token(data={"sub": user.username, "type": "refresh"})
    return {
        "mensaje": "Usuario autenticado",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register")
async def register(request: schemas.User, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == request.username).first()
    if existing_user:
        return {"mensaje": "El usuario ya existe"}

    user = models.User(username=request.username, nombre=request.nombre, password=get_password_hash(request.password), rol=request.rol)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuario creado exitosamente"}

@router.get("/users")
async def obtenerUsurs(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
def refresh(request_data: RefreshRequest, db: Session = Depends(get_db)):
    refresh_token = request_data.refresh_token
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        # Verifica que sea un refresh token
        if payload.get("type") != "refresh":
            logger.error("El token no es de tipo refresh. Payload: %s", payload)
            raise HTTPException(status_code=401, detail="El token no es de tipo refresh")
        
        username = payload.get("sub")
        if username is None:
            logger.error("Token inválido: no contiene 'sub'. Payload: %s", payload)
            raise HTTPException(status_code=401, detail="Token inválido (sin sub)")
        
        user = get_user_by_username(db, username)
        if user is None:
            logger.error("Usuario no encontrado para el token. Username: %s", username)
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
    except JWTError as e:
        # Registra el error con todos sus detalles
        logger.error("Error al decodificar el token: %s", e, exc_info=True)
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    # Generar un nuevo access token
    new_access_token = create_access_token(
        data={"sub": user.username, "rol": user.rol, "type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials  # Extrae el token de la cabecera "Authorization"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Verifica que sea un token de acceso
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="No es un access token válido")
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido (sin sub)")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Si llegaste aquí, el token es válido y es de tipo "access"
    return {"mensaje": f"Ruta protegida. Bienvenido, {username}."}