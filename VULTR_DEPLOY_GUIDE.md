# Complete Vultr Deployment Guide (From Scratch)

This guide provides step-by-step instructions to host your Ayureze AI Backend on Vultr using Docker. This setup ensures the background processes run 24/7 and restart automatically if the server reboots.

---

## Phase 1: Vultr Server Selection

1. **Login to Vultr**: Go to [vultr.com](https://www.vultr.com/).
2. **Deploy Server**:
   - **Choose Server**: `Cloud Compute`.
   - **CPU Architecture**: `Intel` or `AMD High Performance`.
   - **Server Location**: Choose the one closest to your users (e.g., Mumbai, Singapore).
   - **Server Image**: `Ubuntu 22.04 LTS x64`.
   - **Server Size**: **IMPORTANT** Select at least **8GB RAM / 4 vCPU** ($40/month or $48/month High Performance). 
   - **Additional Features**: Enable `Auto Backups` (Recommended).
   - **SSH Keys**: Add your SSH key for secure access.
3. **Deploy Now**.

---

## Phase 2: Initial Server Setup

Once your server is running, copy the IP address and connect via SSH:

```bash
# Replace 'YOUR_SERVER_IP' with the IP from Vultr dashboard
ssh root@YOUR_SERVER_IP
```

Inside the server, run these commands to install Docker:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
apt install -y docker.io docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker
```

---

## Phase 3: Project Deployment

### 1. Upload Code to Server
On your **local machine** (where the code is currently), use `scp` or `git` to upload the files. 

If you use `git`, push your code to GitHub/GitLab and clone it on the server:
```bash
# Inside the Vultr server
git clone <your-repo-URL> /app
cd /app
```

### 2. Configure Environment Variables
You MUST create a `.env` file on the server. You can copy your local one:

```bash
nano .env
```
Paste your environment variables (Supabase keys, Shopify tokens, etc.) and press `Ctrl+O`, `Enter`, `Ctrl+X` to save.

---

## Phase 4: Running the Backend

We will use Docker Compose to run the app in the background.

```bash
# Build and start the container in detached mode (-d)
docker-compose up --build -d
```

### Check if it's running:
```bash
# See running containers
docker ps

# View logs to ensure model is loading
docker-compose logs -f backend
```

Your API is now live at: `http://YOUR_SERVER_IP:5000`

---

## Phase 5: Verification

Use `Postman` or `curl` to test the health check:

```bash
curl http://YOUR_SERVER_IP:5000/health
```

Expected Response:
```json
{"status": "loading", "model_loaded": false, ...}
```
*(It will say `loading` for 5-10 minutes while the Llama model downloads and initializes on the CPU.)*

---

## Phase 6: Automatic Restarts
Since we used `restart: always` in `docker-compose.yml`, your backend will:
- Restart if it crashes.
- Restart if the server reboots.
- Run entirely in the background.

---

## Phase 7: SSL Setup (HTTPS)

To secure your API with HTTPS (Required for web apps and Shopify webhooks), follow these steps:

1. **Point Domain**: In your domain registrar, add an **A Record** pointing `api.yourdomain.com` to your Vultr IP.
2. **Install Nginx & Certbot**:
   ```bash
   apt install -y nginx certbot python3-certbot-nginx
   ```
3. **Configure Nginx**:
   Use the `nginx.conf` provided in this folder. Copy it to `/etc/nginx/nginx.conf` (or use the Docker setup).
4. **Obtain SSL Certificate**:
   ```bash
   certbot --nginx -d api.yourdomain.com
   ```
5. **Restart Docker**:
   ```bash
   docker-compose restart
   ```

Your API will now be available at `https://api.yourdomain.com`.

---

## Folder Structure for Deployment

Ensure your server has this structure:
```
/app
├── main.py
├── .env
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── app/ (The entire logic folder)
```

---

> [!IMPORTANT]
> Always use `https://` for production to ensure data security and compliance.
