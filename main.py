"""
Молиявий Эркинлик Бот — V2
==========================
Yangi funksiyalar:
- Mijoz ism + telefon yig'ish
- Click ilovaga to'g'ridan-to'g'ri o'tkazish
- Payme ilovaga to'g'ridan-to'g'ri o'tkazish
- Webhook ikkalasida ham
"""

import asyncio
import base64
import logging
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import aiohttp
import aiosqlite
import uvicorn
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    ChatMemberUpdated,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ
# ─────────────────────────────────────────────────────────
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_ID_ENV = os.getenv("CHANNEL_ID", "")
CHANNEL_ID = int(CHANNEL_ID_ENV) if CHANNEL_ID_ENV else None

# Click
CLICK_SERVICE_ID = int(os.getenv("CLICK_SERVICE_ID", "0"))
CLICK_MERCHANT_USER_ID = int(os.getenv("CLICK_MERCHANT_USER_ID", "0"))
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")  # ixtiyoriy (deep link uchun)

# Payme
PAYME_MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID", "")
PAYME_SECRET_KEY = os.getenv("PAYME_SECRET_KEY", "")
PAYME_TEST_KEY = os.getenv("PAYME_TEST_KEY", "")
PAYME_CHECKOUT_URL = "https://checkout.paycom.uz"

