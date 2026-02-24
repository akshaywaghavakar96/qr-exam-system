# 📋 QR Exam System - Setup Guide

## Project Structure
```
qr_exam_system/
├── app.py               ← Main Flask app
├── onedrive_helper.py   ← OneDrive Excel read/write
├── requirements.txt     ← Python packages
├── Procfile             ← For Render/Railway deploy
└── templates/
    ├── base.html
    ├── index.html
    ├── register.html
    ├── login.html
    ├── exam.html
    ├── result.html
    └── certificate.html
```

---

## STEP 1: Setup Azure App (for OneDrive access)

1. Go to https://portal.azure.com
2. Search **"App registrations"** → Click **"New registration"**
3. Name it anything (e.g. `ExamApp`) → Click **Register**
4. Copy the **Application (client) ID** → save it
5. Copy the **Directory (tenant) ID** → save it
6. Go to **Certificates & secrets** → **New client secret** → Copy the **Value**
7. Go to **API permissions** → Add → Microsoft Graph → **Files.ReadWrite.All** → Grant admin consent

---

## STEP 2: Get OneDrive Credentials

You now have:
- `ONEDRIVE_CLIENT_ID` = Application ID from step 4
- `ONEDRIVE_TENANT_ID` = Directory ID from step 5
- `ONEDRIVE_CLIENT_SECRET` = Secret value from step 6
- `ONEDRIVE_FILE_PATH` = `/exam_data.xlsx` (file will be auto-created in OneDrive root)

---

## STEP 3: Deploy to Render (Free)

1. Push your project to GitHub
2. Go to https://render.com → Sign up free
3. Click **"New Web Service"** → Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add **Environment Variables:**
   ```
   SECRET_KEY          = any-random-string-123
   ONEDRIVE_CLIENT_ID  = your-client-id
   ONEDRIVE_CLIENT_SECRET = your-secret
   ONEDRIVE_TENANT_ID  = your-tenant-id
   ONEDRIVE_FILE_PATH  = /exam_data.xlsx
   APP_URL             = https://your-app.onrender.com
   ```
6. Click **Deploy** → Wait 2-3 minutes
7. Copy your app URL (e.g. `https://exam-app.onrender.com`)
8. Update `APP_URL` environment variable with this URL

---

## STEP 4: Get Your QR Code

1. Visit `https://your-app.onrender.com`
2. The QR code is shown on the homepage
3. Click **"Download QR Code"** → Print it!

---

## STEP 5: Edit Exam Questions

Open `app.py` and find the `QUESTIONS` list:

```python
QUESTIONS = [
    {
        "question": "Your question here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A"   # ← Must match one of the options exactly
    },
    # Add more questions...
]
```

Also change the pass percentage:
```python
PASS_SCORE = 60  # Change to 70 for 70% pass mark
```

---

## How Users Use It

1. **User scans QR Code** → Opens your website
2. **Clicks "Register"** → Enters username → Gets password on screen
3. **Clicks "Login"** → Enters username + password → Takes MCQ exam
4. **Passes exam** → Downloads PDF certificate automatically!

---

## Excel Data (OneDrive)

Your `exam_data.xlsx` will have 2 sheets:

**Users sheet:**
| username | password | registered_date |
|----------|----------|-----------------|
| john     | aB3xK9mQ | 2024-01-15 10:30 |

**ExamResults sheet:**
| username | score | passed | cert_id | date |
|----------|-------|--------|---------|------|
| john     | 80    | True   | XK9AB2MQ1P | 2024-01-15 |

---

## Run Locally (for testing)

```bash
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY=test-secret
export ONEDRIVE_CLIENT_ID=your-id
export ONEDRIVE_CLIENT_SECRET=your-secret
export ONEDRIVE_TENANT_ID=your-tenant
export ONEDRIVE_FILE_PATH=/exam_data.xlsx
export APP_URL=http://localhost:5000

python app.py
# Open http://localhost:5000
```
