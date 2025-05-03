# God's Eye - Real-Time Person Identification System

**God's Eye** is a real-time person identification system that utilizes camera feeds to extract, process, and match faces against a vectorized database of known or missing persons.

This full-stack application integrates:

* **FastAPI** (Python) backend
* **Vue.js** frontend
* **YOLOv11-face** and **FaceNet** models for face detection and recognition
* **SQL Database** for user authentication
* **ChromaDB** for vector storage and similarity search
* **File storage** system for storing frame data from camera feeds

---

## 📂 Project Structure

```
├── backend
│   ├── database
│   ├── dataHandlers
│   ├── dist
│   ├── utilities
│   ├── main.py
│   ├── missing.mp4
│   ├── requirements.txt
│   ├── README.md
│   └── yolov11n-face.pt
│
├── frontend
│   ├── node_modules
│   ├── public
│   ├── src
│   ├── babel.config.js
│   ├── jsconfig.json
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   └── vue.config.js
│
├── .gitignore
└── LICENSE
```

---

## ⚙️ Features

* **Real-Time Face Detection**: YOLOv11-face model detects faces in live camera feeds.
* **Face Recognition**: FaceNet encodes faces into vectors for comparison.
* **Vector Database**: ChromaDB stores face embeddings and supports fast similarity searches.
* **User Authentication**: SQL database manages user accounts and logins.
* **Video Frame Storage**: Stores frames extracted from camera feeds for offline analysis.
* **Modern Frontend**: Vue.js interface to visualize and interact with results.

---

## 🚀 Deployment Guide

### 1️⃣ Configure Environment Variables

Create a `.env` file in the `backend` directory and configure your environment variables:

```
DB_URL=sqlite:///./users.db
CHROMADB_PATH=./chroma_db
CAMERA_FEED_URL=rtsp://... or file path
SECRET_KEY=your-secret-key
```

### 2️⃣ Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start FastAPI application
uvicorn main:app --reload
```

### 3️⃣ Frontend Setup (Vue.js)

```bash
cd frontend
npm install
npm run deploy
```

---

## 🛠️ Technologies Used

* **Backend**: FastAPI, SQLAlchemy, ChromaDB
* **Frontend**: Vue.js, Vue Router
* **Machine Learning**: YOLOv11-face, FaceNet
* **Database**: SQLite (users), ChromaDB (vectors)
* **Other**: Uvicorn, Pydantic, OpenCV

---

## 📸 How It Works

1. **Camera Feed Input**: Stream is processed frame-by-frame.
2. **Face Detection**: YOLO model detects and crops faces.
3. **Face Embedding**: FaceNet converts faces into numerical embeddings.
4. **Similarity Search**: Embeddings are compared against ChromaDB to find matches.
5. **Frontend Visualization**: Matched information and statistics are displayed on the dashboard.

---

## 📄 License

This project is licensed under the MIT License.