COURSE_PRICE = int(os.getenv("COURSE_PRICE", "1000000"))  # сум
ACCESS_DAYS = int(os.getenv("ACCESS_DAYS", "90"))

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
PORT = int(os.getenv("PORT", "8080"))
DB_PATH = os.getenv("DB_PATH", "data.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("moliya")

# ─────────────────────────────────────────────────────────
# ТУГМАЛАР
# ─────────────────────────────────────────────────────────
BTN_BUY = "💳 Сотиб олиш"
BTN_STATUS = "📊 Менинг ҳолатим"
BTN_INFO = "ℹ️ Курс ҳақида"
BTN_CONTACT = "📞 Менежер билан боғланиш"
BTN_CANCEL = "❌ Бекор қилиш"
BTN_PHONE = "📱 Телефон рақамни юбориш"
BTN_CONFIRM = "✅ Тасдиқлайман"
BTN_EDIT = "✏️ Ўзгартириш"

# ─────────────────────────────────────────────────────────
# МАТНЛАР
# ─────────────────────────────────────────────────────────
WELCOME = """🌟 <b>Молиявий Эркинлик Дарслари</b>
<i>Муаллиф: Асадбек Ашуров</i>

Ассалому алайкум! Сизни кутиб турганимиздан хурсандмиз 🤝

📚 <b>8 та ҳаётий дастур</b>
⏱ Жами: <b>38 соат 16 дақиқа</b> амалий билим

<b>Курсга обуна бўлганда:</b>
✅ Ёпиқ Телеграм каналга кириш
✅ <b>3 ой</b> давомида чекловсиз томоша
✅ Барча қўшимча PDF материаллар

💰 Нархи: <b>1 000 000 сўм</b>

👇 Пастдаги тугмалардан фойдаланинг"""

COURSE_INFO = """📚 <b>Курс таркиби — 8 та дастур</b>

<b>1️⃣</b> Молиявий эркинликка эришиш — 4с 57дақ
<b>2️⃣</b> Модел ҳисоб ва молиявий диагностика — 4с 52дақ
<b>3️⃣</b> Қарз, кредит ва инвестиция қоидалари — 5с 8дақ
<b>4️⃣</b> Кучли жамоани шакллантириш — 4с 41дақ
<b>5️⃣</b> Ходим олиш санъати — 4с 22дақ
<b>6️⃣</b> Сотув тизими ва савдо — 4с 48дақ
<b>7️⃣</b> Беш юлдузли сотувчи тайёрлаш — 4с 30дақ
<b>8️⃣</b> Лойиҳа тақдимоти ва анализ — 4с 58дақ

━━━━━━━━━━━━━━━━━
⏱ <b>Жами: 38 соат 16 дақиқа</b>
💰 Нарх: <b>1 000 000 сўм</b>
📅 Кириш: <b>3 ой</b>"""

ASK_NAME = """✍️ <b>Сотиб олиш жараёни (1/3)</b>

Илтимос, <b>тўлиқ исм-фамилиянгизни</b> ёзинг.

<i>Масалан: Асадбек Ашуров</i>"""

ASK_PHONE = """📱 <b>Сотиб олиш жараёни (2/3)</b>

Раҳмат, <b>{name}</b>!

Энди <b>телефон рақамингизни</b> юборинг.

👇 Пастдаги тугмани босинг ёки ўзингиз ёзинг."""

CONFIRM_DATA = """🤝 <b>Сотиб олиш жараёни (3/3)</b>

Маълумотларингиз:

👤 <b>Исм:</b> {name}
📱 <b>Телефон:</b> <code>{phone}</code>
💬 <b>Telegram:</b> @{username}
💰 <b>Тўлов:</b> 1 000 000 сўм
📅 <b>Кириш:</b> 3 ой

Маълумотлар тўғрими?"""

CHOOSE_PAYMENT = """💳 <b>Тўлов усулини танланг</b>

👤 <b>{name}</b>
📱 <b>{phone}</b>
💰 <b>1 000 000 сўм</b>

👇 Қайси тўлов тизими орқали тўлайсиз?"""

CLICK_PAY = """💳 <b>Click орқали тўлов</b>

📱 Қуйидаги тугмани босинг — Click иловаси очилади.
✅ Сумма ва олиб қабул қилувчи автоматик тўлдирилади.
🔐 Сиз фақат тасдиқлайсиз.

🆔 Буюртма: <code>{trans_id}</code>"""

PAYME_PAY = """💎 <b>Payme орқали тўлов</b>

📱 Қуйидаги тугмани босинг — Payme иловаси очилади.
✅ Сумма ва олиб қабул қилувчи автоматик тўлдирилади.
🔐 Сиз фақат тасдиқлайсиз.

🆔 Буюртма: <code>{trans_id}</code>"""

PAYMENT_SUCCESS = """🎉 <b>Тўлов муваффақиятли қабул қилинди!</b>

💳 Сумма: <b>{amount} сўм</b>
🏦 Тизим: <b>{system}</b>
📅 Сана: {date}
⏰ Кириш муддати: <b>{expiry}</b> гача

👇 Пастдаги тугмани босиб каналга киринг"""

ALREADY_PAID = """✅ <b>Сиз аллақачон тўлов қилгансиз!</b>

📅 Кириш муддати: <b>{expiry}</b> гача

👇 Каналга кириш учун тугмани босинг"""

STATUS_PAID = """✅ <b>Фаол кириш ҳуқуқингиз бор</b>

👤 Исм: <b>{name}</b>
📱 Телефон: <code>{phone}</code>
💰 Сумма: <b>{amount} сўм</b>
🏦 Тизим: <b>{system}</b>
📅 Тўлов санаси: {paid_date}
⏰ Тугаш санаси: <b>{expiry}</b>
📊 Қолган: <b>{days_left} кун</b>"""

STATUS_NO_PAYMENT = """❌ <b>Сизда фаол тўлов йўқ</b>

Курсга обуна бўлиш учун <b>«💳 Сотиб олиш»</b> тугмасини босинг."""

CONTACT_INFO = """📞 <b>Биз билан боғланинг</b>

📱 Телефон:
<code>+998 95 092 46 46</code>
<code>+998 90 099 24 25</code>

💬 Менежерлар:
👉 @AsAsh_Menejer
👉 @menejer_Gulmira

Иш вақти: <b>09:00 — 21:00</b>"""

CANCELLED = "❌ Бекор қилинди.\n\nПастдаги тугмалардан фойдаланинг."

ADMIN_NEW_PAYMENT = """💰 <b>ЯНГИ ТЎЛОВ!</b>

👤 <b>{name}</b>
📱 <code>{phone}</code>
💬 @{username}
🆔 <code>{telegram_id}</code>

💵 <b>{amount:,} сўм</b>
🏦 Тизим: <b>{system}</b>
📅 {date}
⏰ Тугаш: {expiry}

✅ Каналга автоматик қўшилди"""

# ─────────────────────────────────────────────────────────
# БАЗА ДАННЫХ
# ─────────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                custom_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                merchant_trans_id TEXT UNIQUE NOT NULL,
                payment_system TEXT NOT NULL,
                external_id TEXT,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                paid_at TIMESTAMP,
                expiry_at TIMESTAMP,
                removed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_payments_expiry ON payments(expiry_at);
            CREATE INDEX IF NOT EXISTS idx_payments_trans_id ON payments(merchant_trans_id);
        """)
        await db.commit()
    log.info("База данных тайёр")


async def upsert_user(telegram_id, username=None, full_name=None, custom_name=None, phone=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            updates, params = [], []
            if username is not None: updates.append("username=?"); params.append(username)
            if full_name is not None: updates.append("full_name=?"); params.append(full_name)
            if custom_name is not None: updates.append("custom_name=?"); params.append(custom_name)
            if phone is not None: updates.append("phone=?"); params.append(phone)
            if updates:
                params.append(telegram_id)
                await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE telegram_id=?", params)
                await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            return dict(row)
        cur = await db.execute(
            "INSERT INTO users (telegram_id, username, full_name, custom_name, phone) VALUES (?,?,?,?,?)",
            (telegram_id, username, full_name, custom_name, phone)
        )
        await db.commit()
        return {
            "id": cur.lastrowid, "telegram_id": telegram_id, "username": username,
            "full_name": full_name, "custom_name": custom_name, "phone": phone
        }


async def get_active_payment(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.*, u.custom_name, u.phone, u.username FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE u.telegram_id = ? AND p.status = 'paid'
              AND (p.expiry_at IS NULL OR p.expiry_at > CURRENT_TIMESTAMP)
            ORDER BY p.paid_at DESC LIMIT 1
        """, (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_payment(user_id, amount, payment_system):
    merchant_trans_id = f"mol_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, merchant_trans_id, payment_system, amount) VALUES (?,?,?,?)",
            (user_id, merchant_trans_id, payment_system, amount)
        )
        await db.commit()
    return merchant_trans_id


async def get_payment_by_trans_id(merchant_trans_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.*, u.telegram_id, u.username, u.custom_name, u.phone
            FROM payments p JOIN users u ON p.user_id = u.id
            WHERE p.merchant_trans_id = ?
        """, (merchant_trans_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_payment_by_id(payment_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.*, u.telegram_id, u.username, u.custom_name, u.phone
            FROM payments p JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (payment_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def mark_paid(merchant_trans_id, external_id):
    paid_at = datetime.now()
    expiry_at = paid_at + timedelta(days=ACCESS_DAYS)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE payments SET status='paid', external_id=?, paid_at=?, expiry_at=?
            WHERE merchant_trans_id=?
        """, (external_id, paid_at, expiry_at, merchant_trans_id))
        await db.commit()
        cur = await db.execute("""
            SELECT p.*, u.telegram_id, u.username, u.custom_name, u.phone
            FROM payments p JOIN users u ON p.user_id = u.id
            WHERE p.merchant_trans_id = ?
        """, (merchant_trans_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_expired():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.id as payment_id, u.telegram_id FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.status='paid' AND p.expiry_at < CURRENT_TIMESTAMP AND p.removed_at IS NULL
        """)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def mark_removed(payment_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET removed_at=CURRENT_TIMESTAMP WHERE id=?", (payment_id,)
        )
        await db.commit()


async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value)
        )
        await db.commit()


async def get_setting(key):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else None


async def get_channel_id():
    if CHANNEL_ID:
        return CHANNEL_ID
    val = await get_setting("channel_id")
    return int(val) if val else None


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cur.fetchone())[0]
        cur = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount),0), payment_system FROM payments WHERE status='paid' GROUP BY payment_system"
        )
        rows = await cur.fetchall()
        by_system = {r[2]: {"count": r[0], "sum": r[1]} for r in rows}
        cur = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount),0) FROM payments WHERE status='paid'"
        )
        row = await cur.fetchone()
        return {
            "total_users": total_users,
            "paid_count": row[0],
            "revenue": row[1],
            "by_system": by_system,
        }

# ─────────────────────────────────────────────────────────
# CLICK API — Invoice URL
# ─────────────────────────────────────────────────────────

CLICK_API_URL = "https://api.click.uz/v2/merchant"


def _click_auth_header():
    timestamp = str(int(datetime.now().timestamp()))
    digest = hashlib.sha1(f"{timestamp}{CLICK_SECRET_KEY}".encode()).hexdigest()
    return f"{CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"


def click_deep_link(merchant_trans_id, amount):
    """Click ilovaga to'g'ridan-to'g'ri o'tkazadigan link"""
    return (
        f"https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_USER_ID}"
        f"&amount={amount}"
        f"&transaction_param={merchant_trans_id}"
    )


def click_verify_signature(data):
    sign_string = data.get("sign_string", "")
    raw = (
        f"{data.get('click_trans_id','')}"
        f"{data.get('service_id','')}"
        f"{CLICK_SECRET_KEY}"
        f"{data.get('merchant_trans_id','')}"
        f"{data.get('merchant_prepare_id','')}"
        f"{data.get('amount','')}"
        f"{data.get('action','')}"
        f"{data.get('sign_time','')}"
    )
    computed = hashlib.md5(raw.encode()).hexdigest()
    return computed == sign_string

# ─────────────────────────────────────────────────────────
# PAYME — Checkout URL
# ─────────────────────────────────────────────────────────

def payme_deep_link(merchant_trans_id, amount):
    """Payme ilovaga to'g'ridan-to'g'ri o'tkazadigan link.
    Summa tiyin (Payme tiyinda hisoblaydi: 1 so'm = 100 tiyin)
    """
    amount_tiyin = amount * 100
    params = f"m={PAYME_MERCHANT_ID};ac.order={merchant_trans_id};a={amount_tiyin}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"{PAYME_CHECKOUT_URL}/{encoded}"

# ─────────────────────────────────────────────────────────
# TELEGRAM BOT
# ─────────────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


class BuyStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    confirming = State()
    choosing_payment = State()


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BUY)],
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_INFO)],
            [KeyboardButton(text=BTN_CONTACT)],
        ],
        resize_keyboard=True, is_persistent=True,
        input_field_placeholder="Тугмалардан фойдаланинг 👇"
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True
    )


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PHONE, request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True
    )


