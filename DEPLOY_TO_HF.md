# 🚀 Deploying A.I.T.I.A to Hugging Face Spaces

This repository is already configured for a **Zero-Config Deployment**.

### Step 1: Push Changes
Ensure you have pushed the latest `Dockerfile` and `app.py` changes:
```bash
git push origin main
```

### Step 2: Create Space
1.  Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2.  **Name**: `AITIA-Control-Plane` (or similar).
3.  **SDK**: Select **Docker** (This is crucial!).
4.  **Hardware**: `CPU Basic` (Free) is sufficient.

### Step 3: Connect Code
*   **Easy Way**: Select "Public" and connect your GitHub repository: `veerryait/A.I.T.I.A--CLOUD`.
*   **Manual Way**:
    ```bash
    git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/AITIA-Control-Plane
    git push hf main
    ```

### Step 4: Configure Secrets (IMPORTANT)
Go to **Settings** > **Variables and secrets** in your HF Space.
*   New Secret: `GROQ_API_KEY`
*   Value: `(Your Groq API Key)`

### Step 5: Persistence (Optional)
To save your Vector DB between restarts:
1.  Go to **Settings** > **Persistent Storage**.
2.  Sign up for the "Small" tier (usually has a minimal cost, or skip if you don't need long-term memory).
3.  The app automatically detects `/data` and saves history there.

---
**That's it!** The "Smart Owl" will boot up in about 2 minutes. 🦉✨
