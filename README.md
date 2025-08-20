# LunchScraper  

To scrape menus of restaurants and create a webpage.  

---

## 📂 Folder Structure  

- **Output**  
  - Additional files needed to run the pages (can contain CSS, images, etc.).  
  - Do **not** commit any generated HTML files.  
  - Note: all files in this folder will be exposed to the webpage Docker → files will be online.  
  - Example:  
    - `ThisImage.png` – stupid image of PE guy coding  

- **Scripts**  
  - Scripts for scraping and running the project.  
  - Contents:  
    - `crontab.txt` – crontab command used at start of Docker (note: Docker time = winter Cambridge time).  
    - `DockerFile` – build commands for Docker.  
    - `requirements.txt` – all libraries needed (used during Docker build).  
    - `run.sh` – control script.  
    - `scrape.py` – main scraping script.  
    - `template.html` – combination of HTML and Python template page.  

- `docker-compose.yml` – option for Docker setup.  
- `docker_load_and_restart.sh` – script run each morning at 2 a.m. to update repository on server before Docker build.  
  - (After dev is done this should be switched off or set to a higher value.)  
- `README.md` – this file.  

---

## 🔑 Git Workflow  

- Only **you** can push to the `main` branch.  
- Others should create **branches** and submit **merge requests**.  

---

## 👥 Notes  

- Scripts will not be used only by PE, but also by your wife 🙂 → make them as general as possible.  

---

## ⚙️ How it Works  

- Each morning at **7 a.m. (Cambridge winter time)** → `scrape.py` runs.  
- As a result, `index.html` is generated.  
- This folder is also the **source folder for web Docker**: `pe.margetaj.cz`.  

---

## ▶️ Run it Locally  

1. Clone the repository.  
2. Ensure the full Git folder is set as environment.  
3. Download requirements (`pip install -r requirements.txt`).  
4. Run `scrape.py`.  
