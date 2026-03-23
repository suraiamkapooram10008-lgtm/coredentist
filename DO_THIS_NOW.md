# ✅ DO THIS NOW - 5 Minute Setup

## Your Backend is LIVE but needs configuration!

---

## ☑️ STEP 1: Generate SECRET_KEY (30 seconds)

Run this command on your computer:
```bash
python generate_secret_key.py
```

**Copy the output** - you'll need it in Step 3.

---

## ☑️ STEP 2: Add PostgreSQL Database (1 minute)

1. Go to: https://railway.app/project/practical-dream
2. Click **"+ New"** button (top right)
3. Select **"Database"** → **"PostgreSQL"**
4. Wait for it to deploy (30 seconds)

---

## ☑️ STEP 3: Copy DATABASE_URL (30 seconds)

1. Click on the **PostgreSQL** service you just created
2. Go to **"Variables"** tab
3. Find `DATABASE_URL` 
4. Click the **copy icon** next to it

---

## ☑️ STEP 4: Add Variables to Backend (2 minutes)

1. Click on **"coredentist"** service (your backend)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add these ONE BY ONE:

```
DATABASE_URL = [paste the value you copied in Step 3]
SECRET_KEY = [paste the value from Step 1]
ENVIRONMENT = production
DEBUG = False
FRONTEND_URL = https://coredentist.railway.app
CORS_ORIGINS = https://coredentist.railway.app
```

4. Click **"Redeploy"** button

---

## ☑️ STEP 5: Wait for Deployment (1 minute)

Watch the deployment logs. You should see:
```
✓ Build successful
✓ Deployment successful
```

---

## ☑️ STEP 6: Run Migrations (1 minute)

### Option A: Railway Dashboard
1. In your **coredentist** service
2. Click **"Deployments"** → Latest deployment
3. Look for **"Shell"** button
4. Run: `alembic upgrade head`

### Option B: From Your Computer
```bash
cd D:\coredentist
railway link
# Select: practical-dream → production → coredentist
railway run alembic upgrade head
```

---

## ✅ DONE!

Test your backend:
```bash
curl https://coredentist-production.up.railway.app/health
```

Should return:
```json
{"status": "healthy"}
```

---

## 🎯 Next Steps

1. Deploy frontend (separate Railway service)
2. Point frontend to backend URL
3. Test the full application

---

## 🆘 Need Help?

If you see errors, check:
1. All variables are added correctly (no typos)
2. DATABASE_URL starts with `postgresql://`
3. SECRET_KEY is at least 32 characters
4. Redeploy was clicked after adding variables

**Check logs:** Railway Dashboard → coredentist → Deployments → View Logs
