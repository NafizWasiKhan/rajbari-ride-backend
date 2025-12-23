# 🎨 Frontend Deployment Guide (Netlify)

## ✅ Prerequisites
আপনার Railway backend deploy হতে হবে এবং একটা URL পেতে হবে

---

## ধাপ ১: Railway URL কপি করুন

1. Railway dashboard → Backend service
2. **Settings** → **Networking** 
3. আপনার URL copy করুন (যেমন: `rajbari-ride.up.railway.app`)

---

## ধাপ ২: Frontend এর config.js Update করুন

File: `frontend/js/config.js`

আগে যা আছে:
```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

এখন change করুন:
```javascript
const API_BASE_URL = "https://YOUR-RAILWAY-URL.up.railway.app";
```

**গুরুত্বপূর্ণ**: 
- `https://` দিতে হবে (http নয়!)
- শেষে কোনো `/` দেবেন না

---

## ধাপ ৩: নতুন GitHub Repository তৈরি করুন

### Option A: Web থেকে (সহজ)

1. GitHub.com এ যান
2. **"+"** (উপরে ডানে) → **"New repository"** ক্লিক করুন
3. Repository name: `rajbari-ride-frontend`
4. **Public** রাখুন
5. **"Create repository"** ক্লিক করুন

### Option B: Automated Script (খুব সহজ!)

আমি একটা script তৈরি করছি যা সব automatic করবে...

---

## ধাপ ৪: Netlify এ Deploy

1. **Netlify.com** এ যান এবং login করুন (GitHub দিয়ে)
2. **"Add new site"** ক্লিক করুন
3. **"Import an existing project"** সিলেক্ট করুন
4. **"Deploy with GitHub"** ক্লিক করুন
5. `rajbari-ride-frontend` repository সিলেক্ট করুন
6. Settings:
   - **Build command**: (খালি রাখুন)
   - **Publish directory**: `.` (শুধু একটা dot)
7. **"Deploy site"** ক্লিক করুন

---

## ধাপ ৫: Site URL কপি করুন

Netlify আপনাকে একটা URL দেবে:
```
https://random-name-123456.netlify.app
```

এটাই আপনার **live application**! 🎉

---

## ধাপ ৬: CORS Fix করুন

Backend এ CORS allow করতে হবে Netlify URL এর জন্য।

Railway dashboard → Backend → Variables tab → Add:
```
ALLOWED_ORIGINS=https://your-netlify-url.netlify.app
```

অথবা `settings.py` এ মাnually add করুন (আমি script দিচ্ছি)

---

## 🎯 Final Testing

1. Netlify URL খুলুন
2. Login/Register করুন
3. Ride request করুন
4. সব features test করুন!

---

**Next: আমি automated scripts তৈরি করছি যা সব কিছু সহজ করবে!**
