"""
Молиявий Эркинлик Бот
=====================
Telegram bot + Click to'lov + 3 oylik kanal kirish.
ҲАММАСИ ТУГМАЛАР ОРҚАЛИ. Мижоз ҳеч нарса ёзмайди.
"""

import asyncio
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
    KeyboardButton, ReplyKeyboardMarkup,
    ChatMemberUpdated,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ
# ─────────────────────────────────────────────────────────
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_ID_ENV = os.getenv("CHANNEL_ID", "")
CHANNEL_ID = int(CHANNEL_ID_ENV) if CHANNEL_ID_ENV else None

CLICK_SERVICE_ID = int(os.getenv("CLICK_SERVICE_ID", "0"))
CLICK_MERCHANT_USER_ID = int(os.getenv("CLICK_MERCHANT_USER_ID", "0"))
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")

COURSE_PRICE = int(os.getenv("COURSE_PRICE", "1000000"))
ACCESS_DAYS = int(os.getenv("ACCESS_DAYS", "90"))

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
PORT = int(os.getenv("PORT", "8080"))
DB_PATH = os.getenv("DB_PATH", "data.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("moliya")

# ─────────────────────────────────────────────────────────
# ТУГМАЛАР МАТНЛАРИ
# ─────────────────────────────────────────────────────────
BTN_BUY = "💳 Сотиб олиш"
BTN_STATUS = "📊 Менинг ҳолатим"
BTN_INFO = "ℹ️ Курс ҳақида"
BTN_CONTACT = "📞 Менежер билан боғланиш"
BTN_CANCEL = "❌ Бекор қилиш"
BTN_PHONE = "📱 Телефон рақамни юбориш"

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

<b>1️⃣</b> Молиявий эркинликка эришиш
<i>4 соат 57 дақиқа</i>

<b>2️⃣</b> Модел ҳисоб ва молиявий диагностика
<i>4 соат 52 дақиқа</i>

<b>3️⃣</b> Қарз, кредит ва инвестиция қоидалари
<i>5 соат 8 дақиқа</i>

<b>4️⃣</b> Кучли жамоани шакллантириш
<i>4 соат 41 дақиқа</i>

<b>5️⃣</b> Ходим олиш санъати
<i>4 соат 22 дақиқа</i>

<b>6️⃣</b> Сотув тизими ва савдо
<i>4 соат 48 дақиқа</i>

<b>7️⃣</b> Беш юлдузли сотувчи тайёрлаш
<i>4 соат 30 дақиқа</i>

<b>8️⃣</b> Лойиҳа тақдимоти ва анализ
<i>4 соат 58 дақиқа</i>

━━━━━━━━━━━━━━━━━
⏱ <b>Жами: 38 соат 16 дақиқа</b>
💰 Нарх: <b>1 000 000 сўм</b>
📅 Кириш: <b>3 ой</b>"""

PHONE_REQUEST = """📞 <b>Тўловни амалга ошириш</b>

Илтимос, телефон рақамингизни юборинг.

📩 Click тўлов тизими шу рақамга СМС орқали тўлов ҳаволасини юборади.

👇 Пастдаги тугмани босинг"""

INVOICE_CREATED = """✅ <b>Тўлов ҳаволаси яратилди!</b>

📱 Телефон: <code>{phone}</code>
💰 Сумма: <b>{amount} сўм</b>
🆔 Буюртма: <code>{trans_id}</code>

📩 <b>Click СМС юборди.</b>
СМСдаги ҳаволани босиб тўланг.

⏳ Тўлов амалга оширилгач, ботга <b>каналга кириш ҳаволаси</b> автоматик юборилади."""

PAYMENT_SUCCESS = """🎉 <b>Тўлов муваффақиятли қабул қилинди!</b>

💳 Сумма: <b>{amount} сўм</b>
📅 Сана: {date}
⏰ Кириш муддати: <b>{expiry}</b> гача

👇 Пастдаги тугмани босиб каналга киринг"""

ALREADY_PAID = """✅ <b>Сиз аллақачон тўлов қилгансиз!</b>

📅 Кириш муддати: <b>{expiry}</b> гача

👇 Каналга кириш учун тугмани босинг"""

STATUS_PAID = """✅ <b>Фаол кириш ҳуқуқингиз бор</b>

💰 Сумма: <b>{amount} сўм</b>
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

Иш вақти: <b>09:00 — 21:00</b>
Якшанба — дам олиш куни"""

CANCELLED = "❌ Бекор қилинди.\n\nПастдаги тугмалардан фойдаланинг."

ADMIN_NEW_PAYMENT = """💰 <b>ЯНГИ ТЎЛОВ!</b>

👤 {name} (@{username})
📱 {phone}
🆔 <code>{telegram_id}</code>
💵 <b>{amount:,} сўм</b>
🎯 Click: <code>{click_trans_id}</code>
📅 {date}
⏰ Тугаш: {expiry}"""

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
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                merchant_trans_id TEXT UNIQUE NOT NULL,
                click_trans_id TEXT,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                invoice_id TEXT,
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


async def get_or_create_user(telegram_id, username=None, full_name=None, phone=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            if phone:
                await db.execute(
                    "UPDATE users SET phone=?, full_name=?, username=? WHERE telegram_id=?",
                    (phone, full_name, username, telegram_id)
                )
                await db.commit()
            return dict(row)
        cur = await db.execute(
            "INSERT INTO users (telegram_id, username, full_name, phone) VALUES (?, ?, ?, ?)",
            (telegram_id, username, full_name, phone)
        )
        await db.commit()
        return {"id": cur.lastrowid, "telegram_id": telegram_id, "username": username,
                "full_name": full_name, "phone": phone}


async def get_active_payment(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.* FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE u.telegram_id = ? AND p.status = 'paid'
              AND (p.expiry_at IS NULL OR p.expiry_at > CURRENT_TIMESTAMP)
            ORDER BY p.paid_at DESC LIMIT 1
        """, (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_payment(user_id, amount):
    merchant_trans_id = f"mol_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, merchant_trans_id, amount) VALUES (?, ?, ?)",
            (user_id, merchant_trans_id, amount)
        )
        await db.commit()
    return merchant_trans_id


async def update_payment_invoice(merchant_trans_id, invoice_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET invoice_id=? WHERE merchant_trans_id=?",
            (invoice_id, merchant_trans_id)
        )
        await db.commit()


async def get_payment(merchant_trans_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.*, u.telegram_id, u.username, u.full_name, u.phone
            FROM payments p JOIN users u ON p.user_id = u.id
            WHERE p.merchant_trans_id = ?
        """, (merchant_trans_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def mark_prepared(merchant_trans_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status='prepared' WHERE merchant_trans_id=?",
            (merchant_trans_id,)
        )
        await db.commit()
        cur = await db.execute(
            "SELECT id FROM payments WHERE merchant_trans_id=?", (merchant_trans_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def mark_paid(merchant_trans_id, click_trans_id):
    paid_at = datetime.now()
    expiry_at = paid_at + timedelta(days=ACCESS_DAYS)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE payments SET status='paid', click_trans_id=?, paid_at=?, expiry_at=?
            WHERE merchant_trans_id=?
        """, (click_trans_id, paid_at, expiry_at, merchant_trans_id))
        await db.commit()
        cur = await db.execute("""
            SELECT p.*, u.telegram_id, u.username, u.full_name, u.phone
            FROM payments p JOIN users u ON p.user_id = u.id
            WHERE p.merchant_trans_id = ?
        """, (merchant_trans_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_expired_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT p.id as payment_id, u.telegram_id, u.full_name
            FROM payments p JOIN users u ON p.user_id = u.id
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
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
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
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status='paid'"
        )
        row = await cur.fetchone()
        return {"total_users": total_users, "paid_count": row[0], "revenue": row[1]}

# ─────────────────────────────────────────────────────────
# CLICK API
# ─────────────────────────────────────────────────────────

CLICK_API_URL = "https://api.click.uz/v2/merchant"


def _click_auth_header():
    timestamp = str(int(datetime.now().timestamp()))
    digest = hashlib.sha1(f"{timestamp}{CLICK_SECRET_KEY}".encode()).hexdigest()
    return f"{CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"


async def click_create_invoice(amount, phone, merchant_trans_id):
    url = f"{CLICK_API_URL}/invoice/create"
    payload = {
        "service_id": CLICK_SERVICE_ID,
        "amount": amount,
        "phone_number": phone,
        "merchant_trans_id": merchant_trans_id,
    }
    headers = {
        "Auth": _click_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    log.info(f"Click invoice: {merchant_trans_id} → {phone}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=15) as resp:
            data = await resp.json()
            log.info(f"Click javob: {data}")
            return data


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
    is_valid = computed == sign_string
    if not is_valid:
        log.warning(f"Signature XATO: kutilgan {computed}, kelgan {sign_string}")
    return is_valid

# ─────────────────────────────────────────────────────────
# TELEGRAM BOT
# ─────────────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


class BuyStates(StatesGroup):
    waiting_phone = State()


def main_menu_kb():
    """Асосий менюнинг доимий тугмалари (доим қуйида)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BUY)],
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_INFO)],
            [KeyboardButton(text=BTN_CONTACT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Тугмалардан фойдаланинг 👇"
    )


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PHONE, request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="📱 Телефон рақамни юбориш тугмасини босинг"
    )


def channel_btn(invite_link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Каналга кириш", url=invite_link)]
    ])


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await get_or_create_user(telegram_id=user.id, username=user.username, full_name=user.full_name)

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
                await message.answer("👇 Каналга кириш ҳаволаси:", reply_markup=channel_btn(invite.invite_link))
                return
            except Exception as e:
                log.error(f"Invite link xato: {e}")

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
                await message.answer("👇 Каналга кириш ҳаволаси:", reply_markup=channel_btn(invite.invite_link))
                return
            except Exception:
                pass

    await state.set_state(BuyStates.waiting_phone)
    await message.answer(PHONE_REQUEST, reply_markup=phone_kb())


@dp.message(F.text == BTN_STATUS)
async def btn_status(message: types.Message, state: FSMContext):
    await state.clear()
    active = await get_active_payment(message.from_user.id)
    if active:
        paid_at = datetime.fromisoformat(active["paid_at"])
        expiry_at = datetime.fromisoformat(active["expiry_at"])
        days_left = (expiry_at - datetime.now()).days
        await message.answer(
            STATUS_PAID.format(
                amount=f"{active['amount']:,}",
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


@dp.message(BuyStates.waiting_phone, F.contact)
async def got_phone(message: types.Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Илтимос, <b>ўз</b> телефон рақамингизни юборинг.",
            reply_markup=phone_kb()
        )
        return

    phone = contact.phone_number.lstrip("+")
    if not phone.startswith("998"):
        phone = "998" + phone[-9:]

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        phone=phone,
    )
    merchant_trans_id = await create_payment(user["id"], COURSE_PRICE)
    await state.clear()
    await message.answer("⏳ Тўлов ҳаволаси яратилмоқда...", reply_markup=main_menu_kb())

    try:
        result = await click_create_invoice(COURSE_PRICE, phone, merchant_trans_id)
        if result.get("error_code", -1) != 0:
            await message.answer(
                f"❌ Хатолик: {result.get('error_note', 'номаълум')}\n\nМенежер билан боғланинг.",
                reply_markup=main_menu_kb()
            )
            return

        invoice_id = str(result.get("invoice_id", ""))
        await update_payment_invoice(merchant_trans_id, invoice_id)
        await message.answer(
            INVOICE_CREATED.format(
                phone=phone,
                amount=f"{COURSE_PRICE:,}",
                trans_id=merchant_trans_id
            ),
            reply_markup=main_menu_kb()
        )

        if ADMIN_ID:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🆕 Янги тўлов яратилди\n\n"
                    f"👤 {message.from_user.full_name} (@{message.from_user.username})\n"
                    f"📱 {phone}\n"
                    f"🆔 {merchant_trans_id}\n"
                    f"💵 {COURSE_PRICE:,} сўм"
                )
            except Exception:
                pass
    except Exception:
        log.exception("Click invoice xato")
        await message.answer(
            "❌ Техник хатолик. Менежер билан боғланинг.",
            reply_markup=main_menu_kb()
        )


@dp.message(BuyStates.waiting_phone)
async def wrong_phone_input(message: types.Message):
    if message.text == BTN_CANCEL:
        return
    await message.answer(
        f"⚠️ Илтимос, пастдаги <b>«{BTN_PHONE}»</b> тугмасини босинг.",
        reply_markup=phone_kb()
    )


@dp.message(F.text == "/stats")
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    stats = await get_stats()
    channel_id = await get_channel_id()
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Жами: <b>{stats['total_users']}</b>\n"
        f"💳 Тўлов: <b>{stats['paid_count']}</b>\n"
        f"💰 Даромад: <b>{stats['revenue']:,} сўм</b>\n\n"
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
                    f"✅ Бот канални автоматик аниқлади!\n\n"
                    f"📢 Канал: <b>{chat.title}</b>\n"
                    f"🆔 ID: <code>{chat.id}</code>"
                )
            except Exception:
                pass

# ─────────────────────────────────────────────────────────
# FASTAPI WEBHOOK
# ─────────────────────────────────────────────────────────

def click_response(error=0, error_note="Success", **extra):
    base = {"error": error, "error_note": error_note}
    base.update(extra)
    return base


async def process_payment_complete(payment):
    channel_id = await get_channel_id()
    if not channel_id:
        log.error("Канал ID топилмаган!")
        return

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=channel_id, member_limit=1, name=f"User {payment['telegram_id']}",
        )
        paid_at = datetime.fromisoformat(payment["paid_at"]) if isinstance(payment["paid_at"], str) else payment["paid_at"]
        expiry_at = datetime.fromisoformat(payment["expiry_at"]) if isinstance(payment["expiry_at"], str) else payment["expiry_at"]

        await bot.send_message(
            payment["telegram_id"],
            PAYMENT_SUCCESS.format(
                amount=f"{payment['amount']:,}",
                date=paid_at.strftime("%d.%m.%Y %H:%M"),
                expiry=expiry_at.strftime("%d.%m.%Y"),
            ),
            reply_markup=channel_btn(invite.invite_link)
        )
        if ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                ADMIN_NEW_PAYMENT.format(
                    name=payment.get("full_name") or "?",
                    username=payment.get("username") or "?",
                    phone=payment.get("phone") or "?",
                    telegram_id=payment["telegram_id"],
                    amount=payment["amount"],
                    click_trans_id=payment.get("click_trans_id") or "?",
                    date=paid_at.strftime("%d.%m.%Y %H:%M"),
                    expiry=expiry_at.strftime("%d.%m.%Y"),
                )
            )
    except Exception as e:
        log.exception(f"Process payment xato: {e}")


app = FastAPI(title="Moliya Bot Webhook")


@app.get("/")
async def root():
    return {"status": "ok", "service": "moliya-bot"}


@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}


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
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": action,
        "sign_time": sign_time,
        "sign_string": sign_string,
        "merchant_prepare_id": "",
    }
    log.info(f"Click PREPARE: {merchant_trans_id}")

    if not click_verify_signature(data):
        return click_response(-1, "SIGN CHECK FAILED!")

    payment = await get_payment(merchant_trans_id)
    if not payment:
        return click_response(-5, "User does not exist")
    if payment["status"] == "paid":
        return click_response(-4, "Already paid")

    expected = float(payment["amount"])
    actual = float(amount)
    if abs(expected - actual) > 0.01:
        return click_response(-2, "Incorrect parameter amount")
    if int(action) != 0:
        return click_response(-3, "Action not found")

    merchant_prepare_id = await mark_prepared(merchant_trans_id)
    return click_response(
        error=0, error_note="Success",
        click_trans_id=click_trans_id,
        merchant_trans_id=merchant_trans_id,
        merchant_prepare_id=merchant_prepare_id,
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
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": merchant_prepare_id,
        "amount": amount,
        "action": action,
        "sign_time": sign_time,
        "sign_string": sign_string,
    }
    log.info(f"Click COMPLETE: {merchant_trans_id}, error={error}")

    if not click_verify_signature(data):
        return click_response(-1, "SIGN CHECK FAILED!")

    payment = await get_payment(merchant_trans_id)
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


# ─────────────────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────────────────

async def remove_expired_users():
    log.info("Муддати тугаганларни текшириш...")
    channel_id = await get_channel_id()
    if not channel_id:
        log.warning("Channel ID йўқ")
        return

    expired = await get_expired_users()
    log.info(f"Топилди: {len(expired)} та")

    for record in expired:
        try:
            await bot.ban_chat_member(channel_id, record["telegram_id"])
            await asyncio.sleep(0.5)
            await bot.unban_chat_member(channel_id, record["telegram_id"])
            await mark_removed(record["payment_id"])
            log.info(f"Чиқарилди: {record['telegram_id']}")

            try:
                await bot.send_message(
                    record["telegram_id"],
                    "ℹ️ <b>3 ойлик кириш муддатингиз тугади</b>\n\n"
                    "Сиз каналдан чиқарилдингиз.\n\n"
                    "Курсни қайта сотиб олиш учун <b>«💳 Сотиб олиш»</b> тугмасини босинг.",
                    reply_markup=main_menu_kb()
                )
            except Exception:
                pass

            await asyncio.sleep(1)
        except Exception as e:
            log.error(f"Чиқаришда хато {record['telegram_id']}: {e}")


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

async def setup_bot_commands():
    """Eski commandlarni barcha scope'lardan tozalash va faqat adminga /stats qoldirish"""
    from aiogram.types import (
        BotCommand, BotCommandScopeChat, BotCommandScopeDefault,
        BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats,
        BotCommandScopeAllChatAdministrators
    )
    # Barcha scope'lardan eski commandlarni o'chirish
    for scope in [
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
        BotCommandScopeAllChatAdministrators(),
    ]:
        try:
            await bot.delete_my_commands(scope=scope)
        except Exception as e:
            log.warning(f"Delete commands xato ({type(scope).__name__}): {e}")

    # Adminga - statistika buyrug'i
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
                "🚀 <b>Бот ишга тушди!</b>\n\n"
                f"🔗 Webhook: <code>{WEBHOOK_HOST or 'муҳит ўрнатилмаган'}</code>\n"
                f"💳 Service: <code>{CLICK_SERVICE_ID}</code>\n"
                f"💰 Нарх: <b>{COURSE_PRICE:,} сўм</b>"
            )
        except Exception:
            pass

    yield
    await bot.session.close()


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