def confirm_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CONFIRM)],
            [KeyboardButton(text=BTN_EDIT), KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True
    )


def payment_choice_kb(click_url, payme_url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Payme орқали тўлаш", url=payme_url)],
        [InlineKeyboardButton(text="💳 Click орқали тўлаш", url=click_url)],
    ])


def channel_btn(invite_link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Каналга кириш", url=invite_link)]
    ])


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await upsert_user(
        telegram_id=user.id, username=user.username,
        full_name=user.full_name
    )

    active = await get_active_payment(user.id)
    if active:
        expiry = datetime.fromisoformat(active["expiry_at"]).strftime("%d.%m.%Y")
        channel_id = await get_channel_id()
        if channel_id:
            try:
                invite = await bot.create_chat_invite_link(
                    chat_id=channel_id, member_limit=1, name=f"User {user.id}"
                )
                await message.answer(ALREADY_PAID.format(expiry=expiry), reply_markup=main_menu_kb())
                await message.answer("👇 Каналга кириш:", reply_markup=channel_btn(invite.invite_link))
                return
            except Exception as e:
                log.error(f"Invite xato: {e}")

    await message.answer(WELCOME, reply_markup=main_menu_kb())


@dp.message(F.text == BTN_BUY)
async def btn_buy(message: types.Message, state: FSMContext):
    await state.clear()
    active = await get_active_payment(message.from_user.id)
    if active:
        expiry = datetime.fromisoformat(active["expiry_at"]).strftime("%d.%m.%Y")
        channel_id = await get_channel_id()
        if channel_id:
            try:
                invite = await bot.create_chat_invite_link(
                    chat_id=channel_id, member_limit=1, name=f"User {message.from_user.id}"
                )
                await message.answer(ALREADY_PAID.format(expiry=expiry), reply_markup=main_menu_kb())
                await message.answer("👇 Каналга кириш:", reply_markup=channel_btn(invite.invite_link))
                return
            except Exception:
                pass

    await state.set_state(BuyStates.waiting_name)
    await message.answer(ASK_NAME, reply_markup=cancel_kb())


