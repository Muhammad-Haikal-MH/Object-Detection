# Road Damage Detection Web App

A full-stack portfolio web application that runs a YOLOv8 object detection model to identify **Potholes** and **Cracks** in road photos and videos.

## Features
- **Photo & Video Support**: Upload images (JPG/PNG) or videos (MP4) up to 50MB.
- **FastAPI Backend**: Uses Ultralytics YOLO to run inference and OpenCV for annotating the results with bounding boxes. Video processing utilizes ByteTrack to ensure unique objects aren't double-counted across frames.
- **React + Tailwind Frontend**: A sleek, dark-themed Single Page Application (SPA).
- **Fully Containerized**: Deploy easily with Docker Compose.

## How to Run with Docker

1. Ensure your model file is located in the root of this project (e.g., `best (4).pt`). The `docker-compose.yml` mounts this file into the backend container at `/app/models/best.pt`.
2. Open a terminal in this directory (`web apps road damages`).
3. Run:
   ```bash
   docker-compose up --build
   ```
4. Open your browser and navigate to `http://localhost`.

## Project Structure
- `backend/`: FastAPI application, Dockerfile, requirements.txt.
- `frontend/`: React SPA built with Vite and Tailwind CSS.
- `docker-compose.yml`: Brings up both services (backend on port 8000 internally, frontend on port 80).
