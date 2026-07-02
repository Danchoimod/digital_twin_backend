# FastAPI + Google Cloud Platform Setup

A production-ready FastAPI application template optimized for deployment to Google Cloud Run.

## Project Structure

```
backend_twin_frontend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application initialization & routes
│   ├── config.py        # Configuration management with pydantic-settings
│   └── routers/         # Endpoint submodules
│       ├── __init__.py
│       └── items.py     # Sample endpoint router
├── Dockerfile           # Optimized for GCP Cloud Run
├── .dockerignore        # Prevents unnecessary files in container
├── .gitignore
├── requirements.txt     # Python dependencies
└── README.md            # Setup and deployment guides
```

---

## Local Development

### 1. Using a Local Virtual Environment

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```
Visit http://127.0.0.1:8000/docs to explore the interactive API docs.

---

### 2. Using Docker

Build the Docker image:
```bash
docker build -t fastapi-gcp-app .
```

Run the Docker container locally (binding to port `8080` to simulate GCP Cloud Run):
```bash
docker run -p 8080:8080 -e PORT=8080 fastapi-gcp-app
```
Verify the health check by navigating to: http://localhost:8080/health

---

## Deploying to Google Cloud Platform (Cloud Run)

Google Cloud Run is the recommended serverless container platform for running FastAPI applications.

### Prerequisites
1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
2. Run `gcloud auth login` to authenticate.
3. Set your active project:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Quick Deploy (Build & Host on GCP)

You can build and deploy the container in a single command using Google Cloud Build and Cloud Run:

```bash
gcloud run deploy fastapi-service --source . --region us-central1 --allow-unauthenticated
```

- `--source .`: Instructs GCP to package the local files and build the container image in the cloud.
- `--region us-central1`: Sets the target deployment region.
- `--allow-unauthenticated`: Makes the endpoint publicly accessible.

Once completed, the CLI will output a secure HTTPS URL (e.g., `https://fastapi-service-xxxxxx-uc.a.run.app`) where your FastAPI app is hosted.
