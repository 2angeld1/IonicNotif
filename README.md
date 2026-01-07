# 🗺️ IonicNotif - Smart Route Planner with ML

IonicNotif is a comprehensive mobile/web application designed to optimize route planning using Machine Learning. It combines real-time data from OSRM, weather updates, and community-reported incidents to predict the most efficient travel times.

## 🚀 Key Features

- **Smart Route Prediction**: Uses a Machine Learning model (Scikit-Learn) to predict travel times based on historical data, weather, and traffic conditions.
- **Real-Time Map Interaction**: Built with Leaflet and OpenStreetMap for smooth map navigation and route visualization.
- **Incident Reporting**: Users can report and view incidents like accidents, road work, or hazards in real-time.
- **Weather Integration**: Displays current weather conditions using OpenWeatherMap API to adjust travel expectations.
- **Cross-Platform**: Developed with Ionic and React, making it ready for both Web and Mobile.

---

## 🏗️ Project Structure

This repository is divided into two main parts:

| Folder | Description | Tech Stack |
| :--- | :--- | :--- |
| [`ionic-maps-app`](./ionic-maps-app) | Frontend Application | React, Ionic, Leaflet, Tailwind CSS, Vite |
| [`ionic-maps-backend`](./ionic-maps-backend) | Backend API | FastAPI, MongoDB, Scikit-Learn, OSRM |

---

## 🛠️ Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (v3.10+)
- [MongoDB](https://www.mongodb.com/) (Local or Atlas)

### 1. Backend Setup
```bash
cd ionic-maps-backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env  # Configure your MongoDB and API keys
python run.py
```
> The backend will be running at `http://localhost:8000`.

### 2. Frontend Setup
```bash
cd ionic-maps-app
npm install
npm run dev
```
> The frontend will be running at `http://localhost:5173`.

---

## 🤖 Machine Learning Logic

The backend uses a **Random Forest Regressor** to predict `estimated_duration`. The features include:
- Base distance and duration from OSRM.
- Time of day and Day of the week.
- Current weather conditions (temperature, rain).
- Active incidents on the route.

The model improves over time as users register their completed trips!

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Developed by [2angeld1](https://github.com/2angeld1)
