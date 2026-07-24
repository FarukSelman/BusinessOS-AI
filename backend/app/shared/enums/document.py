from enum import Enum


class DocumentStatus(str, Enum):

    UPLOADING = "UPLOADING"

    UPLOADED = "UPLOADED" 

    PROCESSING = "PROCESSING"

    READY = "READY"

    FAILED = "FAILED"