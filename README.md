````md
# Crashout Cloud

![Crashout Cloud](https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,100:1e293b&height=250&section=header&text=Crashout%20Cloud&fontSize=45&fontColor=ffffff)

A scalable backend system built with Flask and MongoDB that powers journaling, server-based messaging, and user management.

Crashout Cloud is designed as a modular backend foundation for social platforms, private communities, and productivity applications.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

---

## Overview

Crashout Cloud combines multiple backend systems into one unified platform:

- Journaling system with entry management
- Discord-style server and channel messaging
- User authentication and ownership control
- Image upload and file handling
- Persistent settings storage

---

## Features

### User System
- Register and login with username
- Username availability validation
- User-based ownership system

### Journals
- Create journals with descriptions
- Add text and image entries
- Owner-only permissions
- Delete entries securely
- Limit of 3 journals per user

### Server System
- Create servers with unique names
- One server per user limit
- Channel-based messaging (default: general)
- Persistent message storage in MongoDB
- Member tracking system

### Settings System
- Persistent user preferences
- Theme, username, and server configuration

### File Uploads
- Image upload support
- UUID-based file naming
- Static file serving endpoint

---

## API Routes

### Authentication
- POST /api/register
- POST /api/login
- GET /api/check-username/<username>

### Servers
- GET /api/servers
- POST /api/servers
- DELETE /api/servers/<server_name>

### Messaging
- GET /api/servers/<server>/channels/<channel>/messages
- POST /api/servers/<server>/channels/<channel>/messages

### Journals
- GET /api/journals
- POST /api/journals
- DELETE /api/journals/<journal_name>
- POST /api/journals/<journal_name>/entries
- DELETE /api/journals/<journal_name>/entries/<entry_id>

### Settings
- GET /api/settings
- POST /api/settings

### Uploads
- POST /api/upload
- GET /uploads/<filename>

---

## Security Rules

- Users can only modify their own data
- Journals are protected by ownership validation
- Entries can only be deleted by authors
- Servers can only be deleted by owners
- One server per user restriction enforced
- Input validation on all endpoints

---

## Architecture

Crashout Cloud uses a modular MongoDB structure:

- users → authentication + ownership tracking
- journals → entries and content storage
- servers → messaging system and channels
- settings → global user preferences

---

## Installation

```bash
git clone https://github.com/whosdior/Crashout-Cloud.git
cd Crashout-Cloud
pip install -r requirements.txt
python app.py
````

---

## Running the Server

Server runs on:

[http://localhost:5000](http://localhost:5000)

---

## Developer

Developed by **whosdior**

---

## License

This project is licensed under the MIT License.

````

---

# 🚀 How to apply it (important)

Inside your repo:

```bash
git add README.md
git commit -m "Improve README with SaaS-style documentation"
git push origin main
````

---
