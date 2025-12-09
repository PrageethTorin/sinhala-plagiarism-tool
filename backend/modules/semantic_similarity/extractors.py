# backend/semantic_similarity/extractors.py
import io
import PyPDF2
import docx

def extract_text_from_bytes(filename: str, content_bytes: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".txt"):
            try:
                return content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return content_bytes.decode("latin-1", errors="ignore")
        elif name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            pages = []
            for p in reader.pages:
                try:
                    pages.append(p.extract_text() or "")
                except Exception:
                    pages.append("")
            return "\n\n".join(pages)
        elif name.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content_bytes))
            paras = [p.text for p in doc.paragraphs if p.text]
            return "\n\n".join(paras)
        else:
            raise ValueError("Unsupported file type. Use .txt, .pdf, or .docx")
    except Exception as e:
        raise e
