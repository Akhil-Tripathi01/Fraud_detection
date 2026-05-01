from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import models
import schemas
from auth_utils import create_access_token, get_current_user, hash_password, verify_password
from database import get_db

router = APIRouter()


def token_for_user(user: models.User) -> schemas.TokenResponse:
    token = create_access_token({"sub": user.username, "role": user.role, "user_id": user.id})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = (
        db.query(models.User)
        .filter((models.User.username == payload.username) | (models.User.email == payload.email))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists.")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role or "investigator",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "form" in content_type:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
    else:
        payload = await request.json()
        username = payload.get("username")
        password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=422, detail="Username and password are required.")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")

    return token_for_user(user)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