@dp.message(BuyStates.waiting_name, F.text)
async def got_name(message: types.Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        return
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(
            "⚠️ Илтимос, тўғри исм киритинг (2-100 та белги).",
            reply_markup=cancel_kb()
        )
        return
    if name.startswith("/"):
        await message.answer(
            "⚠️ Илтимос, исмингизни ёзинг (буйруқ эмас).",
            reply_markup=cancel_kb()
        )
        return

    await state.update_data(custom_name=name)
    await state.set_state(BuyStates.waiting_phone)
    await message.answer(ASK_PHONE.format(name=name), reply_markup=phone_kb())


@dp.message(BuyStates.waiting_phone, F.contact)
async def got_phone_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("⚠️ Илтимос, <b>ўз</b> рақамингизни юборинг.", reply_markup=phone_kb())
        return
    phone = contact.phone_number.lstrip("+")
    if not phone.startswith("998"):
        phone = "998" + phone[-9:]
    await _show_confirm(message, state, phone)


@dp.message(BuyStates.waiting_phone, F.text)
async def got_phone_text(message: types.Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        return
    if message.text == BTN_PHONE:
        return
    phone_raw = "".join(c for c in message.text if c.isdigit())
    if len(phone_raw) < 9 or len(phone_raw) > 12:
        await message.answer(
            "⚠️ Илтимос, тўғри телефон рақамни киритинг.\n"
            "Масалан: <code>+998 90 123 45 67</code>\n\n"
            "Ёки <b>«📱 Телефон рақамни юбориш»</b> тугмасини босинг.",
            reply_markup=phone_kb()
        )
        return
    if not phone_raw.startswith("998"):
        phone_raw = "998" + phone_raw[-9:]
    await _show_confirm(message, state, phone_raw)


async def _show_confirm(message, state, phone):
    data = await state.get_data()
    name = data.get("custom_name", "?")
    username = message.from_user.username or "—"

    await state.update_data(phone=phone)
    await state.set_state(BuyStates.confirming)

    await message.answer(
        CONFIRM_DATA.format(name=name, phone=phone, username=username),
        reply_markup=confirm_kb()
    )


@dp.message(BuyStates.confirming, F.text == BTN_EDIT)
async def edit_data(message: types.Message, state: FSMContext):
    await state.set_state(BuyStates.waiting_name)
    await message.answer(ASK_NAME, reply_markup=cancel_kb())


@dp.message(BuyStates.confirming, F.text == BTN_CONFIRM)
async def confirm_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("custom_name")
    phone = data.get("phone")

    # Foydalanuvchi ma'lumotlarini saqlash
    user = await upsert_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        custom_name=name,
        phone=phone,
    )

    # Click va Payme uchun alohida to'lov yaratish
    click_trans_id = await create_payment(user["id"], COURSE_PRICE, "click")
    payme_trans_id = await create_payment(user["id"], COURSE_PRICE, "payme")

    click_url = click_deep_link(click_trans_id, COURSE_PRICE)
    payme_url = payme_deep_link(payme_trans_id, COURSE_PRICE)

    await state.update_data(
        click_trans_id=click_trans_id,
        payme_trans_id=payme_trans_id,
    )
    await state.set_state(BuyStates.choosing_payment)

    await message.answer(
        CHOOSE_PAYMENT.format(name=name, phone=phone),
        reply_markup=main_menu_kb()
    )
    await message.answer(
        "👇 Тўлов усулини танланг:",
        reply_markup=payment_choice_kb(click_url, payme_url)
    )

    # Adminga xabar
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🆕 <b>Янги мижоз буюртма берди</b>\n\n"
                f"👤 {name}\n"
                f"📱 <code>{phone}</code>\n"
                f"💬 @{message.from_user.username or '—'}\n"
                f"🆔 <code>{message.from_user.id}</code>\n\n"
                f"⏳ Тўлов кутилмоқда..."
            )
        except Exception:
            pass


