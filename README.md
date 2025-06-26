# 🔊 LIVE EVENT DETECTION SYSTEM BASED ON AUDIO USING DEEP LEARNING

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/python-3.8+-blue)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)

A comprehensive **real-time audio monitoring system** that detects potential **threat sounds** (like gunshots, screams, explosions, etc.) and sends **immediate alerts** through multiple channels with **precise location information**.

---

## 📁 Directory Structure

```
LIVE_EVENT_DETECTION/
├── app/                   # Core application logic (admin, training, detection)
├── audio/         # Directory for categorized threat/non-threat audio
├── models/                # Trained models for detection
├── static/                # Static assets (CSS/JS)
├── templates/             # HTML templates for the web interface
├── contact.csv            # List of emergency contacts
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── run.py                 # Entry point to run the app
```

---

## ⚙️ Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/abilbiju/LIVE_EVENT_DETECTION.git
cd LIVE_EVENT_DETECTION
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Required Directories

Make sure the following directories exist (create if missing):

```bash
mkdir -p audio/
```

---

## 🚀 Usage

### 🔧 Running the Application

Start the main dashboard:

```bash
python main.py
```

Access the following interfaces via browser:

- **Admin Panel** – `http://localhost:5001`
- **Model Training** – `http://localhost:5002`
- **Threat Detection** – `http://localhost:5003`

---

### 🎙️ Adding Audio Samples

Place `.wav` files in the appropriate folders:


---

### 🧠 Training a Model

1. Visit `http://localhost:5002`
2. Select the desired audio categories
3. Configure model settings (epochs, batch size, etc.)
4. Start training and monitor progress

Trained models will be saved in the `models/` directory.

---

### 🚨 Running Threat Detection

1. Visit `http://localhost:5003`
2. Click **Start Detection**
3. The system will begin live audio monitoring
4. If a threat is detected:
   - Alerts will be sent to all contacts in `contact.csv`
   - Location and timestamp details included

---

### 📇 Managing Contacts

You can manage emergency contact numbers via:

- **Admin Interface**: `http://localhost:5001`
- **Or Manually**: Edit `contact.csv` (format: `Name,Phone,Email`)

---

## 🔐 Configuration

Set up key environment variables in `.env`:

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=youremail@example.com
EMAIL_PASS=yourpassword
```

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Abil Biju**

Feel free to contribute, report issues, or suggest features!

---

## 🧠 Modules Overview

- 🔑 **Admin Panel** – Manage contacts and configurations
- 🧪 **Model Training** – Build and customize audio classification models
- 📡 **Threat Detection** – Real-time audio monitoring and alert system

---

### ⭐️ Give this repo a star if you found it useful!
