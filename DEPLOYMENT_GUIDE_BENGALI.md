# 🚀 Zatra - ফ্রি তে Deploy করার সম্পূর্ণ গাইড

এই গাইডে আপনি শিখবেন কিভাবে **সম্পূর্ণ ফ্রি তে** আপনার Zatra প্রজেক্ট deploy করবেন:
- **Backend** → Railway.com (Free)
- **Frontend** → Netlify.com (Free)

---

## 📋 প্রয়োজনীয় জিনিস

1. ✅ GitHub Account
2. ✅ Railway.com Account (GitHub দিয়ে সাইন আপ করবেন)
3. ✅ Netlify.com Account (GitHub দিয়ে সাইন আপ করবেন)

---

# PART 1: Backend Deploy (Railway.com)

## ধাপ ১: GitHub Repository তৈরি করুন

### ১.১ নতুন Repository তৈরি
```bash
# Terminal এ গিয়ে project folder এ যান
cd "C:\Users\nafiz\Desktop\Project Ultra\Rajbari Ride"

# Git initialize (যদি আগে না করে থাকেন)
git init

# সব file add করুন
git add .

# Commit করুন
git commit -m "Initial commit - Backend ready for Railway"
```

### ১.২ GitHub এ Push করুন
1. GitHub.com এ যান
2. "New Repository" ক্লিক করুন
3. নাম দিন: `rajbari-ride-backend`
4. **Public** রাখুন
5. **Create repository** ক্লিক করুন

### ১.৩ আপনার Local Project Push করুন
```bash
# GitHub থেকে পাওয়া commands copy করে paste করুন
git remote add origin https://github.com/YOUR_USERNAME/rajbari-ride-backend.git
git branch -M main
git push -u origin main
```

---

## ধাপ ২: Railway.com এ Backend Deploy

