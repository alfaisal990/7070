# Deployment Guide

Phoenix AI is designed as a local-first system. Follow these instructions to configure and deploy the services for production use.

## Local Deployment (Windows 11)

### 1. Python API Service
Start Uvicorn to serve the API in the background. Use the production flags:

```powershell
.venv\Scripts\python -m uvicorn ai_project.api.main:app --host 127.0.0.1 --port 8000 --workers 2 --log-level info
```

- `--workers 2`: Spawns multiple workers for handling concurrent requests.
- `--log-level info`: Prevents verbose debug prints in console logs.

### 2. Frontend React Service
Build the frontend and preview it or serve the production build using a lightweight web server (e.g. Nginx or IIS):

```bash
cd ai_project/dashboard
npm run build
npm run preview
```

## Running as Windows Service
To run the FastAPI backend as a persistent Windows Service, you can use **NSSM** (Non-Sucking Service Manager):

1. Download NSSM and open your terminal as Administrator.
2. Register the service:
   ```cmd
   nssm install PhoenixBackend
   ```
3. Set the following parameters:
   - **Path**: `c:\Users\1\Desktop\7070\.venv\Scripts\python.exe`
   - **Arguments**: `-m uvicorn ai_project.api.main:app --host 127.0.0.1 --port 8000`
   - **Startup Directory**: `c:\Users\1\Desktop\7070`
4. Start the service:
   ```cmd
   nssm start PhoenixBackend
   ```
