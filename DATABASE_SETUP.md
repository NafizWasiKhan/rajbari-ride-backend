# 🗄️ Database Setup Guide for Railway

## বর্তমান অবস্থা:
✅ Settings updated - এখন SQLite এবং PostgreSQL দুটোই support করে
✅ Requirements updated - PostgreSQL packages added

## 📋 আপনার জন্য দুটি Option:

---

### Option 1: SQLite দিয়ে Test করুন (দ্রুত, কিন্তু temporary)

**সুবিধা:**
- দ্রুত deploy হবে
- কোনো extra setup লাগবে না

**অসুবিধা:**
- প্রতিবার redeploy এ data মুছে যাবে
- Users, rides সব হারিয়ে যাবে

**কখন ভালো:**
- শুধু test করার জন্য
- Demo দেখানোর জন্য

---

### Option 2: PostgreSQL ব্যবহার করুন (Recommended, Production-ready)

**সুবিধা:**
- ✅ Data permanent থাকবে
- ✅ Fast এবং reliable
- ✅ Railway তে FREE

**কিভাবে করবেন:**

#### ধাপ ১: PostgreSQL Database Add করুন
1. Railway Dashboard এ যান
2. আপনার project ক্লিক করুন
3. উপরে **"+ New"** button ক্লিক করুন
4. **"Database"** সিলেক্ট করুন
5. **"Add PostgreSQL"** ক্লিক করুন

#### ধাপ ২: অপেক্ষা করুন
- Railway automatic setup করবে (1-2 মিনিট)
- `DATABASE_URL` environment variable automatic add হবে

#### ধাপ ৩: Backend Re-deploy করুন
- আপনার backend service ক্লিক করুন
- "Deploy" tab এ যান
- "Redeploy" ক্লিক করুন (অথবা GitHub এ নতুন push করুন)

#### ধাপ ৪: Migration চালান
Railway আপনার জন্য automatic `python manage.py migrate` চালাবে

#### ধাপ ৫: Superuser তৈরি করুন
Railway CLI দিয়ে (অথবা Railway Shell থেকে):
```bash
railway run python backend/manage.py createsuperuser
```

---

## 🎯 আমার Recommendation:

**প্রথমে SQLite দিয়ে test করুন:**
1. এখনই files GitHub এ upload করুন
2. Railway তে deploy দেখুন
3. যদি সফল হয়, তাহলে frontend test করুন

**পরে PostgreSQL add করুন:**
1. যখন সব ঠিকমতো কাজ করবে
2. তখন PostgreSQL database add করবেন
3. একবার migrate করলেই হবে

---

## 📝 এখন কি করবেন:

1. ✅ Settings.py updated (আমি করে দিয়েছি)
2. ✅ Requirements.txt updated (আমি করে দিয়েছি)
3. ⏳ GitHub এ files upload করুন
4. ⏳ Railway এ deploy দেখুন
5. ⏳ পরে PostgreSQL add করুন (optional কিন্তু recommended)

---

**Next Step**: 
GitHub এ সব files (including backend/, railway.toml, requirements.txt) upload করুন!
