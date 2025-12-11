# time the client has between pre-signing the file and uploading it
SignedUrlExpirationTime = 300  # seconds, 5 minutes


class FileMetadata:
    station_id: str
    camera_id: str
    date: str  # format: DD-MM-YYYY
    max_size_mb: int
    name: str


class FileResult:
    url: str


class FileUploaderProvider:
    """Base class for file uploader providers."""

    def presigned_url(self, metadata: FileMetadata) -> FileResult:
        """Presigned a file to upload subsequently

        Args:
            payload (FileMetadata): The metadata about the file to upload

        Returns:
            str: The URL or path of the uploaded file.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
