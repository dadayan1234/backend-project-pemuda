from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
from datetime import datetime
from core.security import verify_token
from ..models.user import User

router = APIRouter()

UPLOAD_DIRECTORY = "uploads"

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(verify_token)):
    try:
        today = datetime.today()
        year_month = today.strftime("%Y-%m")
        sub_directory = os.path.join(UPLOAD_DIRECTORY, year_month)
        
        if not os.path.exists(sub_directory):
            os.makedirs(sub_directory)
        
        file_location = os.path.join(sub_directory, file.filename)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        
        return {"info": f"file '{file.filename}' saved at '{file_location}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))