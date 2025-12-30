from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
import requests
from .scraper import parse_instagram, parse_facebook, parse_threads

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="api/static"), name="static")
templates = Jinja2Templates(directory="api/templates")

# PWA Support: Serve manifest and sw from root
@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("api/static/manifest.json", media_type="application/json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("api/static/sw.js", media_type="application/javascript")

class URLRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/analyze")
async def analyze_url(request: URLRequest):
    url = request.url
    print(f"Analyzing: {url}")
    
    try:
        if "instagram.com" in url:
            data = parse_instagram(url)
        elif "facebook.com" in url:
            data = parse_facebook(url)
        elif "threads.com" in url or "threads.net" in url:
            data = parse_threads(url)
        else:
            raise HTTPException(status_code=400, detail="Unsupported URL")
            
        if not data or data.get('error'):
            raise HTTPException(status_code=400, detail=data.get('error', 'Failed to parse'))
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxy_download")
async def proxy_download(url: str, name: str = None, inline: bool = False):
    """
    Proxy the download to avoid CORS/Referer issues on the client side.
    """
    try:
        # Mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.instagram.com/" 
        }
        
        r = requests.get(url, headers=headers, stream=True)
        r.raise_for_status()
        
        # Determine filename
        content_type = r.headers.get("content-type", "")
        ext = "mp4" if "video" in content_type else "jpg"
        if not name:
            filename = f"download.{ext}"
        else:
            filename = name if name.endswith(f".{ext}") else f"{name}.{ext}"

        disposition = "inline" if inline else f"attachment; filename={filename}"

        return StreamingResponse(
            r.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={"Content-Disposition": disposition}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
