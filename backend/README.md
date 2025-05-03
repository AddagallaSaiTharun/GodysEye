# Backend Deployment Guide

This document outlines all necessary steps to deploy the **God's Eye backend**, powered by FastAPI, SQL database, YOLOv11-face, FaceNet, ChromaDB, and file storage utilities.

## ⚙️ Prerequisites

Ensure you have the following installed:

* Python 3.12+
* pip (Python package manager)
* Git (optional)
* Virtualenv (recommended)
* FFmpeg (if processing video feeds)
* CUDA (if using GPU acceleration for YOLO/FaceNet models)

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/AddagallaSaiTharun/GodysEye.git
cd backend
```

## 2️⃣ Set Up Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
touch .env
```

Add the following variables (modify values as per your setup):

```ini
DB_URL=sqlite:///./users.db
CHROMADB_PATH=./chroma_db
CAMERA_FEED_URL=rtsp://<your-camera-stream>  # or local file path
SECRET_KEY=your-secret-key
```

## 5️⃣ Initialize Databases

Ensure SQL database and ChromaDB are initialized:

```bash
# SQL Database setup (for user authentication)
python
>>> from database import models
>>> from database.database import engine
>>> models.Base.metadata.create_all(bind=engine)
>>> exit()

# ChromaDB setup (it will auto-initialize on first run)
```

## 6️⃣ Verify ML Models

Ensure `yolov11n-face.pt` is placed in the `backend` root folder.
If required, download FaceNet weights (if they aren’t auto-downloaded by your code).

## 7️⃣ Start FastAPI Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 8️⃣ Optional: Run Cleanup Script

To clear old uploads or temporary files:

```bash
./cleanup.bat   # On Windows
bash cleanup.sh # If you create a Unix version
```

## 9️⃣ Test API Endpoints

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the auto-generated Swagger UI and test APIs.

## 🛠️ Useful Commands

* Stop FastAPI server: `CTRL+C`
* Deactivate virtualenv: `deactivate`
* Reactivate virtualenv: `source venv/bin/activate`

## 🚀 Production Deployment (Optional)

For production deployments, consider using:

* **Gunicorn + Uvicorn workers**
* **Docker** containerization
* **NGINX** as a reverse proxy
* **Supervisor** or **systemd** for service management

Example Gunicorn launch:

```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

---

Your backend API should now be running and ready to connect with the frontend or external clients!
