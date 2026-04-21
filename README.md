# ⚡ Sociax Auto-Sync Job Board Engine

Welcome to the **Sociax Auto-Sync Engine**! This tool is designed to automatically discover, filter, and sync high-quality job listings (focusing on Visa Sponsorship and Entry-Level roles) from 11 different global sources directly into your database.

---

## 🛠️ Step-by-Step Installation

Follow these steps to set up the project on your computer for the first time.

### 1. Install Python
If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/). Ensure you check the box that says **"Add Python to PATH"** during installation.

### 2. Download the Project
Download the project folder from GitHub or extract the ZIP file you received.

### 3. Open your Terminal (or Command Prompt)
- **Windows**: Search for "Command Prompt" or "PowerShell".
- **Mac**: Search for "Terminal".

### 4. Navigate to the Project Folder
Type `cd` followed by a space, then drag the folder into your terminal and press **Enter**.
```bash
cd path/to/your/project/folder
```

### 5. Install Required Tools
Run this command to install all the necessary "libraries" the project needs to work:
```bash
pip install -r requirements.txt
```

### 6. Set Up Your Configuration
1. Look for a file named `.env` in the folder.
2. Open it with any text editor (like Notepad or TextEdit).
3. You can adjust the `JOB_QUERY` (e.g., "software engineer") to change what jobs the engine looks for.
4. Save the file.

---

## 🚀 How to Use the Project

There are three main ways to interact with the engine.

### A. Launch the Dashboard (The Easiest Way)
The dashboard provides a visual interface to see all jobs, search, filter, and trigger a sync.
1. Run this command:
   ```bash
   python manage.py runserver
   ```
2. Open your web browser and go to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
3. From here, you can click **"Trigger Sync Now"** to start the engine.

### B. Run the Sync Engine Manually
If you want to run the background sync process directly without the dashboard:
```bash
python manage.py run_sync
```

### C. Export Jobs to CSV
To create a spreadsheet (Excel-compatible) file of all the current jobs:
```bash
python manage.py export_jobs
```
*Tip: You can also find an "Export CSV" button on the Dashboard.*

---

## 📂 Project Navigation (For Support)

If you ever need to describe an issue to a developer, here is what the different folders do:

- **`core/scrapers/`**: This is where the actual "bots" live that go out and find the jobs.
- **`core/templates/`**: These are the files that control how the Dashboard looks.
- **`core/utils.py`**: Contains the logic that filters for "Visa" or "Entry Level" keywords.
- **`db.sqlite3`**: This is your local database file where all your data is stored safely.

---

## ❓ Troubleshooting

- **"Command not found"**: Try using `python3` instead of `python` and `pip3` instead of `pip`.
- **"Database is locked"**: This happens if multiple processes are trying to write at once. Simply stop the running commands and start them again.
- **Missing Jobs**: Check your `.env` file to ensure your `JOB_QUERY` (e.g., "Software Engineer") is correct.

---