@dp.message(F.text == BTN_STATUS)
async def btn_status(message: types.Message, state: FSMContext):
    await state.clear()
    active = await get_active_payment(message.from_user.id)
    if active:
        paid_at = datetime.fromisoformat(active["paid_at"])
        expiry_at = datetime.fromisoformat(active["expiry_at"])
        days_left = (expiry_at - datetime.now()).days
        system_name = "Click" if active["payment_system"] == "click" else "Payme"
        await message.answer(
            STATUS_PAID.format(
                name=active.get("custom_name") or "—",
                phone=active.get("phone") or "—",
                amount=f"{active['amount']:,}",
                system=system_name,
                paid_date=paid_at.strftime("%d.%m.%Y"),
                expiry=expiry_at.strftime("%d.%m.%Y"),
                days_left=max(0, days_left)
            ),
            reply_markup=main_menu_kb()
        )
        channel_id = await get_channel_id()
        if channel_id:
            try:
                invite = await bot.create_chat_invite_link(
                    chat_id=channel_id, member_limit=1, name=f"User {message.from_user.id}"
                )
                await message.answer("👇 Каналга кириш:", reply_markup=channel_btn(invite.invite_link))
            except Exception:
                pass
    else:
        await message.answer(STATUS_NO_PAYMENT, reply_markup=main_menu_kb())


@dp.message(F.text == BTN_INFO)
async def btn_info(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(COURSE_INFO, reply_markup=main_menu_kb())


@dp.message(F.text == BTN_CONTACT)
async def btn_contact(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 @AsAsh_Menejer", url="https://t.me/AsAsh_Menejer")],
        [InlineKeyboardButton(text="💬 @menejer_Gulmira", url="https://t.me/menejer_Gulmira")],
    ])
    await message.answer(CONTACT_INFO, reply_markup=kb)


@dp.message(F.text == BTN_CANCEL)
async def btn_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(CANCELLED, reply_markup=main_menu_kb())


@dp.message(F.text == "/stats")
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    stats = await get_stats()
    channel_id = await get_channel_id()
    by_system_text = ""
    for sys_name, info in stats["by_system"].items():
        display = "Click" if sys_name == "click" else "Payme"
        by_system_text += f"  • {display}: <b>{info['count']}</b> та · <b>{info['sum']:,}</b> сўм\n"
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Жами: <b>{stats['total_users']}</b>\n"
        f"💳 Тўлов: <b>{stats['paid_count']}</b>\n"
        f"💰 Даромад: <b>{stats['revenue']:,} сўм</b>\n\n"
        f"<b>Тизим бўйича:</b>\n{by_system_text or '  — '}\n"
        f"📢 Канал ID: <code>{channel_id or 'Йўқ'}</code>",
        reply_markup=main_menu_kb()
    )


