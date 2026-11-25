from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import BadRequestException


class FileValidator:

    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    ALLOWED_EXTENSIONS = {
        ".pdf",
    }

    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
    }

    @classmethod
    def validate(
        cls,
        file: UploadFile,
    ) -> None:

        if file.filename is None:

            raise BadRequestException(
                "Dosya adı eksik."
            )

        extension = Path(file.filename).suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:

            raise BadRequestException(
                "Yalnızca PDF dosyaları yüklenebilir."
            )

        if file.content_type not in cls.ALLOWED_CONTENT_TYPES:

            raise BadRequestException(
                "Geçersiz dosya türü."
            )

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size == 0:

            raise BadRequestException(
                "Dosya boş."
            )

        if size > cls.MAX_FILE_SIZE:

            raise BadRequestException(
                "Dosya boyutu 25 MB'ı aşıyor."
            )