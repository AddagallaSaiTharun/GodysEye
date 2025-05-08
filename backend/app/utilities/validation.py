from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.utilities import config
from app.utilities.logger_config import logger

security = HTTPBearer()

def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    
    logger.debug(f"Auth scheme: '{authorization.scheme.lower()}'")
    logger.debug(f"Token: {authorization.credentials}")

    if authorization.scheme.lower() != "bearer":
        logger.error("Invalid authentication scheme")
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    token = authorization.credentials
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="user_id not found")
        return user_id
    except jwt.ExpiredSignatureError as err:
        logger.error(f"Problem with JWTToken:{str(err)}")
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as err:
        logger.error(f"Problem with JWTToken:{str(err)}")
        raise HTTPException(status_code=401, detail="Invalid token")