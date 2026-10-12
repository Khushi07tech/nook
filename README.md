# Nook 🌿
> A minimalist, aesthetic web workspace to capture fleeting thoughts, track software projects, and organize personal notes.

---

## 📌 Table of Contents
- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Testing](#testing)
- [Roadmap (Nook v2)](#roadmap-nook-v2)

---

## 📖 About the Project

The classic developer dilemma: you sit down to write code, and suddenly:
1. You get brilliant new project ideas that you know you'll forget in five minutes.
2. You forget the feature idea you came up with for your current project just a minute ago.
3. You lose track of the features you *just* finished implementing, leaving you staring into the void after work trying to remember what you even built for your commit messages.
4. You hit a deeply relatable dev existential crisis over a missing semicolon, an extra whitespace, or GitHub merge conflicts (and contemplate crying over it).
5. Above all, **categorization is hard.** We constantly struggle to separate our general life crises from new project features and the fresh bugs introduced by three lines of code!

I experienced every single one of these moments, so I asked myself: *Why not build a tailored second brain made specifically for me?* 

The core philosophy of Nook is simplicity, speed, and clean aesthetics.

---

## ✨ Key Features

- **Ideas Vault:** A space for random thoughts about life, projects, or anything on your mind. The integrated AI automatically categorizes entries and attaches relevant hashtags.
- **Project Tracker:** Easily create projects with descriptions, trackable statuses, and dedicated management views.
- **Project Details:** Dive into dedicated project pages to log entries, which are automatically categorized by the AI pipeline.
- **AI Companion:** Features a dual-mode AI assistant—a context-aware companion tailored specifically to individual projects inside the project detail view, and a general companion chat to discuss overall projects and ideas.
- **Security & Robust Error Handling:** Includes route-level checks, custom error handlers (`404` & `500`), parameterized queries to prevent SQL injection, secure URL routing with `url_for()`, and informative flash messages.

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3 (Custom Styling), JavaScript
- **Testing:** Python `unittest` framework

---

## 🚀 Getting Started

Follow these steps to set up Nook locally on your machine.

### Prerequisites

- Python 3.x installed
- Git installed

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Khushi07tech/nook.git](https://github.com/Khushi07tech/nook.git)
   cd nook

2. Create and activate a virtual environment:
    # On Windows:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate

    # On macOS/Linux:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate

3. Install dependencies:
    ```bash
    pip install -r requirements.txt

4. Environment Configuration:
Create a .env file in the root directory

5. Initialize the database
    ```bash
    python database.py

6. Run the application  
    ```bash
    python app.py

Open http://127.0.0.1:5000 in your browser.

---

## Testing
Nook includes automated unit tests for core routes, error handling, and form submissions.
To run the test suite:
    ```bash
    python -m unittest

---

## 🔮 Roadmap (Nook v2 Features):
Authentication: User registration, logins, and session security.

Vault Integration (The Big One): Connect the Ideas Vault directly to the Project Tracker so ideas related to existing projects automatically sync into the project entries instead of staying in isolation.

Enhanced Dashboard: Make the central overview more dynamic, interactive, and detailed.

UI & Navigation Polish: Add one-click field reset buttons on inputs and smooth section navigation links on vaults to quickly hop between forms and list views.

AI Refinement: Continually improve prompt structure and response consistency.

Editing: Update and modify project statuses on the fly.
