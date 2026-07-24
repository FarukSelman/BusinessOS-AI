from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from app.shared.storage.validator import FileValidator


UPLOAD_DIR = Path("storage/documents")


UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class StorageService:

    @staticmethod
    def save(
        file: UploadFile,
    ) -> tuple[str, str]:

        FileValidator.validate(file)

        extension = Path(file.filename).suffix.lower()

        filename = f"{uuid4()}{extension}"

        path = UPLOAD_DIR / filename

        with open(path, "wb") as buffer:
            buffer.write(file.file.read())

        return filename, str(path)

    @staticmethod
    def delete(path: str):

        file = Path(path)

        if file.exists():
            file.unlink()