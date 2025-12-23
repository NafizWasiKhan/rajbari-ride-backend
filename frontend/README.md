# Zatra - Frontend

Standalone frontend for the Zatra application. Designed for deployment on Netlify or any static hosting platform.

## 📁 Structure

```
frontend/
├── index.html          # Main application (standalone)
├── css/
│   └── style.css      # Application styles
└── js/
    ├── config.js      # API configuration
    ├── main.js        # Main application logic
    ├── auth.js        # Authentication logic
    └── rajbari_data.js # Location data
```

## ⚙️ Configuration

### Local Development

1. Ensure your Django backend is running on `http://127.0.0.1:8000`
2. Open `frontend/index.html` in your browser (or use a simple HTTP server)

### Production Deployment

1. **Update API URL**: Edit `js/config.js`
   ```javascript
   const API_BASE_URL = "https://your-project.up.railway.app";
   ```

2. **Deploy to Netlify**:
   - Push the `frontend/` folder to GitHub
   - Connect to Netlify
   - Set Build Command: (leave empty)
   - Set Publish Directory: `.` (root of frontend)
   - Deploy!

## 🚀 Quick Start

```bash
# Using Python's built-in server
cd frontend
python -m http.server 8080

# Open browser
# Visit: http://localhost:8080
```

## 📝 Notes

- All authentication uses Token-based auth (stored in localStorage)
- The frontend is fully decoupled from Django templates
- WebSocket connections use the same `API_BASE_URL`