@dp.message(F.text)
async def fallback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
    await message.answer(
        "👇 Пастдаги тугмалардан фойдаланинг:",
        reply_markup=main_menu_kb()
    )


@dp.my_chat_member()
async def bot_added_to_channel(event: ChatMemberUpdated):
    new_status = event.new_chat_member.status
    chat = event.chat
    if chat.type in ("channel", "supergroup") and new_status == ChatMemberStatus.ADMINISTRATOR:
        await set_setting("channel_id", str(chat.id))
        log.info(f"Канал ID сақланди: {chat.id} ({chat.title})")
        if ADMIN_ID:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"✅ Канал аниқланди!\n📢 {chat.title}\n🆔 <code>{chat.id}</code>"
                )
            except Exception:
                pass

# ─────────────────────────────────────────────────────────
# FASTAPI WEBHOOK
# ─────────────────────────────────────────────────────────

app = FastAPI(title="Moliya Bot V2")


def click_response(error=0, error_note="Success", **extra):
    base = {"error": error, "error_note": error_note}
    base.update(extra)
    return base


async def process_payment_complete(payment):
    """Tо'lov tasdiqlangach: kanalga qo'shish + adminga xabar"""
    channel_id = await get_channel_id()
    if not channel_id:
        log.error("Канал ID топилмади!")
        return

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=channel_id, member_limit=1,
            name=f"User {payment['telegram_id']}",
        )
        paid_at = datetime.fromisoformat(payment["paid_at"]) if isinstance(payment["paid_at"], str) else payment["paid_at"]
        expiry_at = datetime.fromisoformat(payment["expiry_at"]) if isinstance(payment["expiry_at"], str) else payment["expiry_at"]
        system_name = "Click" if payment["payment_system"] == "click" else "Payme"

        await bot.send_message(
            payment["telegram_id"],
            PAYMENT_SUCCESS.format(
                amount=f"{payment['amount']:,}",
                system=system_name,
                date=paid_at.strftime("%d.%m.%Y %H:%M"),
                expiry=expiry_at.strftime("%d.%m.%Y"),
            ),
            reply_markup=channel_btn(invite.invite_link)
        )

        if ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                ADMIN_NEW_PAYMENT.format(
                    name=payment.get("custom_name") or "?",
                    phone=payment.get("phone") or "?",
                    username=payment.get("username") or "—",
                    telegram_id=payment["telegram_id"],
                    amount=payment["amount"],
                    system=system_name,
                    date=paid_at.strftime("%d.%m.%Y %H:%M"),
                    expiry=expiry_at.strftime("%d.%m.%Y"),
                )
            )
    except Exception as e:
        log.exception(f"Process payment xato: {e}")


@app.get("/")
async def root():
    return {"status": "ok", "service": "moliya-bot-v2"}


@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

# ── CLICK WEBHOOK ──

@app.post("/click/prepare")
async def click_prepare(
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    amount: str = Form(...),
    action: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    error: str = Form("0"),
    click_paydoc_id: str = Form(None),
):
    data = {
        "click_trans_id": click_trans_id, "service_id": service_id,
        "merchant_trans_id": merchant_trans_id, "amount": amount,
        "action": action, "sign_time": sign_time, "sign_string": sign_string,
        "merchant_prepare_id": "",
    }
    log.info(f"Click PREPARE: {merchant_trans_id}")
    if not click_verify_signature(data):
        return click_response(-1, "SIGN CHECK FAILED!")
    payment = await get_payment_by_trans_id(merchant_trans_id)
    if not payment:
        return click_response(-5, "User does not exist")
    if payment["status"] == "paid":
        return click_response(-4, "Already paid")
    if abs(float(payment["amount"]) - float(amount)) > 0.01:
        return click_response(-2, "Incorrect parameter amount")
    if int(action) != 0:
        return click_response(-3, "Action not found")
    return click_response(
        error=0, error_note="Success",
        click_trans_id=click_trans_id,
        merchant_trans_id=merchant_trans_id,
        merchant_prepare_id=payment["id"],
    )


