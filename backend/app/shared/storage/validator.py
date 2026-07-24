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
                "Filename is missing."
            )

        extension = Path(file.filename).suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:

            raise BadRequestException(
                "Only PDF files are allowed."
            )

        if file.content_type not in cls.ALLOWED_CONTENT_TYPES:

            raise BadRequestException(
                "Invalid file type."
            )

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size == 0:

            raise BadRequestException(
                "File is empty."
            )

        if size > cls.MAX_FILE_SIZE:

            raise BadRequestException(
                "File size exceeds 25 MB."
            )