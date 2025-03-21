from sqlalchemy.orm import Session
from BD.database import SessionLocal
from BD.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def crear_usuario_admin():
    db: Session = SessionLocal()
    try:
        if db.query(User).first() is None:
            admin_user = User(
                username="admin",
                nombre="Administrador",
                password=get_password_hash("admin"),  # Contraseña por defecto
                rol=1  # O el rol que consideres para admin
            )
            db.add(admin_user)
            db.commit()
        else:
            print("Ya existen usuarios registrados")
    finally:
        db.close()
