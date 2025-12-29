# Deploying Company Analyzer

This guide walks you through deploying Company Analyzer to get a stable public URL.

**Architecture:**
- **Frontend** (Next.js) → Vercel (free tier)
- **Backend** (FastAPI/Python) → Railway (free tier with $5/month credit)

## Prerequisites

- GitHub account (to connect repos)
- [Vercel account](https://vercel.com/signup) (free)
- [Railway account](https://railway.app/) (free tier available)
- Your Anthropic API key

---

## Step 1: Push Code to GitHub

If not already done, create a GitHub repository and push your code:

```bash
cd company-audit
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/company-analyzer.git
git push -u origin main
```

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Go to [railway.app](https://railway.app/) and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `company-analyzer` repository
5. Railway will detect the Python project

### 2.2 Configure Root Directory

Since the backend is in a subdirectory:
1. Go to your service **Settings**
2. Under **Source**, set **Root Directory** to: `backend`

### 2.3 Set Environment Variables

Go to **Variables** tab and add:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `CORS_ORIGINS` | `https://your-app.vercel.app` (update after Vercel deploy) |

### 2.4 Get Your Backend URL

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"** to get a public URL
3. Your backend URL will look like: `https://company-analyzer-production.up.railway.app`

**Save this URL** - you'll need it for the frontend.

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Project

1. Go to [vercel.com](https://vercel.com/) and sign in with GitHub
2. Click **"Add New Project"**
3. Import your `company-analyzer` repository
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`

### 3.2 Set Environment Variables

Before deploying, add this environment variable:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your Railway backend URL (e.g., `https://company-analyzer-production.up.railway.app`) |

### 3.3 Deploy

Click **"Deploy"** and wait for the build to complete.

Your frontend URL will look like: `https://company-analyzer.vercel.app`

---

## Step 4: Update Backend CORS

Now that you have your Vercel URL, update the Railway backend:

1. Go to Railway → Your project → **Variables**
2. Update `CORS_ORIGINS` to include your Vercel URL:
   ```
   https://company-analyzer.vercel.app,http://localhost:3000
   ```
3. Railway will automatically redeploy

---

## Step 5: Verify Deployment

1. Visit your Vercel URL
2. Search for a company ticker (e.g., "AAPL")
3. Verify the analysis loads correctly

---

## Troubleshooting

### "Failed to fetch" errors
- Check that `NEXT_PUBLIC_API_URL` in Vercel matches your Railway URL exactly
- Verify `CORS_ORIGINS` in Railway includes your Vercel domain

### Backend not starting
- Check Railway logs for errors
- Verify `ANTHROPIC_API_KEY` is set correctly

### Slow initial load
- Railway free tier may sleep after inactivity
- First request after sleep takes 10-20 seconds to wake up

---

## Custom Domain (Optional)

### Vercel (Frontend)
1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS as instructed

### Railway (Backend)
1. Go to Service Settings → Networking
2. Add custom domain
3. Update DNS as instructed
4. **Remember** to update `CORS_ORIGINS` with your new domain

---

## Costs

**Vercel Free Tier:**
- Unlimited deployments for personal projects
- 100GB bandwidth/month

**Railway Free Tier:**
- $5 free credit/month
- Usually sufficient for moderate usage
- ~500 hours of runtime

For higher usage, both platforms offer affordable paid plans.
