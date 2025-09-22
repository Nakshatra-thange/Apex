from .user_roles import UserRole

# ==============================================================================
# File Type Whitelist
# ==============================================================================
# Define allowed file extensions and their corresponding official MIME types.
# This acts as a strict whitelist for security. Only these files will be
# considered for upload.
ALLOWED_FILE_TYPES = {
    ".py": "text/x-python",
    ".js": "application/javascript",
    ".ts": "application/x-typescript",
    ".java": "text/x-java-source",
    ".cs": "text/plain",  # C#
    ".go": "text/x-go",
    ".rb": "application/x-ruby",
    ".php": "application/x-httpd-php",
    ".html": "text/html",
    ".css": "text/css",
    ".json": "application/json",
    ".sql": "application/sql",
    ".md": "text/markdown",
    ".txt": "text/plain",
}


# ==============================================================================
# File Size Limits
# ==============================================================================
# Define max file size in bytes for each user subscription tier.
# 1 KB = 1024 Bytes
# 1 MB = 1024 * 1024 Bytes
MAX_FILE_SIZE_BYTES = {
    UserRole.FREE_USER: 1024 * 100,          # 100 KB for free users
    UserRole.PREMIUM_USER: 1024 * 1024 * 2,  # 2 MB for premium users
    # Admins get the premium tier limit by default in our logic
}