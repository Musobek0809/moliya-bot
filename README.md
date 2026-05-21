# 🚀 Молиявий Эркинлик Бот — Joylash Qo'llanmasi

To'liq tayyor Telegram bot + Click to'lov tizimi. Hammasi avtomatik ishlaydi.

---

## 📋 Bot nima qiladi

1. **Mijoz** `@Moliyaviyerkinlikdasturi_bot` ga `/start` bosadi
2. Bot kursni tanitadi → **"Sotib olish — 1,000,000 so'm"** tugma
3. Bot telefon raqamni so'raydi
4. Bot **Click invoice** yaratadi → mijozga SMS yuboriladi
5. Mijoz Click ilovasida to'laydi
6. Click webhook → bot avtomatik:
   - **Kanalga bir martalik invite link** yuboradi
   - Bazaga `(user, paid_at, expiry: +90 kun)` saqlaydi
   - Sizga (admin) xabar yuboradi
7. **Har kuni 03:00 da** scheduler 3 oy o'tganlarni avtomatik chiqaradi

---

## ⚡️ TEZ JOYLASH (15 daqiqa)

### 1-qadam: GitHub'ga kod joylash

1. **GitHub** akkaunt yarating (yoki kiring): https://github.com/signup
2. Yangi **repository** yarating:
   - Name: `moliya-bot`
   - **Public** yoki **Private** — farqi yo'q
   - "Create repository" tugmasini bosing

3. Yangi sahifada paydo bo'lgan **"uploading an existing file"** linkini bosing
4. **`moliya-bot` papkasidagi BARCHA fayllarni yuklang** (`.env` faylidan tashqari!):
   - `main.py`
   - `requirements.txt`
   - `.env.example`
   - `render.yaml`
   - `Procfile`
   - `runtime.txt`
   - `.gitignore`
   - `README.md`

5. Pastdan "Commit changes" bosing

---

### 2-qadam: Render.com'ga joylash

1. **Render.com** da ro'yxatdan o'ting: https://render.com (GitHub orqali kirish mumkin)

2. Dashboard'da **"New +" → "Web Service"** bosing

3. **"Connect a repository"** bo'limida o'zingiz yaratgan **`moliya-bot`** ni ulang

4. Quyidagi sozlamalarni qo'ying:

   | Maydon | Qiymat |
   |---|---|
   | **Name** | `moliya-bot` |
   | **Region** | `Frankfurt` (eng yaqin) |
   | **Branch** | `main` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `python main.py` |
   | **Instance Type** | **Free** |

5. Pastda **"Advanced"** ni oching → **"Environment Variables"** bo'limiga quyidagilarni qo'shing (bir-bir):

   ```
   BOT_TOKEN              = 7202968542:AAE-w0WvdJgV1qjRJYsqA1e-jZNytR0QgFo
   ADMIN_ID               = 1378539669
   CLICK_SERVICE_ID       = 85618
   CLICK_MERCHANT_USER_ID = 39738
   CLICK_SECRET_KEY       = stuEmFG3tJM6CEl
   COURSE_PRICE           = 1000000
   ACCESS_DAYS            = 90
   PORT                   = 8080
   ```

6. **"Create Web Service"** bosing

7. ~5 daqiqa kuting (Render kodingizni yuklaydi va ishga tushiradi)

8. Tayyor bo'lgach, yuqorida URL ko'rinadi, masalan:
   ```
   https://moliya-bot.onrender.com
   ```
   **Bu URL ni nusxa oling** — keyingi qadamda kerak bo'ladi.

---

### 3-qadam: WEBHOOK_HOST ni qo'shish

