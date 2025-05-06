import aiofiles
import os
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from typing import Optional
from PIL import Image
from io import BytesIO

class FileHandler:
    def __init__(self, base_path: str = "uploads"):
        self.base_path = base_path
        
    async def save_file(self, file: UploadFile, category: str, filename: str) -> str:
        """Menyimpan file ke dalam direktori tertentu dengan nama yang diberikan."""
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
        category_path = Path(self.base_path) / category / year_month
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Paksa simpan sebagai JPEG untuk kompresi
        file_path = category_path / Path(filename).with_suffix(".jpg")

        content = await file.read()

        # Jika file adalah gambar dan termasuk dalam kategori yang ditarget
        if file.content_type.startswith("image/") and category in ["news", "events", "finances"]:
            try:
                image = Image.open(BytesIO(content)).convert("RGB")

                # Simpan terkompresi sebagai JPEG
                with open(file_path, "wb") as f:
                    image.save(f, format="JPEG", quality=80, optimize=True)
                print(f"[INFO] Gambar dikompres dan disimpan ke {file_path}")
            except Exception as e:
                print(f"[ERROR] Gagal mengompres gambar: {e}")
                # Fallback
                async with aiofiles.open(file_path, 'wb') as out_file:
                    await out_file.write(content)
        else:
            # Simpan file secara biasa jika bukan target kategori/gambar
            print(f"[ERROR] Bukan gambar euy: {file.content_type}")
            async with aiofiles.open(file_path, 'wb') as out_file:
                await out_file.write(content)

        return f"/{file_path.as_posix()}"


        
    # async def save_file(self, file: UploadFile, category: str, filename: str) -> str:
    #     """Menyimpan file ke dalam direktori tertentu dengan nama yang diberikan."""
    #     today = datetime.now()
    #     year_month = today.strftime("%Y-%m")
    #     category_path = Path(self.base_path) / category / year_month

    #     category_path.mkdir(parents=True, exist_ok=True)

    #     file_path = category_path / filename

    #     async with aiofiles.open(file_path, 'wb') as out_file:
    #         content = await file.read()
    #         await out_file.write(content)

    #     # Pastikan path dalam format Unix-style (untuk URL)
    #     return f"/{file_path.as_posix()}"
    
    def _resize_and_crop_user(self, image: Image.Image) -> Image.Image:
        """Resize and crop to 4:3 aspect ratio, center crop, final size 400x300"""
        target_ratio = 4 / 3
        width, height = image.size
        current_ratio = width / height

        if current_ratio > target_ratio:
            # Crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            top, right, bottom = 0, left + new_width, height
        else:
            # Crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            left, right, bottom = 0, width, top + new_height

        image = image.crop((left, top, right, bottom))
        image = image.resize((400, 300))  # Resize to standard
        return image
    
    @staticmethod
    def delete_image(file_url: str):  # sourcery skip: use-string-remove-affix
        """Hapus file dari sistem penyimpanan jika file_url ada di folder uploads."""
        if file_url.startswith("/"):
            file_url = file_url[1:]  # Hilangkan '/' di awal agar cocok dengan path lokal
        
        file_path = Path(file_url)

        try:
            if file_path.exists():
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: gagal menghapus file {file_path} - {e}")
