# File: apex/backend/app/api_auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from jose import JWTError, jwt
from .rate_limiter import rate_limit
from . import crud, schemas, security, models
from .database import get_db
from .dependencies import get_current_user


router = APIRouter()


# --- THIS LINE IS NOW CORRECTED ---
@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    user_in: schemas.UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    existing_user = await crud.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    new_user = await crud.create_user(db=db, user=user_in)
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"user_id": str(user.id)})
    refresh_token = security.create_refresh_token(data={"user_id": str(user.id)})
    await crud.create_refresh_token(db=db, user_id=user.id, token=refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        max_age=security.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token/refresh", response_model=schemas.Token)
async def refresh_access_token(
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")
    try:
        payload = jwt.decode(refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        new_access_token = security.create_access_token(data={"user_id": user_id})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate refresh token")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if refresh_token:
        # In a real app, you would find and delete the hashed token from the DB.
        pass
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    request_data: schemas.PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_email(db, email=request_data.email)
    if user:
        token = await crud.create_password_reset_token(db, user_id=user.id)
        print("="*50)
        print(f"PASSWORD RESET EMAIL SIMULATION for {user.email}")
        print(f"Reset Token: {token}")
        print("Reset Link would be: http://frontend.com/reset-password?token=" + token)
        print("="*50)
    return {"message": "If an account with that email exists, we have sent a password reset link."}


@router.post("/password/reset", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_password_reset_token(db, token=reset_data.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )
    await crud.update_user_password(db, user=user, new_password=reset_data.new_password)
    return {"message": "Your password has been successfully reset."}


@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_user_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not security.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )
    await crud.update_user_password(db, user=current_user, new_password=password_data.new_password)
    return {"message": "Your password has been successfully changed."}

@router.post(
    "/login", 
    response_model=schemas.Token,
    # --- ADD THIS DEPENDENCY ---
    dependencies=[Depends(rate_limit("login"))]
)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # The user is passed in by the rate limiter's own dependency now,
    # so we can get it directly.
    # NOTE: This is a slight change in how we get the user.
    user = await crud.get_user_by_email(db, email=form_data.username)
    
    # ... (rest of the login function is identical) ...