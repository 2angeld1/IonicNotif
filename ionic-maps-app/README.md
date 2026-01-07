# 📱 Ionic Maps App

Frontend application for the **IonicNotif** project. A mobile-first web app built with Ionic and React for smart route planning.

## 🛠️ Tech Stack

- **Framework**: [Ionic React](https://ionicframework.com/docs/react)
- **Tooling**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Maps**: [Leaflet](https://leafletjs.com/) with [React Leaflet](https://react-leaflet.js.org/)
- **State/API**: Axios & React Hooks

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Environment Variables**:
   Create a `.env` file in the root of this folder:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. **Run in development mode**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## 📸 Features Implemented

- **Interactive Map**: Search destinations and visualize routes.
- **Route Panel**: Detailed breakdown of distance and ML-predicted time.
- **Incidents Overlay**: Add and view markers for traffic incidents.
- **Weather Display**: Integrated weather widget for the current location.
- **Responsive UI**: Optimized for mobile devices via Ionic components.

## 📁 Structure

- `src/components`: Reusable UI components (Map, RoutePanel, etc.)
- `src/pages`: Main application views.
- `src/services`: API client and utility logic.
- `src/types`: TypeScript interfaces.
