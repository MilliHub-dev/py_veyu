"""
Log file service layer for the web log viewer system.
Provides secure access to application log files with validation and parsing capabilities.
"""

import os
import re
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from django.conf import settings
from django.utils import timezone


@dataclass
class LogEntry:
    """Represents a single log entry with parsed components."""
    timestamp: Optional[datetime]
    level: str
    message: str
    raw_line: str
    line_number: int


@dataclass
class LogFileInfo:
    """Metadata information about a log file."""
    filename: str
    full_path: str
    size: int
    last_modified: datetime
    line_count: int
    is_accessible: bool


class LogFileService:
    """Service class for managing log file operations."""
    
    # Whitelist of allowed log files for security
    ALLOWED_LOG_FILES = [
        'api.log',
        'auth.log', 
        'cloudinary.log',
        'database.log',
        'django.log',
        'email.log',
        'errors.log',
        'security.log'
    ]
    
    def __init__(self):
        """Initialize the log file service with the logs directory."""
        self.logs_directory = getattr(settings, 'LOG_DIRECTORY', Path(settings.BASE_DIR) / 'logs')
        if isinstance(self.logs_directory, str):
            self.logs_directory = Path(self.logs_directory)
    
    def get_available_logs(self) -> List[LogFileInfo]:
        """
        Scan the logs directory and return metadata for all accessible log files.
        
        Returns:
            List[LogFileInfo]: List of log file metadata objects
        """
        log_files = []
        
        if not self.logs_directory.exists():
            return log_files
        
        # First, check whitelisted files
        for filename in self.ALLOWED_LOG_FILES:
            file_path = self.logs_directory / filename
            if file_path.exists() and file_path.is_file():
                try:
                    file_info = self.get_file_info(filename)
                    if file_info:
                        log_files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files that can't be accessed
                    continue
        
        # Also scan for any .log files in the directory (for dynamic discovery)
        try:
            for file_path in self.logs_directory.glob('*.log'):
                if file_path.is_file() and file_path.name not in self.ALLOWED_LOG_FILES:
                    # Add discovered log files to the whitelist dynamically
                    try:
                        file_info = LogFileInfo(
                            filename=file_path.name,
                            full_path=str(file_path),
                            size=file_path.stat().st_size,
                            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.get_current_timezone()),
                            line_count=self._count_lines(file_path),
                            is_accessible=True
                        )
                        log_files.append(file_info)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
                    
        return sorted(log_files, key=lambda x: x.last_modified, reverse=True)
    
    def get_file_info(self, filename: str) -> Optional[LogFileInfo]:
        """
        Get metadata information for a specific log file.
        
        Args:
            filename: Name of the log file
            
        Returns:
            LogFileInfo: File metadata or None if file is not accessible
        """
        if not self.validate_file_access(filename):
            return None
            
        file_path = self.logs_directory / filename
        
        try:
            stat = file_path.stat()
            line_count = self._count_lines(file_path)
            
            return LogFileInfo(
                filename=filename,
                full_path=str(file_path),
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone()),
                line_count=line_count,
                is_accessible=True
            )
        except (OSError, PermissionError):
            return LogFileInfo(
                filename=filename,
                full_path=str(file_path),
                size=0,
                last_modified=timezone.now(),
                line_count=0,
                is_accessible=False
            )
    
    def read_log_file(self, filename: str, start_line: int = 1, end_line: Optional[int] = None) -> List[LogEntry]:
        """
        Read log file content with line range support.
        
        Args:
            filename: Name of the log file
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based), None for end of file
            
        Returns:
            List[LogEntry]: List of parsed log entries
        """
        if not self.validate_file_access(filename):
            return []
            
        file_path = self.logs_directory / filename
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                lines = file.readlines()
                
            # Handle line range
            if end_line is None:
                end_line = len(lines)
                
            # Convert to 0-based indexing and validate range
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            if start_idx >= len(lines):
                return []
                
            # Parse the selected lines
            log_entries = []
            parser = LogParser()
            
            for i in range(start_idx, end_idx):
                line = lines[i].rstrip('\n\r')
                if line.strip():  # Skip empty lines
                    entry = parser.parse_line(line, i + 1)
                    log_entries.append(entry)
                    
            return log_entries
            
        except FileNotFoundError as e:
            # Log the error to security log if possible
            self._log_security_event(f"File not found when reading log file {filename}: {str(e)}")
            return []
        except PermissionError as e:
            # Log the error to security log if possible
            self._log_security_event(f"Permission denied reading log file {filename}: {str(e)}")
            return []
        except UnicodeDecodeError as e:
            # Log the error to security log if possible
            self._log_security_event(f"Encoding error reading log file {filename}: {str(e)}")
            return []
        except OSError as e:
            # Log the error to security log if possible
            self._log_security_event(f"OS error reading log file {filename}: {str(e)}")
            return []
    
    def validate_file_access(self, filename: str) -> bool:
        """
        Validate that a log file can be safely accessed.
        
        Args:
            filename: Name of the log file to validate
            
        Returns:
            bool: True if file access is allowed, False otherwise
        """
        # Prevent path traversal attacks
        if '..' in filename or '/' in filename or '\\' in filename:
            self._log_security_event(f"Path traversal attempt detected: {filename}")
            return False
        
        # Only allow .log files
        if not filename.endswith('.log'):
            self._log_security_event(f"Attempted access to non-log file: {filename}")
            return False
            
        # Check if file exists and is readable
        file_path = self.logs_directory / filename
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Ensure file is within the logs directory (additional security check)
        try:
            file_path.resolve().relative_to(self.logs_directory.resolve())
        except ValueError:
            self._log_security_event(f"File outside logs directory: {filename}")
            return False
            
        try:
            # Test read access
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Try to read one character
            return True
        except (OSError, PermissionError):
            return False
    
    def _count_lines(self, file_path: Path) -> int:
        """
        Count the number of lines in a file efficiently.
        
        Args:
            file_path: Path to the file
            
        Returns:
            int: Number of lines in the file
        """
        try:
            with open(file_path, 'rb') as f:
                count = sum(1 for _ in f)
            return count
        except (OSError, PermissionError):
            return 0
    
    def _log_security_event(self, message: str) -> None:
        """
        Log security events to the security log file.
        
        Args:
            message: Security event message to log
        """
        try:
            security_log_path = self.logs_directory / 'security.log'
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] LOG_VIEWER: {message}\n"
            
            with open(security_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except (OSError, PermissionError):
            # If we can't log to security.log, there's not much we can do
            pass


class LogParser:
    """Parser class for extracting structured information from log entries."""
    
    # Common log level patterns
    LOG_LEVEL_PATTERNS = [
        r'\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b',
        r'\b(debug|info|warning|error|critical)\b',
        r'\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]',
        r'\[(debug|info|warning|error|critical)\]',
    ]
    
    # Common timestamp patterns
    TIMESTAMP_PATTERNS = [
        # Django format: [15/Nov/2024 10:30:15]
        r'\[(\d{1,2}/\w{3}/\d{4} \d{1,2}:\d{2}:\d{2})\]',
        # ISO format: 2024-11-15 10:30:15
        r'(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2})',
        # ISO with microseconds: 2024-11-15 10:30:15.123456
        r'(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}\.\d+)',
        # Syslog format: Nov 15 10:30:15
        r'(\w{3} \d{1,2} \d{1,2}:\d{2}:\d{2})',
    ]
    
    def parse_line(self, line: str, line_number: int) -> LogEntry:
        """
        Parse a single log line to extract structured information.
        
        Args:
            line: Raw log line text
            line_number: Line number in the file
            
        Returns:
            LogEntry: Parsed log entry object
        """
        timestamp = self.extract_timestamp(line)
        level = self.extract_level(line)
        
        # Extract message by removing timestamp and level from the line
        message = self._extract_message(line, timestamp, level)
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            raw_line=line,
            line_number=line_number
        )
    
    def detect_log_format(self, filename: str) -> str:
        """
        Detect the log format based on filename and content patterns.
        
        Args:
            filename: Name of the log file
            
        Returns:
            str: Detected log format identifier
        """
        # Simple format detection based on filename
        format_mapping = {
            'django.log': 'django',
            'api.log': 'django',
            'auth.log': 'django',
            'cloudinary.log': 'django',
            'database.log': 'django',
            'email.log': 'django',
            'errors.log': 'django',
            'security.log': 'syslog'
        }
        
        return format_mapping.get(filename, 'generic')
    
    def extract_timestamp(self, line: str) -> Optional[datetime]:
        """
        Extract timestamp from a log line.
        
        Args:
            line: Log line text
            
        Returns:
            datetime: Parsed timestamp or None if not found
        """
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                return self._parse_timestamp(timestamp_str)
        
        return None
    
    def extract_level(self, line: str) -> str:
        """
        Extract log level from a log line.
        
        Args:
            line: Log line text
            
        Returns:
            str: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or 'INFO' as default
        """
        for pattern in self.LOG_LEVEL_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Default to INFO if no level found
        return 'INFO'
    
    def _extract_message(self, line: str, timestamp: Optional[datetime], level: str) -> str:
        """
        Extract the message content by removing timestamp and level prefixes.
        
        Args:
            line: Original log line
            timestamp: Extracted timestamp
            level: Extracted log level
            
        Returns:
            str: Cleaned message content
        """
        message = line
        
        # Remove timestamp patterns
        for pattern in self.TIMESTAMP_PATTERNS:
            message = re.sub(pattern, '', message)
        
        # Remove level patterns
        for pattern in self.LOG_LEVEL_PATTERNS:
            message = re.sub(pattern, '', message, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and common separators
        message = re.sub(r'^[\s\-:]+', '', message)
        message = re.sub(r'[\s]+', ' ', message)
        
        return message.strip()
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string into datetime object.
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            datetime: Parsed datetime or None if parsing fails
        """
        # Common timestamp formats to try
        formats = [
            '%d/%b/%Y %H:%M:%S',  # Django: 15/Nov/2024 10:30:15
            '%Y-%m-%d %H:%M:%S',  # ISO: 2024-11-15 10:30:15
            '%Y-%m-%d %H:%M:%S.%f',  # ISO with microseconds
            '%b %d %H:%M:%S',  # Syslog: Nov 15 10:30:15
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp_str, fmt)
                # For syslog format without year, assume current year
                if fmt == '%b %d %H:%M:%S':
                    parsed = parsed.replace(year=timezone.now().year)
                
                # Make timezone aware
                return timezone.make_aware(parsed)
            except ValueError:
                continue
        
        return None