1. Render dashboard'da **Environment** bo'limiga qaytib boring
2. **Add Environment Variable** bosing:
   - Key: `WEBHOOK_HOST`
   - Value: `https://moliya-bot.onrender.com` *(sizning Render URL'ingiz)*
3. **Save Changes** bosing — Render avtomatik qayta ishga tushiradi

---

### 4-qadam: Click panelga webhook URL'larni qo'shish

1. **mc.click.uz** ga kiring
2. Chap menyudan **"СЕРВИСЫ"** ni bosing
3. **`moliyaviyerkinlik.wmg.uz`** (ID: 85618) qatoridagi **qalam ikonkasini** bosing
4. **Service URL** maydonlariga quyidagilarni yozing:

   ```
   Prepare URL:  https://moliya-bot.onrender.com/click/prepare
   Complete URL: https://moliya-bot.onrender.com/click/complete
   ```

   *(`moliya-bot.onrender.com` o'rniga o'zingizning Render URL'ingizni qo'ying)*

5. **Saqlash** bosing

---

### 5-qadam: Bot'ni kanalga admin qilib qo'shish

1. Telegramda yopiq kanalingizga kiring (`https://t.me/+nwH8f-uWIgs0ZDdi`)
2. Kanal nomi ustiga bosing → **Administrators** → **Add Admin**
3. Qidirishda `@Moliyaviyerkinlikdasturi_bot` yozing
4. Bot'ni tanlang va quyidagi huquqlarni bering:
   - ✅ **Add Subscribers** (eng muhim!)
   - ✅ **Invite Users via Link**
   - ✅ **Ban Users** (3 oy keyin chiqarish uchun)
   - ✅ **Manage Channel**
5. **Save** bosing

⚡️ **Bot avtomatik:** sizning Telegram'ingizga "Kanal aniqlandi!" degan xabar yuboradi.

---

### 6-qadam: Sinab ko'rish

1. Telegramda **`@Moliyaviyerkinlikdasturi_bot`** ga kirib `/start` bosing
2. "Sotib olish" tugmasini bosing
3. Telefon raqamingizni yuboring
4. Click invoice yaratiladi → SMS keladi
5. Click ilovasi orqali to'lang
6. Bot avtomatik kanalga kirish havolasi yuboradi ✅

---

## 🔧 KO'P UCHRAYDIGAN MUAMMOLAR

### ❌ Bot javob bermayapti
- Render dashboard → **Logs** ni tekshiring
- "Build successful" va "Бот ишга тушди" yozuvi bo'lishi kerak
- Yo'q bo'lsa, Environment variables to'g'ri kiritilganligini tekshiring

### ❌ Click "SIGN CHECK FAILED" qaytaryapti
- `CLICK_SECRET_KEY` to'g'ri kiritilganligini tekshiring
- Click panelda Prepare/Complete URL'lar to'g'ri yozilganligini tekshiring

### ❌ Bot kanalga qo'shmayapti
- Bot kanalda **administrator** ekanligini tekshiring
- **Add Subscribers** huquqi yoqilganligini tekshiring
- `/stats` buyrug'ini admin sifatida yuboring — kanal ID aniqlanganmi?

### ❌ Render bepul tarif uxlab qoladi (15 daqiqa ishlamasa)
**Yechim:** UptimeRobot bilan har 5 daqiqada ping yuboring (bepul):
1. https://uptimerobot.com da ro'yxatdan o'ting
2. **Add New Monitor** → **HTTP(s)**
3. URL: `https://moliya-bot.onrender.com/health`
4. Interval: 5 daqiqa
5. Save

Bot endi 24/7 uyg'oq turadi.

---

## 📊 ADMIN BUYRUQLARI

Botga (faqat siz, Admin sifatida) yuborishingiz mumkin:

- `/stats` — Statistika (foydalanuvchilar, daromad)
- `/help` — Yordam

---

## 💡 KEYINGI ULANISHLAR

Bot ishlab boshlagach, qo'shimcha quyidagilarni qo'shish mumkin:

- **Bo'lib-bo'lib to'lash** — Click "splitting payments" funksiyasi
- **Reklamalar** — qoldiq vaqt eslatmalari (60-kun, 30-kun, 7-kun)
- **Promokod** — chegirma kodlari
- **Sayt** — Vercel'ga statik sayt + "Sotib olish" tugmasi bot'ga olib boradi

Bularning birortasini xohlasangiz — ayting, qo'shamiz.

---

## 🆘 TEXNIK YORDAM

Muammo bo'lsa, **Render Logs**ni ochib ko'ring — u yerda nima xato qilayotganligi yoziladi.

Buyruqlar:
```bash
# Bazani tozalash (lokal test uchun)
rm data.db

# Lokal ishga tushirish (sinab ko'rish uchun)
pip install -r requirements.txt
cp .env.example .env
# .env faylni to'ldiring
python main.py
```

---

✅ **Tayyor!** Bot ishlab turadi, har kuni avtomatik 3 oy o'tganlarni chiqarib turadi.