@app.post("/click/complete")
async def click_complete(
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: str = Form(...),
    amount: str = Form(...),
    action: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    error: str = Form("0"),
    error_note: str = Form(""),
    click_paydoc_id: str = Form(None),
):
    data = {
        "click_trans_id": click_trans_id, "service_id": service_id,
        "merchant_trans_id": merchant_trans_id, "merchant_prepare_id": merchant_prepare_id,
        "amount": amount, "action": action, "sign_time": sign_time, "sign_string": sign_string,
    }
    log.info(f"Click COMPLETE: {merchant_trans_id}, error={error}")
    if not click_verify_signature(data):
        return click_response(-1, "SIGN CHECK FAILED!")
    payment = await get_payment_by_trans_id(merchant_trans_id)
    if not payment:
        return click_response(-5, "User does not exist")
    if int(error) < 0:
        return click_response(int(error), error_note or "Cancelled by user")
    if payment["status"] == "paid":
        return click_response(
            -4, "Already paid",
            click_trans_id=click_trans_id,
            merchant_trans_id=merchant_trans_id,
            merchant_confirm_id=payment["id"],
        )
    updated = await mark_paid(merchant_trans_id, click_trans_id)
    if updated:
        asyncio.create_task(process_payment_complete(updated))
    return click_response(
        error=0, error_note="Success",
        click_trans_id=click_trans_id,
        merchant_trans_id=merchant_trans_id,
        merchant_confirm_id=payment["id"],
    )

# ── PAYME WEBHOOK ──

