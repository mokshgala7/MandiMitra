from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserSignup, UserLogin, UserOut, Token
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user_required
from app.services.geocoding_service import GeocodingService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
geocoder = GeocodingService()

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserSignup, db: Session = Depends(get_db)):
    # Check if mobile exists
    if db.query(User).filter(User.mobile == user_in.mobile).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists."
        )

    # Check if email exists (if provided)
    if user_in.email and db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # Resolve coordinates if missing using fallback geocoding
    lat = user_in.latitude
    lng = user_in.longitude
    if lat is None or lng is None:
        coords = geocoder.geocode_address(user_in.state, user_in.district, user_in.village)
        if coords:
            lat = coords["latitude"]
            lng = coords["longitude"]

    hashed = hash_password(user_in.password)
    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        mobile=user_in.mobile,
        password_hash=hashed,
        state=user_in.state,
        district=user_in.district,
        village=user_in.village,
        primary_crop=user_in.primary_crop,
        latitude=lat,
        longitude=lng
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id)})
    return Token(access_token=token, user=UserOut.model_validate(new_user))

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    # User can log in via mobile or email
    user = db.query(User).filter(
        (User.mobile == login_in.username) | (User.email == login_in.username)
    ).first()

    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user_required)):
    return UserOut.model_validate(current_user)
