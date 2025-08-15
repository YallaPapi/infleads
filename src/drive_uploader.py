"""
Google Drive uploader with service account support
"""

import os
import logging
from typing import Optional
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

logger = logging.getLogger(__name__)


class DriveUploader:
    """Upload files to Google Drive using service account or OAuth"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self):
        """Initialize Google Drive client"""
        self.service = self._get_drive_service()
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', None)
        logger.info("Drive uploader initialized")
    
    def _get_drive_service(self):
        """Get authenticated Drive service"""
        creds = None
        
        # First try service account (no popups)
        if os.path.exists('service_account.json'):
            logger.info("Using service account credentials")
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json',
                scopes=self.SCOPES
            )
        # Then try saved token
        elif os.path.exists('token.pickle'):
            logger.info("Using saved token")
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # Then try OAuth flow (will create popup on first run)
        elif os.path.exists('credentials.json'):
            logger.info("Using OAuth credentials")
            # Check if token needs refresh
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                # Use port 0 for automatic port selection to avoid conflicts
                creds = flow.run_local_server(
                    port=0,
                    success_message='Authorization successful! You can close this window.',
                    open_browser=True
                )
            # Save the credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        else:
            raise ValueError("No Google Drive credentials found. Please add service_account.json or credentials.json")
        
        return build('drive', 'v3', credentials=creds)
    
    def upload_file(self, filepath: str, filename: str) -> str:
        """
        Upload a file to Google Drive and return share link
        
        Args:
            filepath: Path to the file to upload
            filename: Name for the file in Drive
            
        Returns:
            Public share link
        """
        try:
            # File metadata
            file_metadata = {'name': filename}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            # Upload file
            media = MediaFileUpload(filepath, mimetype='text/csv')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"File uploaded with ID: {file_id}")
            
            # Make file publicly accessible
            self._set_public_permission(file_id)
            
            # Return the share link
            share_link = file.get('webViewLink')
            if not share_link:
                share_link = f"https://drive.google.com/file/d/{file_id}/view"
            
            return share_link
            
        except Exception as e:
            logger.error(f"Error uploading file to Drive: {e}")
            raise
    
    def _set_public_permission(self, file_id: str):
        """Set public read permission on a file"""
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            logger.info(f"Public permission set for file {file_id}")
        except Exception as e:
            logger.warning(f"Could not set public permission: {e}")
            # Continue anyway - file is still accessible to owner