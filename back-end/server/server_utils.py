from passlib.context import CryptContext
from jose import jwt
from datetime import datetime,timedelta,timezone
from fastapi import Depends,HTTPException,WebSocket
from bd_initialization.Bridge import get_session
from fastapi.requests import Request
from bd_initialization.DataBase_models import Admin
import cv2
import easyocr
from datetime import datetime


context=CryptContext(schemes=["bcrypt"],deprecated="auto")
def hash_password(password):
    return context.hash(password)

def verify_password(password,hashed_password):
    return context.verify(password,hashed_password)


ALGO="HS256"

def expire_time():
    return datetime.now(timezone.utc)+timedelta(minutes=300)


def create_token(data:dict):
    try:
        to_encode=data.copy()
        to_encode.update({
            "exp":expire_time()
        })
        return jwt.encode(to_encode,key="secret_key",algorithm=ALGO)
    except Exception:
     raise(HTTPException(status_code=401,detail="erreur lors de la creation du token"))
        

ALGO="HS256"
def get_current_admin(request:Request,database=Depends(get_session)):
   access_token=request.cookies.get("access_token")
   if not access_token:
      raise HTTPException(status_code=401, detail="Token manquant")
   user_data=jwt.decode(access_token,key="secret_key",algorithms=ALGO)

   if user_data:
       user = database.query(Admin).filter(
            Admin.id == user_data["id"]
        ).first()

       return user
   else:
      raise HTTPException(status_code=401,detail="invalid token")




def get_admin_from_ws(websocket: WebSocket, database=Depends(get_session)):
    # 1. On récupère le token depuis les COOKIES de la requête WebSocket
    access_token = websocket.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Token manquant")
        
    user_data = jwt.decode(access_token, key="secret_key", algorithms=[ALGO])
        
    if user_data:
            user = database.query(Admin).filter(
                Admin.id == user_data["id"]
            ).first()
            
            return user

    else:
            raise HTTPException(status_code=401, detail="Token invalide: ID manquant")
            


            


            
                    

    

