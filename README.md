# Daily Gold | Momentum FX

An automated, mobile-first, static website generator for **Gold (XAU/USD) Daily Session Reports**. 
Refined by the Momentum FX Team.

![Daily Gold PWA](public/static/images/logo.png)

## ✨ Features

- **Agentic Content Generation**: Uses AI (Gemini) to fetch real-time market data and generating professional trading session briefings.
- **Progressive Web App (PWA)**: 
  - Installable on Mobile (iOS/Android) and Desktop (Chrome/Edge).
  - Offline Check-in capabilities.
- **Mobile-First Design**: 
  - Optimized specifically for phone screens.
  - Horizontally scrollable data tables.
  - Sticky "Fear Factor" meter for constant sentiment context.
- **Premium Dark UI**: A sleek, high-contrast aesthetics focused on readability and professional presentation.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### 1. Generate a Report
Use the generation script to create a new markdown report with real-time price data.
```bash
python scripts/generate_report.py --session "London Session"
```
*Note: Requires `GEMINI_API_KEY` in `.env` file.*

### 2. Build the Website
Compile the markdown reports into a static HTML website (output to `public/`).
```bash
python scripts/build_site.py
```

### 3. Preview Locally & Test PWA
Serve the site locally to verify the "Install App" button and service workers.
```bash
python -m http.server 8000 --directory public
```
Visit: **http://localhost:8000**

## 🌐 Deployment (GitHub Pages)

This project is ready for GitHub Pages. 

### Method A: Manual (gh-pages)
1. Build the site: `python scripts/build_site.py`
2. Push the `public` folder to a `gh-pages` branch on your repository.
   ```bash
   git subtree push --prefix public origin gh-pages
   ```
3. Go to GitHub Repo > Settings > Pages.
4. Ensure "Source" is set to the `gh-pages` branch.

### Method B: Docs Folder (Simpler)
1. Rename `public` folder to `docs`.
2. Push to `main`.
3. In GitHub Settings > Pages, select source as `main` branch and `/docs` folder.

## 🛠 Project Structure

- `content/reports/`: Markdown source files for daily reports.
- `templates/`: Jinja2 HTML templates (`base`, `index`, `post`).
- `static/`: Raw CSS, JS, and Images.
- `scripts/`: Python automation scripts.
- `public/`: **Distribution build** (Do not edit directly).

---

&copy; 2025 Momentum FX Team.
