# backend/semantic_similarity/googledoc.py
import os

# This function uses service account json from SERVICE_ACCOUNT_FILE env var.
# If you do not use a service account, this will return "".
def fetch_google_doc_text_service(doc_id: str) -> str:
    try:
        svc_file = os.getenv("SERVICE_ACCOUNT_FILE")
        if not svc_file:
            return ""
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        SCOPES = ["https://www.googleapis.com/auth/documents.readonly", "https://www.googleapis.com/auth/drive.readonly"]
        creds = service_account.Credentials.from_service_account_file(svc_file, scopes=SCOPES)
        service = build("docs", "v1", credentials=creds)
        doc = service.documents().get(documentId=doc_id).execute()
        paragraphs = []
        for elem in doc.get("body", {}).get("content", []):
            if "paragraph" in elem:
                texts = []
                for run in elem["paragraph"].get("elements", []):
                    txt = run.get("textRun", {}).get("content")
                    if txt:
                        texts.append(txt)
                if texts:
                    paragraphs.append("".join(texts).strip())
        return "\n\n".join(p for p in paragraphs if p)
    except Exception:
        return ""
