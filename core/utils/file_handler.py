import aiofiles
import os
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from typing import Optional

class FileHandler:
    def __init__(self, base_path: str = "uploads"):
        self.base_path = base_path
        
    async def save_file(self, file: UploadFile, category: str, filename: str) -> str:
        """Menyimpan file ke dalam direktori tertentu dengan nama yang diberikan."""
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
        category_path = Path(self.base_path) / category / year_month

        category_path.mkdir(parents=True, exist_ok=True)

        file_path = category_path / filename

        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Pastikan path dalam format Unix-style (untuk URL)
        return f"/{file_path.as_posix()}"
    
    
    @staticmethod
    def delete_image(file_url: str):
        """Hapus file dari sistem jika file_url adalah path lokal."""
        base_upload_dir = "uploads/events/"  # Sesuaikan dengan direktori penyimpanan
        
        # Konversi URL ke path file jika perlu
        file_path = os.path.join(base_upload_dir, os.path.basename(file_url))
        
        if os.path.exists(file_path):
            os.remove(file_path)