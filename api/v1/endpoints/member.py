from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.user import User as UserModel, Member  # SQLAlchemy models
from ..schemas.user import User, MemberResponse, MemberCreate, MemberUpdate, UserCreate  # Pydantic schemas
from dateutil.relativedelta import relativedelta
import pytz

router = APIRouter()

# Fungsi helper untuk menghitung usia
def calculate_age_from_birthdate(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

@router.get("/", response_model=List[User])
@admin_required()
async def get_all_members(
    age_gt: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    query = db.query(UserModel).join(Member).filter(UserModel.role == "Member")

    if age_gt is not None:
        today = datetime.now()
        max_birth_date = today - relativedelta(years=age_gt)
        query = query.filter(Member.birth_date <= max_birth_date)

    users = query.all()

    return [
        User(
            id=user.id, # type: ignore
            username=user.username, # type: ignore # type: ignore
            role=user.role,
            member_info=MemberResponse.model_validate(user.member_info.__dict__)
            if user.member_info else None
        )
        for user in users
    ]
    
@router.get("/search", response_model=List[User])
async def search_members(
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(UserModel).join(Member).filter(UserModel.role == "Member")

    if name:
        search_pattern = f"%{name}%"
        query = query.filter(Member.full_name.ilike(search_pattern))

    query = query.order_by(Member.full_name.asc())
    
    users = query.all()
    return [
        User(
            id=user.id,
            username=user.username,
            role=user.role,
            member_info=MemberResponse.model_validate(user.member_info.__dict__)
            if user.member_info else None
        )
        for user in users
    ]

@router.get("/me", response_model=User)
def get_my_profile(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    member_data = None
    if db_user.member_info:
        member_dict = db_user.member_info.__dict__
        member_dict['age'] = calculate_age_from_birthdate(member_dict['birth_date'])
        member_data = MemberResponse.model_validate(member_dict)
    
    return User(
        id=db_user.id,
        username=db_user.username,
        role=db_user.role,
        member_info=member_data
    )
    
@router.post("/create_user", response_model=User)
@admin_required()
async def create_user_account(
    user_data: UserCreate,  # Schema untuk data akun
    biodata: MemberCreate,  # Schema untuk biodata member
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)  # Pastikan hanya admin yang bisa mengakses ini
):
    # Cek apakah username sudah ada
    if db.query(UserModel).filter(UserModel.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Membuat User baru
    new_user = UserModel(
        username=user_data.username,
        password=user_data.password,  # Hash password sebelum disimpan
        role="Member",  # Role untuk member
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Membuat biodata member
    member = Member(
        user_id=new_user.id,
        full_name=biodata.full_name,
        birth_place=biodata.birth_place,
        birth_date=biodata.birth_date,
        email=biodata.email,
        phone_number=biodata.phone_number,
        division=biodata.division,
        address=biodata.address,
        photo_url=biodata.photo_url
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return User(
        id=new_user.id, # type: ignore
        username=new_user.username,
        role=new_user.role,
        member_info=MemberResponse.model_validate(member.__dict__)
    )

@router.post("/biodata/", response_model=MemberResponse)
def create_biodata(
    biodata: MemberCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if db.query(Member).filter(Member.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Biodata already exists")
    
    member = Member(
        user_id=current_user.id,
        full_name=biodata.full_name,
        birth_place=biodata.birth_place,
        birth_date=biodata.birth_date,
        email=biodata.email,
        phone_number=biodata.phone_number,
        division=biodata.division,
        address=biodata.address,
        photo_url=biodata.photo_url if hasattr(biodata, 'photo_url') else None
    )
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return MemberResponse.model_validate(member.__dict__)

@router.put("/biodata/", response_model=MemberResponse)
async def update_biodata(
    biodata: MemberUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if current_user.role != "Admin" and member.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    update_data = biodata.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)
    
    db.commit()
    db.refresh(member)
    
    return MemberResponse.model_validate(member.__dict__)

@router.delete("/user/{user_id}")
@admin_required()
async def delete_user(
    user_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Use SQLAlchemy UserModel
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.delete("/delete_older_than_35", response_model=List[User])
@admin_required()
async def delete_users_older_than_35(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    today = datetime.now()
    max_birth_date = today - relativedelta(years=35)
    
    # Mencari user dengan usia lebih dari 35 tahun
    users_to_delete = db.query(UserModel).join(Member).filter(
        Member.birth_date <= max_birth_date
    ).all()

    if not users_to_delete:
        raise HTTPException(status_code=404, detail="No users older than 35 found")

    for user in users_to_delete:
        db.delete(user)
    
    db.commit()

    return {"message": f"Successfully deleted {len(users_to_delete)} users older than 35 years."}

