# 🎨 Botni chiroyli qilish (@BotFather sozlamalari)

Mavjud bot kabi professional ko'rinish berish uchun quyidagi sozlamalarni qiling.

---

## 1. Bot suratini qo'yish

Asadbek Ashurovning surati botda paydo bo'lishi uchun:

1. **@BotFather** ga kiring
2. `/mybots` → `@Moliyaviyerkinlikdasturi_bot` ni tanlang
3. **Edit Bot** → **Edit Botpic**
4. Asadbekning suratini yuboring (kvadrat shakli yaxshi — 640x640px)

---

## 2. Bot tavsifini qo'yish (Description)

Bu matn bot ochilganda foydalanuvchi birinchi bo'lib ko'radi:

1. **@BotFather** → `/mybots` → Bot tanlash
2. **Edit Bot** → **Edit Description**
3. Quyidagi matnni nusxa olib qo'ying:

```
Bu bot nimalar qila oladi?
Moliyaviy Erkinlik Dasturi 🎉
Muallif: Asadbek Ashurov

✅ 8 ta amaliy dastur (38 soat 16 daqiqa)
✅ Yopiq Telegram kanalga 3 oy kirish
✅ Barcha PDF materiallar
✅ Click orqali xavfsiz to'lov

70% chegirma — bugungi narx 1 000 000 so'm
```

---

## 3. About Text (Qisqa tavsif)

Bot ustiga bosilganda profilda ko'rinadi:

1. **@BotFather** → **Edit Bot** → **Edit About**
2. Quyidagi matnni qo'ying (120 belgidan oshmasligi kerak):

```
Asadbek Ashurov — Moliyaviy Erkinlik Dasturi. 8 ta amaliy dars + 3 oylik kanal kirish.
```

---

## 4. Menyu buyruqlarini tozalash

Mijoz hech narsa yozmasligi uchun barcha buyruqlarni o'chiramiz (faqat admin uchun `/stats` qoladi — u kod ichida avtomatik o'rnatiladi):

1. **@BotFather** → **Edit Bot** → **Edit Commands**
2. Eski buyruqlar bo'lsa, hammasini o'chiring va bo'sh saqlang
3. Yoki shu matnni yuboring (faqat bitta admin buyrug'i):

```
stats - 📊 Statistika (admin)
```

⚡️ **Bot avtomatik:** kod ishga tushganda buyruqlarni to'g'rilab qo'yadi.

---

## 5. Menu Button (chap pastdagi 4 chiziqli tugma)

Mavjud botda "Menyu" tugmasi bor edi. Bizning bot uchun bu kerak emas, chunki **doimiy tugmalar** bor.

1. **@BotFather** → **Edit Bot** → **Configure Menu Button**
2. **Default menu button** ni tanlang (yoki o'chirib qo'ying)

---

## 6. Bot Privacy (Maxfiylik)

1. **@BotFather** → **Bot Settings** → **Group Privacy**
2. **Enable** holatida qoldiring (xavfsizlik uchun)

---

## ✅ Tekshirish

Hammasini sozlab bo'lganingizdan keyin:

1. Botingizni ochib `/start` bosing
2. Quyidagilar ko'rinishi kerak:
   - 📷 Asadbekning surati profilda
   - 📝 Tavsif matni ochilganda
   - 4 ta katta tugma: **💳 Sotib olish**, **📊 Mening holatim**, **ℹ️ Kurs haqida**, **📞 Menejer bilan bog'lanish**
   - Hech qanday `/buyruq` yo'q (faqat admin sifatida `/stats` ko'rinadi)

---

## Mijoz tajribasi (qanday ishlaydi)

```
1. Mijoz botni ochadi
   ↓
2. Asadbekning surati + WELCOME matn ko'rinadi
   ↓
3. 4 ta tugma:
   [💳 Sotib olish]
   [📊 Mening holatim]  [ℹ️ Kurs haqida]
   [📞 Menejer bilan bog'lanish]
   ↓
4. "Sotib olish" → telefon so'raydi
   ↓
5. Telefon yuborgach → Click SMS keladi
   ↓
6. To'lov → bot avtomatik kanalga qo'shadi
   ↓
7. 3 oydan keyin avtomatik chiqaradi
```

**Mijoz hech narsa yozmaydi.** Hammasi tugmalar bilan ishlaydi. ✨
