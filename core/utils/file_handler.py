import aiofiles
import os
from datetime import datetime
from fastapi import UploadFile
from typing import Optional

class FileHandler:
    def __init__(self, base_path: str = "uploads"):
        self.base_path = base_path
        
    async def save_file(self, file: UploadFile, category: str) -> str:
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
        category_path = os.path.join(self.base_path, category, year_month)
        
        os.makedirs(category_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}{file_extension}"
        
        file_path = os.path.join(category_path, new_filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        return f"/{file_path}"