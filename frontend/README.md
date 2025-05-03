# God's Eye Frontend Deployment Guide

This document outlines all necessary steps to set up and deploy the **God's Eye Frontend**, built with Vue.js.

## ⚙️ Prerequisites

Ensure you have the following installed:

* Node.js (v14.x or higher)
* npm (comes with Node.js)
* Git (optional)

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/AddagallaSaiTharun/GodysEye.git
cd frontend
```

## 2️⃣ Install Project Dependencies

```bash
npm install
```

## 3️⃣ Configure Environment Variables (Optional)

If your Vue.js project interacts with environment variables (e.g., backend API URLs), create a `.env` file:

```bash
touch .env
```

Add your configuration:

```bash
VUE_APP_API_URL=http://127.0.0.1:8000
```

## 4️⃣ Run Frontend in Development Mode (with hot reload)

```bash
npm run serve
```

Access your frontend locally at [http://localhost:8080](http://localhost:8080)

## 5️⃣ Build Frontend for Production

```bash
npm run build
```

This generates optimized static files in the `dist/` directory.

## 6️⃣ Deploy Changes (Connect to Backend)

```bash
npm run deploy
```

This command will build and deploy the latest frontend code to production or connect updates to the backend service.

## 7️⃣ Lint and Fix Code

```bash
npm run lint
```

## 🛠️ Useful Commands Summary

| Task                 | Command          |
| -------------------- | ---------------- |
| Install dependencies | `npm install`    |
| Run dev server       | `npm run serve`  |
| Build for production | `npm run build`  |
| Deploy frontend      | `npm run deploy` |
| Lint and fix         | `npm run lint`   |

## 📝 Customize Vue Configuration

You can customize project settings in `vue.config.js` or refer to:
[Vue CLI Configuration Reference](https://cli.vuejs.org/config/)

---

Your frontend should now be up and running, ready to interface with the backend API!