### ২.১ Railway Account তৈরি
1. [Railway.app](https://railway.app) এ যান
2. "Login with GitHub" ক্লিক করুন
3. GitHub দিয়ে সাইন ইন করুন

### ২.২ নতুন Project তৈরি
1. Dashboard এ "New Project" ক্লিক করুন
2. "Deploy from GitHub repo" সিলেক্ট করুন
3. আপনার `rajbari-ride-backend` repository সিলেক্ট করুন
4. "Deploy Now" ক্লিক করুন

### ২.৩ Environment Variables সেট করুন

Railway dashboard এ:
1. আপনার deployed project ক্লিক করুন
2. "Variables" ট্যাব এ যান
3. নিচের variables add করুন:

```
DJANGO_SETTINGS_MODULE = rajbari_ride.settings
PYTHONUNBUFFERED = 1
```

### ২.৪ Start Command সেট করুন

1. "Settings" ট্যাব এ যান
2. "Deploy" section খুঁজুন
3. "Custom Start Command" এ ক্লিক করুন
4. এই command টাইপ করুন:
```bash
cd backend && python manage.py migrate && gunicorn rajbari_ride.wsgi
```
5. "Save" করুন

### ২.৫ Domain/URL কপি করুন

1. "Settings" → "Public Networking" এ যান
2. "Generate Domain" ক্লিক করুন
3. Railway আপনাকে একটি URL দেবে (যেমন: `rajbari-ride.up.railway.app`)
4. এই URL টা কপি করে রাখুন ✅

---

## ধাপ ৩: Database Migration

Railway dashboard থেকে:
1. "Deploy Logs" দেখুন
2. নিশ্চিত করুন migration সফল হয়েছে
3. যদি error দেখান, "Deployments" tab থেকে আবার deploy করুন

---

# PART 2: Frontend Deploy (Netlify.com)

## ধাপ ৪: Frontend এর জন্য নতুন Repository

### ৪.১ Frontend Folder আলাদা করুন
```bash
# একটা নতুন folder তৈরি করুন Desktop এ
cd C:\Users\nafiz\Desktop
mkdir rajbari-ride-frontend

# Frontend files copy করুন
xcopy "C:\Users\nafiz\Desktop\Project Ultra\Rajbari Ride\frontend\*" "C:\Users\nafiz\Desktop\rajbari-ride-frontend\" /E /I
```

### ৪.২ API URL আপডেট করুন

`rajbari-ride-frontend/js/config.js` file টি খুলুন এবং edit করুন:

```javascript
// আগে ছিল:
const API_BASE_URL = "http://127.0.0.1:8000";

// এখন করুন (Railway URL বসান):
const API_BASE_URL = "https://rajbari-ride.up.railway.app";
```

**গুরুত্বপূর্ণ**: আপনার Railway URL টা সঠিক ভাবে copy করুন!

### ৪.৩ GitHub এ Frontend Push করুন

```bash
cd C:\Users\nafiz\Desktop\rajbari-ride-frontend

git init
git add .
git commit -m "Frontend ready for Netlify"

# GitHub এ নতুন repo তৈরি করুন (নাম: rajbari-ride-frontend)
git remote add origin https://github.com/YOUR_USERNAME/rajbari-ride-frontend.git
git branch -M main
git push -u origin main
```

---

## ধাপ ৫: Netlify এ Frontend Deploy

### ৫.১ Netlify Account তৈরি
1. [Netlify.com](https://netlify.com) এ যান
2. "Sign up with GitHub" ক্লিক করুন
3. GitHub দিয়ে সাইন ইন করুন

### ৫.২ নতুন Site Deploy
1. Dashboard এ "Add new site" ক্লিক করুন
2. "Import an existing project" সিলেক্ট করুন
3. "GitHub" সিলেক্ট করুন
4. `rajbari-ride-frontend` repository সিলেক্ট করুন

### ৫.৩ Build Settings
- **Build command**: (খালি রাখুন)
- **Publish directory**: `.` (শুধু একটা dot)
- "Deploy site" ক্লিক করুন

### ৫.৪ Site URL কপি করুন

Netlify আপনাকে একটা random URL দেবে (যেমন: `amazing-curie-123456.netlify.app`)

এই URL ই আপনার live application! 🎉

---

# PART 3: CORS এবং Final Setup

## ধাপ ৬: Backend এ CORS Configure করুন

### ৬.১ settings.py Update করুন

আপনার local project এ যান:
`backend/rajbari_ride/settings.py` খুলুন:

```python
# এই line টা খুঁজুন:
CORS_ALLOW_ALL_ORIGINS = True

# এর নিচে add করুন:
CORS_ALLOWED_ORIGINS = [
    "https://YOUR-NETLIFY-URL.netlify.app",
]

# এবং add করুন:
CSRF_TRUSTED_ORIGINS = [
    "https://YOUR-NETLIFY-URL.netlify.app",
]
```

### ৬.২ GitHub এ Push করুন

```bash
cd "C:\Users\nafiz\Desktop\Project Ultra\Rajbari Ride"
git add .
git commit -m "Update CORS settings for Netlify"
git push
```

Railway automatically আবার deploy করবে!

---

## ধাপ ৭: Database Admin Setup

### ৭.১ Superuser তৈরি করুন

Railway dashboard থেকে:
1. "Settings" tab এ যান
2. "Connect" সেকশন খুঁজুন
3. Railway Shell/Terminal পাবেন (বা local থেকে Railway CLI দিয়ে করতে পারেন)

অথবা আপনার local terminal থেকে Railway CLI ব্যবহার করুন:
```bash
# Railway CLI install (যদি না থাকে)
npm i -g @railway/cli

# Login
railway login

# Link your project
railway link

# Run commands
railway run python backend/manage.py createsuperuser
```

Username, Email, Password দিয়ে superuser তৈরি করুন।

---

# 🎊 সম্পূর্ণ!

## ✅ আপনার Live URLs:

1. **Frontend**: `https://YOUR-SITE.netlify.app`
2. **Backend API**: `https://YOUR-PROJECT.up.railway.app`
3. **Admin Panel**: `https://YOUR-PROJECT.up.railway.app/admin`

---

## 🔧 Troubleshooting (যদি কোনো সমস্যা হয়)

### Problem 1: "CORS Error" দেখাচ্ছে
**Solution**: 
- `settings.py` এ `CSRF_TRUSTED_ORIGINS` ঠিকমতো add করেছেন কিনা check করুন
- Git push করে Railway তে আবার deploy করুন

### Problem 2: "500 Internal Server Error"
**Solution**:
- Railway logs চেক করুন (Deploy Logs tab)
- `python manage.py migrate` run হয়েছে কিনা দেখুন

### Problem 3: Static files load হচ্ছে না Frontend এ
**Solution**:
- Netlify এ গিয়ে "Deploys" → "Trigger deploy" → "Clear cache and deploy" করুন

### Problem 4: Database save হচ্ছে না
**Solution**:
- Railway free tier এ SQLite সাপোর্ট করে না persistent ভাবে
- PostgreSQL database add করতে হবে (Railway এ "New" → "Database" → "PostgreSQL")

---

## 💰 Free Tier Limits

### Railway.com (Free)
- ✅ 500 ঘন্টা/মাস (execution time)
- ✅ $5 credit/মাস
- ⚠️ Credit শেষ হলে sleep mode এ যাবে

### Netlify.com (Free)
- ✅ 100 GB bandwidth/মাস
- ✅ Unlimited sites
- ✅ Auto SSL (HTTPS)

---

## 📝 পরবর্তী Update করার নিয়ম

### Backend Update:
```bash
cd "C:\Users\nafiz\Desktop\Project Ultra\Rajbari Ride"
git add .
git commit -m "Your update message"
git push
```
Railway automatic deploy করবে!

### Frontend Update:
```bash
cd C:\Users\nafiz\Desktop\rajbari-ride-frontend
git add .
git commit -m "Your update message"
git push
```
Netlify automatic deploy করবে!

---

## 🎯 Custom Domain যুক্ত করা (Optional)

### Netlify এ:
1. "Domain settings" এ যান
2. "Add custom domain" ক্লিক করুন
3. আপনার domain (যেমন: rajbariride.com) add করুন
4. DNS settings update করুন (your domain provider এ)

### Railway এ:
1. Settings → Public Networking
2. "Custom Domain" add করুন
3. CNAME record add করুন আপনার domain এ

---

**তৈরি করেছেন**: Antigravity AI Assistant
**তারিখ**: December 23, 2025

সফল Deployment এর জন্য শুভকামনা! 🚀
