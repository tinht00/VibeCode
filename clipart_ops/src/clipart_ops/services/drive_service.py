"""Upload marketing assets lên Google Drive và resolve media URL."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

from clipart_ops.domain.models import DriveAsset
from clipart_ops.services.workspace_service import WorkspaceService

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None
    MediaFileUpload = None


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveService:
    """Tích hợp Google Drive có fallback rõ ràng khi thiếu deps/secret."""

    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service
        self.client_secret = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET", "").strip()
        self.token_path = Path.home() / ".clipart_ops" / "drive_token.json"

    def upload_marketing_assets(self, topic_root: Path) -> list[DriveAsset]:
        if not all([build, InstalledAppFlow, MediaFileUpload]):
            raise RuntimeError("Thiếu thư viện Google Drive. Hãy cài dependency đầy đủ.")
        if not self.client_secret:
            raise RuntimeError("Thiếu GOOGLE_DRIVE_CLIENT_SECRET.")

        service = self._build_service()
        topic = self.workspace_service.scan_topic(topic_root)
        parent_folder_id = self._ensure_folder(service, "ClipartOps Marketing", "")
        topic_folder_id = self._ensure_folder(service, topic.name, parent_folder_id)
        assets: list[DriveAsset] = []

        for image_path in self.workspace_service.find_images(topic.paths.marketing_watermark):
            assets.append(self._upload_file(service, image_path, topic_folder_id))

        self.workspace_service.write_json(
            topic_root / "drive_assets.json",
            {"assets": [asset.model_dump() for asset in assets]},
        )
        return assets

    def validate_media_url(self, url: str) -> tuple[bool, str]:
        try:
            response = httpx.get(
                url,
                follow_redirects=True,
                timeout=30.0,
                headers={"User-Agent": "ClipartOps/0.1"},
            )
            content_type = response.headers.get("content-type", "").lower()
            is_valid = response.status_code == 200 and content_type.startswith("image/")
            return is_valid, content_type
        except Exception as exc:
            return False, str(exc)

    def _build_service(self) -> Any:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        creds = None
        if self.token_path.exists() and Credentials is not None:
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if creds and creds.expired and creds.refresh_token and Request is not None:
            creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret, SCOPES)
            creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")
        return build("drive", "v3", credentials=creds)

    def _ensure_folder(self, service: Any, name: str, parent_id: str) -> str:
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get("files", [])
        if files:
            return files[0]["id"]
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            metadata["parents"] = [parent_id]
        created = service.files().create(body=metadata, fields="id").execute()
        return created["id"]

    def _upload_file(self, service: Any, file_path: Path, parent_id: str) -> DriveAsset:
        metadata = {"name": file_path.name, "parents": [parent_id]}
        media = MediaFileUpload(str(file_path), resumable=True)
        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id, name, mimeType, webViewLink, webContentLink",
        ).execute()
        service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()
        resolved_url = file.get("webContentLink") or f"https://drive.google.com/uc?id={file['id']}&export=download"
        is_valid, detail = self.validate_media_url(resolved_url)
        return DriveAsset(
            file_name=file_path.name,
            local_path=str(file_path),
            drive_file_id=file["id"],
            web_view_link=file.get("webViewLink", ""),
            web_content_link=file.get("webContentLink", ""),
            resolved_media_url=resolved_url,
            media_url_status="valid" if is_valid else "invalid",
            mime_type=file.get("mimeType", detail if is_valid else ""),
            error="" if is_valid else detail,
        )
