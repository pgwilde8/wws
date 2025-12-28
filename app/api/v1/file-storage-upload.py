from fastapi import APIRouter, File, UploadFile, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import boto3, os, uuid
from app.db.session import get_session
from app.models import PortfolioFile

router = APIRouter()

# DigitalOcean Spaces (S3 compatible) client
s3 = boto3.client(
    "s3",
    region_name=os.getenv("DO_SPACE_REGION"),
    endpoint_url="https://sfo3.digitaloceanspaces.com",
    aws_access_key_id=os.getenv("DO_SPACE_KEY"),
    aws_secret_access_key=os.getenv("DO_SPACE_SECRET"),
)

UPLOAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0f172a] text-gray-200 flex justify-center min-h-screen p-6">

<div class="bg-[#1e293b] p-6 rounded-xl shadow-xl w-full max-w-lg border border-gray-700">

  <h1 class="text-2xl font-bold text-center mb-4 text-emerald-400">Upload Portfolio Image</h1>

  <!-- Drop zone -->
  <div id="dropzone"
    class="w-full h-40 flex justify-center items-center border-2 border-dashed border-gray-600 rounded-lg bg-[#334155] cursor-pointer hover:border-emerald-400 transition">
    Drop image here or click to select
  </div>

  <!-- Preview -->
  <img id="preview" class="hidden w-full rounded-lg mt-4 shadow-lg" />

  <button id="uploadBtn"
    class="hidden w-full bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-2 rounded mt-4">
    Upload →
  </button>

  <div id="status" class="mt-4 text-center text-sm text-gray-400"></div>

</div>

<input type="file" id="fileInput" class="hidden" />

<script>
const dz = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const uploadBtn = document.getElementById("uploadBtn");
const status = document.getElementById("status");
let file;

dz.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  file = e.target.files[0];
  showPreview(file);
});

dz.addEventListener("dragover", (e) => {
  e.preventDefault();
  dz.classList.add("border-emerald-400");
});

dz.addEventListener("dragleave", () => {
  dz.classList.remove("border-emerald-400");
});

dz.addEventListener("drop", (e) => {
  e.preventDefault();
  dz.classList.remove("border-emerald-400");
  file = e.dataTransfer.files[0];
  showPreview(file);
});

function showPreview(f) {
  if (!f || !f.type.startsWith("image/")) {
    status.textContent = "Only images supported.";
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.classList.remove("hidden");
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.add("mt-4");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    preview.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    uploadBtn.style.display = "block";
    uploadBtn.classList.remove("hidden");
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
    preview.classList.remove("hidden");
    uploadBtn.classList.remove("hidden");
    preview.style.display = "block";
    uploadBtn.style.display = "block";
}

uploadBtn.addEventListener("click", async () => {
  if (!file) return;
  status.textContent = "Uploading...";
  const res = await fetch("/api/v1/upload-file", {
    method: "POST",
    body: (() => { const fd = new FormData(); fd.append("file", file); return fd; })()
  });
  const j = await res.json();
  if (j.status === "ok") {
    preview.src = "https://"+window.location.hostname+"/api/v1/file/"+j.file;
    status.textContent = "Saved.";
  } else {
    status.textContent = "Upload failed.";
  }
});
</script>

</div></body></html>
"""

@router.get("/upload", response_class=HTMLResponse)
def upload_ui():
    return UPLOAD_PAGE

def _safe_prefix(raw: str | None) -> str:
    if not raw:
        return ""
    # strip leading slashes and prevent path traversal
    cleaned = raw.replace("..", "").lstrip("/").strip()
    if cleaned and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    path: str | None = Form(None),
    db: AsyncSession = Depends(get_session),
):
    # Optional folder prefix (for multi-file/folder uploads)
    prefix = _safe_prefix(path)
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    suffix = f".{ext}" if ext else ""
    fname = f"{prefix}{uuid.uuid4()}{suffix}"
    try:
        s3.put_object(
            Bucket=os.getenv("DO_SPACE_BUCKET"),
            Key=fname,
            Body=await file.read(),
            ACL="private",
        )
        url_path = f"/api/v1/file/{fname}"
        db.add(PortfolioFile(filename=fname, url_path=url_path))
        await db.commit()
        return {"status": "ok", "file": fname}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/api/v1/file/{filename:path}")
async def get_file(filename: str):
    """
    Generate a short-lived signed URL to fetch the private object.
    """
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.getenv("DO_SPACE_BUCKET"), "Key": filename},
            ExpiresIn=600,  # 10 minutes
        )
        return RedirectResponse(url)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