def payme_error(code, message, data=None, request_id=None):
    err = {
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    if data:
        err["error"]["data"] = data
    return err


def payme_result(result, request_id=None):
    return {"id": request_id, "result": result}


def payme_check_auth(request: Request) -> bool:
    """Payme Basic Auth tekshirish"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        login, password = decoded.split(":", 1)
        # Login = "Paycom", password = bizning Secret Key
        return login == "Paycom" and password == PAYME_SECRET_KEY
    except Exception:
        return False


@app.post("/payme")
async def payme_webhook(request: Request):
    """Payme Merchant API webhook"""
    try:
        body = await request.json()
    except Exception:
        return payme_error(-32700, "Parse error")

    request_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    # Auth tekshirish
    if not payme_check_auth(request):
        return payme_error(-32504, "Insufficient privileges", request_id=request_id)

    log.info(f"Payme {method}: {params}")

    # ── CheckPerformTransaction ──
    if method == "CheckPerformTransaction":
        account = params.get("account", {})
        order = account.get("order", "")
        amount = params.get("amount", 0)

        payment = await get_payment_by_trans_id(order)
        if not payment:
            return payme_error(-31050, "Order not found",
                              data={"name": "order"}, request_id=request_id)

        expected_tiyin = payment["amount"] * 100
        if amount != expected_tiyin:
            return payme_error(-31001, "Wrong amount", request_id=request_id)

        if payment["status"] == "paid":
            return payme_error(-31099, "Order already paid", request_id=request_id)

        return payme_result({"allow": True}, request_id=request_id)

    # ── CreateTransaction ──
    elif method == "CreateTransaction":
        payme_id = params.get("id", "")
        time_ms = params.get("time", 0)
        account = params.get("account", {})
        order = account.get("order", "")
        amount = params.get("amount", 0)

        payment = await get_payment_by_trans_id(order)
        if not payment:
            return payme_error(-31050, "Order not found",
                              data={"name": "order"}, request_id=request_id)

        # Avval shu tranzaktsiya yaratilganmi?
        if payment.get("external_id") == payme_id:
            return payme_result({
                "create_time": time_ms,
                "transaction": str(payment["id"]),
                "state": 1,
            }, request_id=request_id)

        if payment["status"] != "pending":
            return payme_error(-31008, "Unable to perform operation", request_id=request_id)

        # external_id ni saqlash (tranzaktsiya ID)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE payments SET external_id=?, status='prepared' WHERE merchant_trans_id=?",
                (payme_id, order)
            )
            await db.commit()

        return payme_result({
            "create_time": time_ms,
            "transaction": str(payment["id"]),
            "state": 1,
        }, request_id=request_id)

    # ── PerformTransaction ──
    elif method == "PerformTransaction":
        payme_id = params.get("id", "")

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM payments WHERE external_id=? AND payment_system='payme'",
                (payme_id,)
            )
            payment = await cur.fetchone()

        if not payment:
            return payme_error(-31003, "Transaction not found", request_id=request_id)

        payment_dict = dict(payment)

        if payment_dict["status"] == "paid":
            paid_time = datetime.fromisoformat(payment_dict["paid_at"]) if isinstance(payment_dict["paid_at"], str) else payment_dict["paid_at"]
            return payme_result({
                "perform_time": int(paid_time.timestamp() * 1000),
                "transaction": str(payment_dict["id"]),
                "state": 2,
            }, request_id=request_id)

        # To'lovni tasdiqlash
        updated = await mark_paid(payment_dict["merchant_trans_id"], payme_id)
        if updated:
            asyncio.create_task(process_payment_complete(updated))

        perform_time = datetime.now()
        return payme_result({
            "perform_time": int(perform_time.timestamp() * 1000),
            "transaction": str(payment_dict["id"]),
            "state": 2,
        }, request_id=request_id)

    # ── CancelTransaction ──
    elif method == "CancelTransaction":
        payme_id = params.get("id", "")
        reason = params.get("reason", 0)

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM payments WHERE external_id=? AND payment_system='payme'",
                (payme_id,)
            )
            payment = await cur.fetchone()

        if not payment:
            return payme_error(-31003, "Transaction not found", request_id=request_id)

        payment_dict = dict(payment)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE payments SET status='cancelled' WHERE id=?", (payment_dict["id"],)
            )
            await db.commit()

        return payme_result({
            "cancel_time": int(datetime.now().timestamp() * 1000),
            "transaction": str(payment_dict["id"]),
            "state": -1 if payment_dict["status"] != "paid" else -2,
        }, request_id=request_id)

    # ── CheckTransaction ──
    elif method == "CheckTransaction":
        payme_id = params.get("id", "")

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM payments WHERE external_id=? AND payment_system='payme'",
                (payme_id,)
            )
            payment = await cur.fetchone()

        if not payment:
            return payme_error(-31003, "Transaction not found", request_id=request_id)

        payment_dict = dict(payment)
        state = 1
        perform_time = 0
        cancel_time = 0
        if payment_dict["status"] == "paid":
            state = 2
            paid_dt = datetime.fromisoformat(payment_dict["paid_at"]) if isinstance(payment_dict["paid_at"], str) else payment_dict["paid_at"]
            perform_time = int(paid_dt.timestamp() * 1000)
        elif payment_dict["status"] == "cancelled":
            state = -1

        created_dt = datetime.fromisoformat(payment_dict["created_at"]) if isinstance(payment_dict["created_at"], str) else payment_dict["created_at"]
        return payme_result({
            "create_time": int(created_dt.timestamp() * 1000),
            "perform_time": perform_time,
            "cancel_time": cancel_time,
            "transaction": str(payment_dict["id"]),
            "state": state,
            "reason": None,
        }, request_id=request_id)

    # ── GetStatement ──
    elif method == "GetStatement":
        return payme_result({"transactions": []}, request_id=request_id)

    return payme_error(-32601, "Method not found", request_id=request_id)

# ─────────────────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────────────────

async def remove_expired_users():
    log.info("Муддати тугаганларни текшириш...")
    channel_id = await get_channel_id()
    if not channel_id:
        log.warning("Channel ID йўқ")
        return
    expired = await get_expired()
    log.info(f"Топилди: {len(expired)} та")
    for record in expired:
        try:
            await bot.ban_chat_member(channel_id, record["telegram_id"])
            await asyncio.sleep(0.5)
            await bot.unban_chat_member(channel_id, record["telegram_id"])
            await mark_removed(record["payment_id"])
            try:
                await bot.send_message(
                    record["telegram_id"],
                    "ℹ️ <b>3 ойлик кириш муддатингиз тугади</b>\n\n"
                    "Курсни қайта сотиб олиш учун <b>«💳 Сотиб олиш»</b> тугмасини босинг.",
                    reply_markup=main_menu_kb()
                )
            except Exception:
                pass
            await asyncio.sleep(1)
        except Exception as e:
            log.error(f"Чиқариш хато {record['telegram_id']}: {e}")

# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

async def setup_bot_commands():
    """Eski commandlarni barcha scope'lardan tozalash"""
    from aiogram.types import (
        BotCommand, BotCommandScopeChat, BotCommandScopeDefault,
        BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats,
        BotCommandScopeAllChatAdministrators
    )
    for scope in [
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
        BotCommandScopeAllChatAdministrators(),
    ]:
        try:
            await bot.delete_my_commands(scope=scope)
        except Exception as e:
            log.warning(f"Delete xato: {e}")

    if ADMIN_ID:
        try:
            await bot.set_my_commands(
                commands=[BotCommand(command="stats", description="📊 Статистика")],
                scope=BotCommandScopeChat(chat_id=ADMIN_ID)
            )
        except Exception as e:
            log.warning(f"Admin commands xato: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await setup_bot_commands()

    asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))
    log.info("✅ Бот ишга тушди")

    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(remove_expired_users, "cron", hour=3, minute=0)
    scheduler.start()
    log.info("✅ Scheduler (ҳар куни 03:00)")

    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                "🚀 <b>Бот V2 ишга тушди!</b>\n\n"
                f"💳 Click: <code>{CLICK_SERVICE_ID}</code>\n"
                f"💎 Payme: <code>{PAYME_MERCHANT_ID[:8]}...</code>\n"
                f"💰 Нарх: <b>{COURSE_PRICE:,} сўм</b>"
            )
        except Exception:
            pass

    yield
    await bot.session.close()


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
