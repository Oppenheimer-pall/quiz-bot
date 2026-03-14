#!/usr/bin/env python3
"""
SUPER QUIZ BOT v3.3
+ PDF → AI test tuzish (Claude API)
+ Feedback tizimi (⭐ baho, 💬 izoh, 👍👎)
"""

import logging, random, sqlite3, os, json, asyncio
from datetime import datetime
from io import BytesIO

try:
    from pypdf import PdfReader
    PYPDF_OK = True
except ImportError:
    PYPDF_OK = False

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

try:
    from PIL import Image, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PollAnswerHandler, ContextTypes, MessageHandler, filters
)

# ── CONFIG ────────────────────────────────────────────────
TOKEN          = os.getenv("BOT_TOKEN", "8657957504:AAEqdqcK9Ljix2-DYiYoXFgWiuWJzIkq9c8")
GEMINI_KEY     = os.getenv("GEMINI_API_KEY", "")
_adm      = os.getenv("ADMIN_IDS", "0")
ADMIN_IDS = [int(x) for x in _adm.split(",") if x.strip().isdigit()]
DB_PATH   = "quiz.db"
TIMER_SEC = 30

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ── MATNLAR ───────────────────────────────────────────────
TX = {
    "uz": {
        "welcome"     : "Salom, {name}! 👋\nIqtisodiyot Super Quiz Botiga xush kelibsiz!",
        "choose_lang" : "🌐 Tilni tanlang:",
        "main_menu"   : "📚 Asosiy menyu — bo'limni tanlang:",
        "topic_menu"  : "{cat} — mavzu tanlang:",
        "coming_soon" : "⏳ Bu bo'lim tez kunda qo'shiladi!",
        "quiz_start"  : "✅ Mavzu: {topic}\n📝 Savollar: {n} ta\n⏱ Har savolga {timer} soniya\n\nBoshlanmoqda...",
        "q_label"     : "{i}/{n}",
        "time_up"     : "⏰ Vaqt tugadi! Keyingi savol...",
        "result"      : "{emoji} Test yakunlandi!\n\n📊 Natija: {s}/{total} ({p}%)\nBaho: {grade}\n\n/start — Qayta boshlash",
        "grade_5"     : "A'lo ⭐⭐⭐",
        "grade_4"     : "Yaxshi ✅",
        "grade_3"     : "Qoniqarli 📝",
        "grade_2"     : "Qayta o'qing ❌",
        "top_title"   : "🏆 TOP-10 — {topic}",
        "top_empty"   : "Hali natijalar yo'q.",
        "stats"       : "📊 Statistika:\n👥 Foydalanuvchilar: {u}\n📝 Testlar: {t}\n📈 O'rtacha ball: {a}%",
        "not_admin"   : "❌ Siz admin emassiz.",
        "bcast_ok"    : "✅ {n} ta foydalanuvchiga yuborildi.",
        "addq_help"   : "Savol qo'shish:\n\n/addq\nCAT:mikro\nTOPIC:1\nQ:Savol\nA:A\nB:B\nC:C\nD:D\nANS:0\nEXP:Izoh\n\nCAT: mikro|makro|pul",
        "addq_ok"     : "✅ Savol qo'shildi!",
        "addq_err"    : "❌ Format xato.",
        "all_mix"     : "🔀 Barcha aralash",
        "back_cat"    : "⬅️ Orqaga",
        "help"        : "📌 Buyruqlar:\n/start — Bosh menyu\n/top — Reyting\n/stats — Statistika\n/admin — Admin\n/feedback — Fikrlar (admin)",
        # PDF
        "pdf_recv"    : "📄 PDF qabul qilindi! AI test tuzmoqda... ⏳ (30-60 soniya)",
        "pdf_no_text" : "❌ PDF dan matn o'qib bo'lmadi.",
        "pdf_no_ai"   : "❌ AI xizmati sozlanmagan (GEMINI_API_KEY yo'q). Admin bilan bog'laning.",
        "pdf_fail"    : "❌ Test tuzishda xato yuz berdi. Qayta urinib ko'ring.",
        "pdf_done"    : "✅ {n} ta savol tayyorlandi! Boshlanmoqda...",
        # Feedback
        "fb_ask"      : "📝 Test haqida fikringiz?",
        # Timer/Pause
        "timer_msg"   : "⏱ Savol {i}/{n}  |  {bar}  {sec} sek",
        "paused_msg"  : "⏸ <b>To\'xtatildi</b>\n\n⏱ Qolgan vaqt: <b>{sec} sek</b>\nDavom etish uchun tugmani bosing.",
        "btn_pause"   : "⏸ Pauza",
        "btn_resume"  : "▶️ Davom etish",
        "btn_stop"    : "🚫 Testni tugatish",
        "stop_confirm": "✅ Test to\'xtatildi.",
        "fb_thumb_q"  : "Test foydali boldimi?",
        "fb_star_q"   : "Bahoning nechta yulduz?",
        "fb_comment_q": "💬 Izohing bo'lsa yoz (yoki /skip):",
        "fb_done"     : "✅ Fikringiz uchun rahmat!",
        "fb_skip"     : "Tushunildi, keyingisida! 👍",
        # ReplyKeyboard
        "btn_tests"   : "📝 Testlar",
        "btn_mikro"   : "📊 Mikroiqtisodiyot",
        "btn_makro"   : "📈 Makroiqtisodiyot",
        "btn_pul"     : "🏦 Pul va Bank",
        "btn_pdf"     : "📄 PDF dan test",
        "btn_top"     : "🏆 Reyting",
        "btn_stats"   : "📊 Statistika",
        "btn_feedback": "💬 Fikrlar",
        "btn_help"    : "ℹ️ Yordam",
    },
    "ru": {
        "welcome"     : "Привет, {name}! 👋\nДобро пожаловать в Super Quiz Bot!",
        "choose_lang" : "🌐 Выберите язык:",
        "main_menu"   : "📚 Главное меню — выберите раздел:",
        "topic_menu"  : "{cat} — выберите тему:",
        "coming_soon" : "⏳ Этот раздел скоро будет добавлен!",
        "quiz_start"  : "✅ Тема: {topic}\n📝 Вопросов: {n}\n⏱ На каждый {timer} секунд\n\nНачинаем...",
        "q_label"     : "{i}/{n}",
        "time_up"     : "⏰ Время вышло! Следующий вопрос...",
        "result"      : "{emoji} Тест завершён!\n\n📊 Результат: {s}/{total} ({p}%)\nОценка: {grade}\n\n/start — Начать заново",
        "grade_5"     : "Отлично ⭐⭐⭐",
        "grade_4"     : "Хорошо ✅",
        "grade_3"     : "Удовлетворительно 📝",
        "grade_2"     : "Повторите материал ❌",
        "top_title"   : "🏆 ТОП-10 — {topic}",
        "top_empty"   : "Результатов пока нет.",
        "stats"       : "📊 Статистика:\n👥 Пользователей: {u}\n📝 Тестов: {t}\n📈 Средний балл: {a}%",
        "not_admin"   : "❌ Вы не администратор.",
        "bcast_ok"    : "✅ Отправлено {n} пользователям.",
        "addq_help"   : "Добавление вопроса:\n\n/addq\nCAT:mikro\nTOPIC:1\nQ:Вопрос\nA:A\nB:B\nC:C\nD:D\nANS:0\nEXP:Пояснение",
        "addq_ok"     : "✅ Вопрос добавлен!",
        "addq_err"    : "❌ Неверный формат.",
        "all_mix"     : "🔀 Все вперемешку",
        "back_cat"    : "⬅️ Назад",
        "help"        : "📌 Команды:\n/start — Меню\n/top — Рейтинг\n/stats — Статистика\n/admin — Админ\n/feedback — Отзывы (admin)",
        # PDF
        "pdf_recv"    : "📄 PDF получен! AI составляет тест... ⏳ (30-60 секунд)",
        "pdf_no_text" : "❌ Не удалось прочитать текст из PDF.",
        "pdf_no_ai"   : "❌ AI сервис не настроен (GEMINI_API_KEY отсутствует). Обратитесь к администратору.",
        "pdf_fail"    : "❌ Ошибка при составлении теста. Попробуйте снова.",
        "pdf_done"    : "✅ Подготовлено {n} вопросов! Начинаем...",
        # Feedback
        "fb_ask"      : "📝 Ваше мнение о тесте?",
        # Timer/Pause
        "timer_msg"   : "⏱ Вопрос {i}/{n}  |  {bar}  {sec} сек",
        "paused_msg"  : "⏸ <b>Пауза</b>\n\n⏱ Осталось: <b>{sec} сек</b>\nНажмите кнопку для продолжения.",
        "btn_pause"   : "⏸ Пауза",
        "btn_resume"  : "▶️ Продолжить",
        "btn_stop"    : "🚫 Остановить тест",
        "stop_confirm": "✅ Тест остановлен.",
        "fb_thumb_q"  : "Тест был полезным?",
        "fb_star_q"   : "Сколько звёзд?",
        "fb_comment_q": "💬 Напишите комментарий (или /skip):",
        "fb_done"     : "✅ Спасибо за отзыв!",
        "fb_skip"     : "Понятно, в следующий раз! 👍",
        "btn_tests"   : "📝 Тесты",
        "btn_mikro"   : "📊 Микроэкономика",
        "btn_makro"   : "📈 Макроэкономика",
        "btn_pul"     : "🏦 Деньги и Банки",
        "btn_pdf"     : "📄 Тест из PDF",
        "btn_top"     : "🏆 Рейтинг",
        "btn_stats"   : "📊 Статистика",
        "btn_feedback": "💬 Отзывы",
        "btn_help"    : "ℹ️ Помощь",
    }
}

user_lang  = {}
user_state    = {}
feedback_state = {}   # uid -> step: 'thumb'|'star'|'comment'

def txt(uid, key, **kw):
    lang = user_lang.get(uid, "uz")
    s    = TX[lang].get(key, key)
    return s.format(**kw) if kw else s

# ── KATEGORIYALAR ─────────────────────────────────────────
CATEGORIES = {
    "mikro": {"emoji": "📊", "uz": "Mikroiqtisodiyot", "ru": "Микроэкономика",  "active": True},
    "makro": {"emoji": "📈", "uz": "Makroiqtisodiyot", "ru": "Макроэкономика",  "active": False},
    "pul"  : {"emoji": "🏦", "uz": "Pul va Bank",      "ru": "Деньги и Банки", "active": True},
}

# ── SAVOLLAR ──────────────────────────────────────────────
TOPICS = {
    "mikro_1": {
        "cat": "mikro",
        "uz" : "Ishlab chiqarish omillari bozori",
        "ru" : "Рынок факторов производства",
        "questions": [
            {"q":"Raqobatlashgan mehnat bozorida firmalar ishchi yollashni qachongacha davom ettiradi?","opts":["Ishchilar soni kamayguncha", "MRPL = ish haqi bo'lguncha", "Mehnatga taklif tugaguncha", "Ish haqi maksimal bo'lguncha"],"ans":1,"exp":"Firma MRPL ish haqiga teng bo'lguncha ishchi yollaydi."},
            {"q":"Mehnatga talab kim tomonidan shakllantiriladi?","opts":["Davlat", "Banklar", "Uy xo'jaliklari", "Firmalar"],"ans":3,"exp":"Mehnatga talab firmalar tomonidan shakllantiriladi."},
            {"q":"Mehnat bozori nimani ifodalaydi?","opts":["Ishchi kuchi xizmatlari bozori", "Valyuta bozori", "Kapital bozori", "Tovarlar almashinuvi"],"ans":0,"exp":"Mehnat bozori — ishchi kuchi xizmatlari sotiladi va sotib olinadigan bozor."},
            {"q":"Mehnatga taklif qaysi subyekt tomonidan shakllantiriladi?","opts":["Davlat", "Uy xo'jaliklari", "Firmalar", "Banklar"],"ans":1,"exp":"Mehnatga taklifni uy xo'jaliklari (ishchilar) shakllantiradi."},
            {"q":"Raqobatlashgan mehnat bozorida ish haqi nimaning natijasida belgilanadi?","opts":["Ish beruvchi xohishi", "Talab va taklif muvozanati", "Inflyatsiya", "Davlat qarori"],"ans":1,"exp":"Raqobatlashgan bozorda ish haqi talab va taklif muvozanati orqali belgilanadi."},
            {"q":"MRPL nimani bildiradi?","opts":["Mehnatning chekli daromadliligi", "Umumiy daromad", "Ish haqi", "Mehnatning o'rtacha mahsuloti"],"ans":0,"exp":"MRPL — Marginal Revenue Product of Labour — mehnatning chekli daromadliligi."},
            {"q":"MRPL qanday aniqlanadi?","opts":["MPL / P", "MPL x P", "MPL + P", "MPL - P"],"ans":1,"exp":"MRPL = MPL x P (chekli mahsulot x narx)."},
            {"q":"Firma foydasini maksimal qilish sharti:","opts":["MRPL = W", "MP = W", "MPL = W", "AP = W"],"ans":0,"exp":"Optimal ishchi soni: MRPL = W."},
            {"q":"Mehnat bozorida monopsoniya nimani anglatadi?","opts":["Bitta ish beruvchi", "Ko'p ishchi", "Ko'p ish beruvchi", "Davlat bozori"],"ans":0,"exp":"Monopsoniya — bozorda yagona ish beruvchi mavjud bo'lgan holat."},
            {"q":"Monopsoniyada ish haqi qanday bo'ladi?","opts":["Muvozanatdan past", "Muvozanatdan yuqori", "Nolga teng", "Muvozanatga teng"],"ans":0,"exp":"Monopsoniyada ish haqi muvozanat darajasidan past belgilanadi."},
            {"q":"Kapital bozorida foiz stavkasi nimani muvozanatlashtiradi?","opts":["Narxlar darajasi", "Ish haqi", "Inflyatsiya", "Kapitalga talab va taklifni"],"ans":3,"exp":"Foiz stavkasi kapital bozorida talab va taklifni muvozanatlashtiradigan narx."},
            {"q":"Asosiy kapitalga qaysi resurs kiradi?","opts":["Ish haqi", "Mashina-uskunalar", "Yoqilg'i", "Xom ashyo"],"ans":1,"exp":"Asosiy kapital — mashina-uskunalar, binolar, uzoq muddat xizmat qiladi."},
            {"q":"Aylanma kapitalning asosiy xususiyati nima?","opts":["Qayta tiklanmaydi", "Bir siklda to'liq sarflanadi", "Uzoq muddat xizmat qiladi", "Amortizatsiyalanadi"],"ans":1,"exp":"Aylanma kapital bir ishlab chiqarish siklida to'liq sarflanadi."},
            {"q":"Agar MPL = 4, narxi P = 25 bo'lsa, MRPL nechaga teng?","opts":["100", "4", "25", "21"],"ans":0,"exp":"MRPL = MPL x P = 4 x 25 = 100."},
            {"q":"Minimal ish haqi monopsoniya sharoitida qanday natija berishi mumkin?","opts":["Bandlik kamayadi", "Bandlik oshadi", "Ishsizlik ortadi", "Ta'sir qilmaydi"],"ans":1,"exp":"Monopsoniyada minimal ish haqi to'g'ri belgilansa, bandlik oshishi mumkin."},
            {"q":"Foiz stavkasi 10%, amortizatsiya 5%. Kapitalning foydalanuvchi xarajati?","opts":["20%", "5%", "15%", "10%"],"ans":2,"exp":"Foydalanuvchi xarajati = foiz stavkasi + amortizatsiya = 10% + 5% = 15%."},
            {"q":"Mehnat taklifi oshsa, ish haqi qanday o'zgaradi?","opts":["Pasayadi", "Nol bo'ladi", "O'zgarmaydi", "Oshadi"],"ans":0,"exp":"Taklif oshsa muvozanat narxi (ish haqi) pasayadi."},
            {"q":"Iqtisodiy renta qaysi omillarga tatbiq etiladi?","opts":["Faqat mehnatga", "Faqat kapitalga", "Faqat yerga", "Barcha cheklangan resurslarga"],"ans":3,"exp":"Iqtisodiy renta barcha taklifi cheklangan resurslarga tatbiq etiladi."},
            {"q":"Yuqori malakali ishchi ish haqining bir qismi nima sababdan renta hisoblanadi?","opts":["Davlat belgilaydi", "Talab past", "Malaka noyob", "Mehnat ortiqcha"],"ans":2,"exp":"Noyob malaka taklifini cheklab qo'yadi — bu rentaning asosiy sababi."},
            {"q":"Monopsoniyada bandlik darajasi raqobatnikiga nisbatan:","opts":["Yuqori", "Past", "Teng", "Maksimal"],"ans":1,"exp":"Monopsonist ME = MRP qoidasida kamroq ishchi yollaydi — bandlik past."},
            {"q":"Mehnat bozorida muvozanat nimani bildiradi?","opts":["Ish haqi nol", "Talab va taklif teng", "Bandlik maksimal", "Ishchilar ko'p"],"ans":1,"exp":"Muvozanat — mehnatga talab va taklif teng bo'lgan holat."},
            {"q":"Iqtisodiy renta qachon yuzaga keladi?","opts":["Mehnat taklifi cheklanganda", "Davlat aralashganda", "Inflyatsiyada", "Ishsizlikda"],"ans":0,"exp":"Iqtisodiy renta taklif cheklangan omillarda yuzaga keladi."},
            {"q":"MRPL = MPL x P formulasi qaysi sharoitda amal qiladi?","opts":["Monopsoniyada", "Davlat bozorida", "Raqobatlashgan mahsulot bozorida", "Monopol bozorida"],"ans":2,"exp":"MRPL = MPL x P faqat raqobatlashgan mahsulot bozorida amal qiladi."},
            {"q":"Ishlab chiqarish omillari bozori tahlilining asosiy maqsadi?","opts":["Resurslardan optimal foydalanishni aniqlash", "Foydani nolga tenglashtirish", "Narxlarni pasaytirish", "Soliqni oshirish"],"ans":0,"exp":"Resurslardan samarali va optimal foydalanishni o'rgatadi."},
            {"q":"Iqtisodiy renta tushunchasi qaysi nazariyaga asoslanadi?","opts":["Monetarizm", "Klassik iqtisodiyot", "Keyneschilik", "Institutsionalizm"],"ans":1,"exp":"Renta nazariyasi klassik iqtisodiyot (D. Rikardo) doirasida ishlab chiqilgan."},
        ]
    },
    "mikro_2": {
        "cat": "mikro",
        "uz" : "Umumiy muvozanat va samaradorlik",
        "ru" : "Общее равновесие и эффективность",
        "questions": [
            {"q":"Umumiy muvozanat nimani anglatadi?","opts":["Barcha bozorlar bir vaqtning o'zida muvozanatga kelgan holatni", "Faqat ishlab chiqarish samaradorligini", "Faqat bitta bozorda narx muvozanatini", "Davlat tomonidan belgilangan narxlar tizimini"],"ans":0,"exp":"Umumiy muvozanat — barcha bozorlar bir vaqtning o'zida muvozanatga kelgan holat."},
            {"q":"Pareto samarali holat qachon yuzaga keladi?","opts":["Davlat aralashuvi bo'lganda", "Hech kimni yomonlashtirmasdan birovni yaxshilab bo'lmaganda", "Resurslar teng taqsimlanganda", "Kimningdir foydasi oshsa"],"ans":1,"exp":"Pareto samaradorligi: hech kimni yomonlashtirmasdan birovning holatini yaxshilab bo'lmaydi."},
            {"q":"Edgeworth qutisi nimani ko'rsatadi?","opts":["Barcha mumkin bo'lgan taqsimotlarni", "Soliq ta'sirini", "Ishlab chiqarish xarajatlarini", "Faqat muvozanat narxini"],"ans":0,"exp":"Edgeworth qutisi ikkita iste'molchi o'rtasidagi barcha mumkin bo'lgan taqsimotlarni ko'rsatadi."},
            {"q":"Shartnoma egri chizig'i nimani ifodalaydi?","opts":["Narxlar nisbatini", "Barcha adolatli taqsimotlarni", "Davlat aralashuvi yo'llarini", "Barcha Pareto samarali taqsimotlarni"],"ans":3,"exp":"Shartnoma (contract) egri chizig'i — barcha Pareto samarali taqsimotlar to'plami."},
            {"q":"Iste'molda samaradorlik sharti:","opts":["MRT = MRS", "MRSa = MRSb", "MC = MR", "P = AC"],"ans":1,"exp":"Iste'molda samaradorlik: ikkala iste'molchining MRS lari teng bo'lishi kerak."},
            {"q":"Ishlab chiqarishda samaradorlik sharti:","opts":["MC = P", "MRS = MRT", "AC = MC", "MRTS1 = MRTS2"],"ans":3,"exp":"Ishlab chiqarish samaradorligi sharti: barcha firmalar uchun MRTS lar teng bo'lishi kerak."},
            {"q":"Mahsulot (output) samaradorligi nimani talab qiladi?","opts":["MRS = MRT", "TR = TC", "MC = AC", "MRS = MRTS"],"ans":0,"exp":"Mahsulot samaradorligi sharti: MRS = MRT."},
            {"q":"Raqobatli muvozanat nimani ta'minlaydi?","opts":["Faqat adolatlilikni", "Faqat samaradorlikni", "Samaradorlikni, lekin adolatlilikni emas", "Teng daromadni"],"ans":2,"exp":"Raqobatli muvozanat samaradorlikni ta'minlaydi, lekin adolatli taqsimotni kafolatlamaydi."},
            {"q":"UPF nimani ko'rsatadi?","opts":["Iste'molchilar foydalilik kombinatsiyalarini", "Soliq tushumlarini", "Ishlab chiqarish imkoniyatlarini", "Narxlar harakatini"],"ans":0,"exp":"UPF — iste'molchilar foydalilik kombinatsiyalarini ko'rsatadi."},
            {"q":"PPF ichidagi nuqtalar nimani bildiradi?","opts":["Samarali ishlab chiqarish", "Resurslardan to'liq foydalanilmagan holat", "Imkonsiz holat", "Muvozanat"],"ans":1,"exp":"PPF ichidagi nuqtalar resurslardan to'liq foydalanilmagan holatni bildiradi."},
            {"q":"Pareto mezonining asosiy cheklovi?","opts":["Tenglikni hisobga olmaydi", "Bozorni inkor qiladi", "Texnologiyani hisobga olmaydi", "Samaradorlikni o'lchay olmaydi"],"ans":0,"exp":"Pareto mezoni samaradorlikni o'lchaydi, lekin taqsimot tengligini hisobga olmaydi."},
            {"q":"Birinchi farovonlik teoremasi:","opts":["Har qanday Pareto samarali holat raqobatli", "Har qanday raqobatli muvozanat Pareto samarali", "Davlat har doim samarali", "Tenglik avtomatik yuzaga keladi"],"ans":1,"exp":"1-farovonlik teoremasi: har qanday raqobatli muvozanat Pareto samarali bo'ladi."},
            {"q":"Ikkinchi farovonlik teoremasi:","opts":["Davlat samaradorlikni buzadi", "Raqobat tenglik beradi", "Har qanday Pareto samarali holatni raqobatli muvozanatga aylantirish mumkin", "Narxlar ahamiyatsiz"],"ans":2,"exp":"2-farovonlik teoremasi: istalgan Pareto samarali holatga qayta taqsimlash orqali erishish mumkin."},
            {"q":"Adolatlilik nimaga asoslanadi?","opts":["Texnologiyaga", "Iqtisodiy qonunlarga", "Bozor signallariga", "Ijtimoiy va normativ baholarga"],"ans":3,"exp":"Adolatlilik — normativ tushuncha bo'lib, ijtimoiy qadriyatlar va normativ baholarga asoslanadi."},
            {"q":"Qisman muvozanat tahlilining asosiy farazi:","opts":["Narxlar qat'iy belgilanadi", "Davlat aralashuvi mavjud", "Boshqa bozorlar o'zgarmas deb olinadi", "Barcha bozorlar o'zgaradi"],"ans":2,"exp":"Qisman muvozanat tahlilida boshqa bozorlar o'zgarmas (ceteris paribus) deb olinadi."},
            {"q":"Nima uchun samarali taqsimot adolatli bo'lmasligi mumkin?","opts":["Soliq yo'q", "Resurslar teng emas", "Narxlar noto'g'ri", "Pareto mezoni tenglikni talab qilmaydi"],"ans":3,"exp":"Pareto mezoni faqat samaradorlikni o'lchaydi, tenglikni talab qilmaydi."},
            {"q":"Umumiy muvozanat tahliliga xos xususiyat:","opts":["Bitta bozorni tahlil qilish", "Feedback ta'sirlarni hisobga olish", "Ceteris paribus farazi", "Qat'iy narxlar"],"ans":1,"exp":"Umumiy muvozanat tahlili bozorlar orasidagi o'zaro ta'sir va feedback effektlarni hisobga oladi."},
            {"q":"O'zbekiston sharoitida subsidiyalar nimani buzishi mumkin?","opts":["Ishlab chiqarishni", "Samaradorlikni", "Texnologiyani", "Adolatlilikni"],"ans":1,"exp":"Subsidiyalar narx signallarini buzib, resurslardan samarasiz foydalanishga olib kelishi mumkin."},
            {"q":"Qaysi holatda umumiy muvozanatga erishilmaydi?","opts":["Raqobat mavjud bo'lsa", "Narxlar erkin bo'lsa", "Narxlar qat'iy belgilansa", "MRS = MRTS = MRT"],"ans":2,"exp":"Narxlar qat'iy belgilanganda bozor mexanizmi ishlamaydi."},
            {"q":"Umumiy muvozanatning eng asosiy afzalligi:","opts":["Real iqtisodiy tizimni to'liq aks ettiradi", "Hisoblash oson", "Davlat uchun qulay", "Faqat nazariy"],"ans":0,"exp":"Umumiy muvozanat tahlili barcha bozorlar o'rtasidagi o'zaro bog'liqlikni hisobga oladi."},
        ]
    },
    "mikro_3": {
        "cat": "mikro",
        "uz" : "Monopoliya va monopsoniya",
        "ru" : "Монополия и монопсония",
        "questions": [
            {"q":"Agar talab elastikligi Ed = -4 bo'lsa, Lerner indeksi L nechaga teng?","opts":["-0.25", "0.25", "0", "4"],"ans":1,"exp":"L = 1/|Ed| = 1/4 = 0.25"},
            {"q":"Talab: Q = 200 - 2P. MC = 20. Optimal ishlab chiqarish hajmi?","opts":["100", "60", "80", "40"],"ans":2,"exp":"P = 100 - Q/2, MR = 100 - Q. MR=MC: 100-Q=20, Q=80."},
            {"q":"3 ta firma ulushlari: 50%, 30%, 20%. HHI?","opts":["2500", "10000", "3800", "5000"],"ans":2,"exp":"HHI = 50^2 + 30^2 + 20^2 = 2500+900+400 = 3800."},
            {"q":"Agar monopolist MR < MC bo'lsa u nima qiladi?","opts":["Ishlab chiqarishni kamaytiradi", "Ishlab chiqarishni oshiradi", "O'zgartirmaydi", "Narxni oshiradi"],"ans":0,"exp":"MR < MC bo'lsa, qo'shimcha ishlab chiqarish zararli — hajm kamaytiriladi."},
            {"q":"Monopsoniyada optimal shart:","opts":["W = MRP", "MR = MC", "W = ME", "MRP = ME"],"ans":3,"exp":"Monopsoniyada optimal: MRP = ME."},
            {"q":"Agar P = 120 va MC = 60 bo'lsa, Lerner indeksi?","opts":["2", "1", "0.5", "0"],"ans":2,"exp":"L = (P - MC)/P = (120 - 60)/120 = 0.5"},
            {"q":"HHI = 10000 nimani bildiradi?","opts":["Past konsentratsiya", "Oligopoliya", "Sof monopoliya", "Mukammal raqobat"],"ans":2,"exp":"HHI = 10000 — faqat bitta firma mavjud, ya'ni sof monopoliya."},
            {"q":"Monopolist talabning qaysi qismida ishlaydi?","opts":["Noelastik", "Vertikal", "Elastik", "Birlik elastik"],"ans":2,"exp":"Monopolist faqat elastik qismda ishlaydi, chunki noelastik qismda MR < 0."},
            {"q":"Sof monopoliyada narx:","opts":["MC ga teng", "MC dan yuqori", "MR ga teng", "ATC dan kichik"],"ans":1,"exp":"Monopoliyada P > MC — narx chekli xarajatdan yuqori belgilanadi."},
            {"q":"MR = MC sharti nimani beradi?","opts":["Nol foyda", "Maksimal TR", "Maksimal foyda", "Minimal AC"],"ans":2,"exp":"MR = MC — foyda maksimallashtirilishi sharti."},
            {"q":"Lerner indeksi 0 bo'lsa:","opts":["Sof monopoliya", "Monopsoniya", "Mukammal raqobat", "Oligopoliya"],"ans":2,"exp":"L = 0 bo'lsa P = MC — mukammal raqobat bozori."},
            {"q":"Deadweight loss (DWL) sababi?","opts":["P = MC", "Q optimal", "Ishlab chiqarish ko'p", "P > MC"],"ans":3,"exp":"Monopoliyada P > MC bo'lgani uchun ishlab chiqarish optimaldan kam — DWL yuzaga keladi."},
            {"q":"Monopolistning |Ed| = 3 bo'lsa, narx MC dan necha foiz yuqori?","opts":["33%", "50%", "75%", "25%"],"ans":0,"exp":"L = 1/|Ed| = 1/3 = 33%."},
            {"q":"Monopsoniyada W = 10 + L bo'lsa, ME nimaga teng?","opts":["20 + L", "L", "10 + 2L", "10 + L"],"ans":2,"exp":"TC = W*L = (10+L)*L. ME = d(TC)/dL = 10 + 2L."},
            {"q":"Monopsoniyada bandlik darajasi raqobatnikiga nisbatan:","opts":["Maksimal", "Yuqori", "Teng", "Past"],"ans":3,"exp":"Monopsonist ME = MRP qoidasida kamroq ishchi yollaydi — bandlik past."},
            {"q":"Tabiiy monopoliya sababi:","opts":["Masshtab samarasi", "Kartel", "Import", "Patent"],"ans":0,"exp":"Tabiiy monopoliya — katta masshtab samarasi sababli bir firma samaraliroq ishlashi."},
            {"q":"Monopolist TR maksimal bo'ladigan nuqta:","opts":["MC minimum", "P = MC", "MR = MC", "MR = 0"],"ans":3,"exp":"TR maksimal nuqtada MR = 0 bo'ladi."},
            {"q":"Qisqa muddatda P < AVC bo'lsa:","opts":["Ishlab chiqarishni to'xtatadi", "Subsidiyalaydi", "Ishlab chiqaradi", "Narxni oshiradi"],"ans":0,"exp":"P < AVC bo'lsa, o'zgaruvchan xarajatlar ham qoplanmaydi — to'xtatish maqsadga muvofiq."},
            {"q":"50% va 50% duopoliya HHI:","opts":["2500", "5000", "2000", "10000"],"ans":1,"exp":"HHI = 50^2 + 50^2 = 5000."},
            {"q":"Monopsoniyada minimal ish haqi joriy qilinsa (raqobat darajasida):","opts":["Monopsoniya yo'qoladi", "Bandlik kamayadi", "Bandlik o'zgarmaydi", "Bandlik oshadi"],"ans":3,"exp":"Monopsoniyada minimal ish haqi to'g'ri belgilansa, bandlik raqobat darajasiga ko'tariladi."},
        ]
    },
    "mikro_4": {
        "cat": "mikro",
        "uz" : "Monopoliyada narxlar strategiyasi",
        "ru" : "Ценовая стратегия монополии",
        "questions": [
            {"q":"1-darajali diskriminatsiyada ishlab chiqarish hajmi:","opts":["MR = 0", "P = MC", "MR = MC", "ATC minimum"],"ans":1,"exp":"1-daraja diskriminatsiyada har bir birlik WTP ga sotiladi, optimal Q: P = MC."},
            {"q":"Mukammal diskriminatsiyada iste'molchi ortiqchaligi:","opts":["Nolga teng bo'ladi", "Yarimga kamayadi", "Maksimal bo'ladi", "MC ga teng bo'ladi"],"ans":0,"exp":"Mukammal diskriminatsiyada monopolist barcha iste'molchi ortiqchasini oladi."},
            {"q":"Talab: P = 200 - Q, MC = 20. Mukammal diskriminatsiyada foyda?","opts":["18000", "16200", "9000", "8100"],"ans":1,"exp":"Q* = 180. Foyda = 1/2 * 180 * 180 = 16200."},
            {"q":"2-darajali diskriminatsiya nimaga asoslanadi?","opts":["Daromadga", "Yoshga", "Hududga", "Hajmga"],"ans":3,"exp":"2-daraja diskriminatsiya sotib olinadigan miqdor (hajm) ga qarab turli narxlar belgilashga asoslanadi."},
            {"q":"3-darajali diskriminatsiyada optimal shart:","opts":["MR1 = MR2 = MC", "P1 = P2", "MC1 = MC2", "TR max"],"ans":0,"exp":"3-daraja diskriminatsiyada optimal: barcha segmentlarda MR MC ga teng bo'lishi kerak."},
            {"q":"Qaysi segmentda narx yuqori belgilanadi?","opts":["MC past", "Noelastik", "Q katta", "Elastik"],"ans":1,"exp":"Talab noelastik bo'lgan segmentda narx yuqori belgilanadi."},
            {"q":"Agar |Ed1| = 2 va |Ed2| = 4 bo'lsa, qaysi segmentda narx yuqori?","opts":["2-segment", "Aniqlab bo'lmaydi", "1-segment", "Teng"],"ans":2,"exp":"L=1/|Ed|. 1-segment: L=0.5 → narx yuqori."},
            {"q":"1-darajali diskriminatsiyada DWL:","opts":["Maksimal", "Yarim monopol", "Mavjud", "Nol"],"ans":3,"exp":"Mukammal diskriminatsiyada Q = Qraqobat bo'ladi — DWL yo'q."},
            {"q":"3-darajali diskriminatsiya umumiy foydani:","opts":["Nolga tushiradi", "Kamaytiradi", "MC ga teng", "Oshiradi"],"ans":3,"exp":"Segmentlash va farqlangan narx belgilash foydani oshiradi."},
            {"q":"2-qismli tarifda optimal T:","opts":["MC", "Minimal", "Nol", "Iste'molchi ortiqchaligiga teng"],"ans":3,"exp":"Optimal kirish to'lovi T = CS (iste'molchi ortiqchaligi) ga teng belgilanadi."},
            {"q":"Ikki qismli tarifda agar P = MC bo'lsa:","opts":["TR nol", "Zarar", "Foyda faqat T dan", "Foyda nol"],"ans":2,"exp":"P = MC bo'lsa savdo foydasi nol, lekin kirish to'lovi T dan foyda olinadi."},
            {"q":"Agar qayta sotish erkin bo'lsa:","opts":["Narxlar tenglashadi", "MC o'zgaradi", "P oshadi", "Diskriminatsiya mumkin"],"ans":0,"exp":"Qayta sotish erkin bo'lsa narxlar tenglashadi — diskriminatsiya buziladi."},
            {"q":"3-darajali diskriminatsiyada umumiy Q:","opts":["Monopol Q dan katta", "Monopol Q ga teng", "Nol", "Monopol Q dan kichik"],"ans":0,"exp":"Diskriminatsiya bilan umumiy Q yagona monopol Q dan ko'proq bo'ladi."},
            {"q":"Mukammal diskriminatsiyaning asosiy sharti:","opts":["Ko'p firma bo'lishi", "Har xaridor WTP ni bilish", "Qayta sotish mumkin bo'lishi", "Elastiklik bir xil bo'lishi"],"ans":1,"exp":"Mukammal diskriminatsiya uchun monopolist har bir xaridorning WTP ni bilishi zarur."},
            {"q":"Ikki qismli tarif optimal tanlovi:","opts":["P va T birgalikda optimallashtiriladi", "Faqat P", "MC", "Faqat T"],"ans":0,"exp":"Optimal 2 qismli tarifda P va T bir vaqtda optimallashtiriladi."},
        ]
    },
    "mikro_yakuniy": {
        "cat": "mikro",
        "uz" : "Yakuniy test (261 savol)",
        "ru" : "Итоговый тест (261 вопрос)",
        "questions": [
            {"q":"1-darajali narx diskriminatsiyasida ishlab chiqarish hajmi qaysi nuqtada aniqlanadi?","opts":["TR maksimum nuqtasida", "MR = 0 nuqtasida", "AC = MC nuqtasida", "P = MC nuqtasida"],"ans":3,"exp":"To'g'ri javob: B) P = MC nuqtasida"},
            {"q":"Mukammal narxlar diskriminatsiyasi sharoitida iste'molchi ortiqchaligi qanday bo'ladi?","opts":["Maksimal darajada oshadi", "Nolga teng bo'ladi", "O'zgarmaydi", "Ikki barobarga oshadi"],"ans":1,"exp":"To'g'ri javob: C) Nolga teng bo'ladi"},
            {"q":"Talab: P=200-Q, MC=20. Mukammal narx diskriminatsiyasida firma foydasi?","opts":["3 600", "18 000", "12 000", "16 200"],"ans":3,"exp":"To'g'ri javob: C) 16 200"},
            {"q":"Mukammal narxlar diskriminatsiyasining asosiy sharti qaysi?","opts":["Faqat ikkita bozor segmenti", "MC = 0 bo'lishi", "Bir xil narx barcha xaridorlarga", "Rezervatsiya narxida sotish va qayta sotish imkonsizligi"],"ans":3,"exp":"To'g'ri javob: B) Rezervatsiya narxida sotish va qayta sotish imkonsizligi"},
            {"q":"2-darajali narx diskriminatsiya nimaga asoslanadi?","opts":["Xaridorning yoshiga", "Sotib olingan tovar miqdori (hajmi)ga", "Xaridorning daromadiga", "Geografik joylashuvga"],"ans":1,"exp":"To'g'ri javob: C) Sotib olingan tovar miqdori (hajmi)ga"},
            {"q":"3-darajali narx diskriminatsiyasida optimal shart qaysi?","opts":["MR1 = MR2 = MC", "Q1 = Q2", "P1 = P2", "TR1 = TR2"],"ans":0,"exp":"To'g'ri javob: B) MR1 = MR2 = MC"},
            {"q":"3-darajali narx diskriminatsiyasida qaysi segmentda narx yuqori belgilanadi?","opts":["Xaridorlar ko'p bo'lgan segmentda", "Talab elastik bo'lgan segmentda", "Talab noelastik bo'lgan segmentda", "Daromad yuqori bo'lgan segmentda"],"ans":2,"exp":"To'g'ri javob: C) Talab noelastik bo'lgan segmentda"},
            {"q":"1-darajali narx diskriminatsiyasida sof jamiyat yo'qotishi (DWL) qanday?","opts":["Monopol DWL ga teng", "Iste'molchi ortiqchasiga teng", "Nolga teng", "Maksimal"],"ans":2,"exp":"To'g'ri javob: C) Nolga teng"},
            {"q":"3-darajali diskriminatsiya umumiy foydani qanday o'zgartiradi?","opts":["Nolga tushiradi", "Oshiradi", "Kamaytiradi", "O'zgartirmaydi"],"ans":1,"exp":"To'g'ri javob: C) Oshiradi"},
            {"q":"3-darajali narx diskriminatsiyasida umumiy ishlab chiqarish hajmi (Q)?","opts":["Q = Q1 + Q2", "Q = Q1 - Q2", "Q = Q1 / Q2", "Q = Q1 x Q2"],"ans":0,"exp":"To'g'ri javob: C) Q = Q1 + Q2"},
            {"q":"Monopolist uchun Q=200-2P, MC=20. Optimal ishlab chiqarish hajmi (Q*)?","opts":["100", "40", "80", "60"],"ans":2,"exp":"To'g'ri javob: C) 80"},
            {"q":"Agar monopolist uchun MR < MC bo'lsa, firma ishlab chiqarish hajmini qanday o'zgartiradi?","opts":["Ikki barobarga oshiradi", "O'zgartirmaydi", "Kamaytiradi", "Oshiradi"],"ans":2,"exp":"To'g'ri javob: B) Kamaytiradi"},
            {"q":"Tabiiy monopoliyaning asosiy iqtisodiy sababi nima?","opts":["Xomashyoga monopol egalik", "Miqyos samarasi — AC doimo pasayib boradi", "Davlat himoyasi", "Patent huquqi"],"ans":1,"exp":"To'g'ri javob: B) Miqyos samarasi — AC doimo pasayib boradi"},
            {"q":"Patent asosida vujudga keladigan monopoliya qaysi turga kiradi?","opts":["Tabiiy monopoliya", "Huquqiy (yuridik) monopoliya", "Texnologik monopoliya", "Sun'iy monopoliya"],"ans":1,"exp":"To'g'ri javob: C) Huquqiy (yuridik) monopoliya"},
            {"q":"Monopoliyaning qanday turlari bor?","opts":["Real va nominal", "Qisqa va uzoq muddatli", "Ichki va tashqi", "Tabiiy, huquqiy va sun'iy monopoliya"],"ans":3,"exp":"To'g'ri javob: B) Tabiiy, huquqiy va sun'iy monopoliya"},
            {"q":"Sof monopoliya bozorida narx va MC o'rtasidagi munosabat?","opts":["P > MC", "P = MC", "P < MC", "P = 0"],"ans":0,"exp":"To'g'ri javob: C) P > MC"},
            {"q":"Monopolist ishlab chiqarishni optimal Q* dan oshirsa qanday holat yuzaga keladi?","opts":["MR < MC bo'lib, foyda kamayadi", "Foyda o'zgarmaydi", "MR > MC bo'lib, foyda oshadi", "Foyda oshadi"],"ans":0,"exp":"To'g'ri javob: C) MR < MC bo'lib, foyda kamayadi"},
            {"q":"Foydani maksimallashtirish sharti qaysi?","opts":["MR = MC", "MR = 0", "P = AC", "TR = TC"],"ans":0,"exp":"To'g'ri javob: B) MR = MC"},
            {"q":"Agar MR > MC bo'lsa, monopolist nima qiladi?","opts":["Firmani yopadi", "Narxni oshiradi", "Ishlab chiqarishni kamaytiradi", "Ishlab chiqarishni oshiradi"],"ans":3,"exp":"To'g'ri javob: C) Ishlab chiqarishni oshiradi"},
            {"q":"MR < 0 bo'lgan talab qismida ishlab chiqarish qanday baholanadi?","opts":["Foydali", "Samarasiz — monopolist bu qismda ishlab chiqarmaydi", "Zarur", "Optimal"],"ans":1,"exp":"To'g'ri javob: B) Samarasiz — monopolist bu qismda ishlab chiqarmaydi"},
            {"q":"|Ep| > 1 bo'lsa, MR qanday bo'ladi?","opts":["MR = P", "MR = 0", "MR < 0", "MR > 0"],"ans":3,"exp":"To'g'ri javob: C) MR > 0"},
            {"q":"Elastiklik |E|=1 nuqtasida MR nechchiga teng?","opts":["0", "-1", "Cheksiz", "1"],"ans":0,"exp":"To'g'ri javob: B) 0"},
            {"q":"Agar MC oshsa, optimal Q qanday o'zgaradi?","opts":["O'zgarmaydi", "Oshadi", "Ikki barobara oshadi", "Kamayadi"],"ans":3,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"Tabiiy monopoliyada adolatli narx (P=AC) belgilansa firma qanday foyda oladi?","opts":["Normal foyda (nol iqtisodiy foyda)", "Maksimal foyda", "Zarar ko'radi", "Monopol foyda"],"ans":0,"exp":"To'g'ri javob: C) Normal foyda (nol iqtisodiy foyda)"},
            {"q":"Agar P1=AC va Q1 < Qe bo'lsa, firma qanday foyda oladi?","opts":["Normal foyda (nol iqtisodiy foyda)", "Monopol foyda", "Zarar ko'radi", "Maksimal foyda"],"ans":0,"exp":"To'g'ri javob: B) Normal foyda (nol iqtisodiy foyda)"},
            {"q":"Monopolist MR=MC da ishlab chiqaradi. MR > MC bo'lsa:","opts":["Narxni tushirishi kerak", "Monopolist ishlab chiqarishni oshirishi kerak", "Kamaytirishi kerak", "O'zgartirmasligi kerak"],"ans":1,"exp":"To'g'ri javob: A) Monopolist ishlab chiqarishni oshirishi kerak"},
            {"q":"Mukammal narx diskriminatsiyasida MR nimaga teng?","opts":["MFC ga", "Nolga", "MC ga", "P (talab chizig'i)ga"],"ans":3,"exp":"To'g'ri javob: C) P (talab chizig'i)ga"},
            {"q":"Ep=-4, MC=50. Monopol narx?","opts":["66.67", "50", "60", "75"],"ans":0,"exp":"To'g'ri javob: C) 66.67"},
            {"q":"Monopol 'o'lik yuk' (DWL) nimani bildiradi?","opts":["Ishlab chiqarish xarajatlari", "Iste'molchi ortiqchaligi", "Monopol sababli yo'qolgan jamiyat farovonligi", "Monopol foyda"],"ans":2,"exp":"To'g'ri javob: C) Monopol sababli yo'qolgan jamiyat farovonligi"},
            {"q":"Monopol narx va raqobatlashgan bozordagi narxlarning farqi nimani ko'rsatadi?","opts":["Monopol hokimiyat darajasi va monopol rentani", "Ishlab chiqarish hajmini", "Iste'molchi ortiqchaligini", "DWL ni"],"ans":0,"exp":"To'g'ri javob: B) Monopol hokimiyat darajasi va monopol rentani"},
            {"q":"Monopolist narxni MC dan yuqori belgilasa, jamiyat yo'qotishi nimada ifodalanadi?","opts":["Ishlab chiqarish xarajatida", "Iste'molchi ortiqchaligida", "Monopol foydada", "O'lik yo'qotish (DWL) uchburchak maydonida"],"ans":3,"exp":"To'g'ri javob: C) O'lik yo'qotish (DWL) uchburchak maydonida"},
            {"q":"Tabiiy monopoliyada adolatli narx qanday aniqlanadi?","opts":["P = MR", "P = AVC", "P = AC", "P = MC"],"ans":2,"exp":"To'g'ri javob: C) P = AC"},
            {"q":"Lerner indeksi formulasi qaysi?","opts":["L = (P-MC)/P", "L = (TR-TC)/P", "L = MC/P", "L = MR/P"],"ans":0,"exp":"To'g'ri javob: B) L = (P-MC)/P"},
            {"q":"P=80, MC=60. Lerner indeksi?","opts":["0.20", "0.25", "0.50", "0.10"],"ans":1,"exp":"To'g'ri javob: C) 0.25"},
            {"q":"Monopol narx MC dan 2 barobara katta. Lerner ko'rsatkichi?","opts":["0.75", "1.00", "0.50", "0.25"],"ans":2,"exp":"To'g'ri javob: B) 0.50"},
            {"q":"Monopol narx MC dan 4 barobara katta. Lerner ko'rsatkichi?","opts":["0.50", "0.75", "0.25", "1.00"],"ans":1,"exp":"To'g'ri javob: C) 0.75"},
            {"q":"Lerner indeksi nolga teng bo'lishi qaysi bozorda kuzatiladi?","opts":["Mukammal raqobat", "Monopoliya", "Oligopoliya", "Monopolistik raqobat"],"ans":0,"exp":"To'g'ri javob: D) Mukammal raqobat"},
            {"q":"Lerner ko'rsatkichi 1 ga teng bo'lishi uchun MC nechchiga teng bo'lishi kerak?","opts":["P/2", "0", "1", "P"],"ans":1,"exp":"To'g'ri javob: D) 0"},
            {"q":"Talabning narx bo'yicha elastikligi ortdi. Lerner indeksi qanday o'zgaradi?","opts":["Ikki barobarga oshadi", "Kamayadi", "O'zgarmaydi", "Oshadi"],"ans":1,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"Elastiklik cheksizga intilsa, quyidagilardan qaysi biri o'rinli?","opts":["MR > 0", "P < MC", "P > MC, L = 1", "P = MC, L = 0"],"ans":3,"exp":"To'g'ri javob: B) P = MC, L = 0"},
            {"q":"Lerner ko'rsatkichi qanday sharoitda yuqori bo'ladi?","opts":["Firmalar ko'p", "Elastiklik yuqori, raqobat kuchli", "MC = P bo'lganda", "Talab noelastik, kirish to'siqlari kuchli, o'rnini bosuvchi tovar kam"],"ans":3,"exp":"To'g'ri javob: B) Talab noelastik, kirish to'siqlari kuchli, o'rnini bosuvchi tovar kam"},
            {"q":"Amaliyotda Lerner ko'rsatkichida MC o'rniga qaysi xarajat ishlatiladi?","opts":["FC", "TC", "AC yoki AVC", "VC"],"ans":2,"exp":"To'g'ri javob: C) AC yoki AVC"},
            {"q":"HHI = 10000 bo'lsa, bozorda qanday holat?","opts":["Oligopoliya", "Monopolistik raqobat", "Sof raqobat", "Sof monopoliya"],"ans":3,"exp":"To'g'ri javob: D) Sof monopoliya"},
            {"q":"Duopoliya: 2 ta teng ulushli firma. HHI?","opts":["4000", "10000", "2500", "5000"],"ans":3,"exp":"To'g'ri javob: C) 5000"},
            {"q":"Oligopoliya: 4 ta teng ulushli firma. HHI?","opts":["2500", "2000", "1250", "4000"],"ans":0,"exp":"To'g'ri javob: C) 2500"},
            {"q":"Ulushlar: 50%, 30%, 20%. HHI?","opts":["3800", "4000", "3200", "3600"],"ans":0,"exp":"To'g'ri javob: C) 3800"},
            {"q":"Sof monopoliyada HHI?","opts":["10000", "5000", "7500", "9000"],"ans":0,"exp":"To'g'ri javob: D) 10000"},
            {"q":"HHI=9000 bo'lsa, bozor qanday?","opts":["Sof raqobat", "Yuqori konsentratsiyali (monopoliyaga yaqin)", "Past konsentratsiyali", "O'rtacha konsentratsiyali"],"ans":1,"exp":"To'g'ri javob: C) Yuqori konsentratsiyali (monopoliyaga yaqin)"},
            {"q":"Firmaning bozordagi ulushi ortsa, odatda HHI qanday o'zgaradi?","opts":["Kamayadi", "Ortadi", "O'zgarmaydi", "Nolga tushadi"],"ans":1,"exp":"To'g'ri javob: C) Ortadi"},
            {"q":"E1=-3, E2=-6. Qaysi segmentda narx yuqoriroq?","opts":["Aniqlab bo'lmaydi", "1-segmentda", "Ikkisi teng", "2-segmentda"],"ans":1,"exp":"To'g'ri javob: C) 1-segmentda"},
            {"q":"MR1 > MR2 bo'lsa, firma qanday qaror qiladi?","opts":["2-bozorga ko'proq tovar yo'naltiradi", "Teng taqsimlaydi", "1-bozorga ko'proq tovar yo'naltiradi", "Ishlab chiqarishni kamaytiradi"],"ans":2,"exp":"To'g'ri javob: C) 1-bozorga ko'proq tovar yo'naltiradi"},
            {"q":"Ikki segmentli bozor uchun optimallik sharti?","opts":["Q1 = Q2", "MR1 = MR2 = MC", "TR1 = TR2", "P1 = P2 = MC"],"ans":1,"exp":"To'g'ri javob: B) MR1 = MR2 = MC"},
            {"q":"Qk+Qb=56000, Qk=36000. Qb=?","opts":["10000", "25000", "20000", "15000"],"ans":2,"exp":"To'g'ri javob: C) 20000"},
            {"q":"P=10-Q/8000. Q=36000 bo'lsa, P=?","opts":["5.0", "4.5", "5.5", "4.0"],"ans":2,"exp":"To'g'ri javob: D) 5.5"},
            {"q":"Narx diskriminatsiyasi uchun zarur shart qaysi?","opts":["Raqobatlashgan bozor", "Bozorlarni ajratish + elastiklik farqi + monopol kuch", "Faqat 2 ta xaridor", "Davlat ruxsati"],"ans":1,"exp":"To'g'ri javob: B) Bozorlarni ajratish + elastiklik farqi + monopol kuch"},
            {"q":"Narx diskriminatsiyasi natijasida umumiy farovonlik?","opts":["1-darajali diskriminatsiyada DWL=0, samaradorlik oshadi", "Doimo kamayadi", "O'zgarmaydi", "Doimo oshadi"],"ans":0,"exp":"To'g'ri javob: B) 1-darajali diskriminatsiyada DWL=0, samaradorlik oshadi"},
            {"q":"Qm < Qe bo'lishi nimani bildiradi?","opts":["Monopol hajm raqobatlashgan hajmdan kam — DWL mavjud", "Monopoliya samaraliroq", "Raqobat zaif", "Taklif ko'p"],"ans":0,"exp":"To'g'ri javob: B) Monopol hajm raqobatlashgan hajmdan kam — DWL mavjud"},
            {"q":"Qd = MR bo'lishi qachon yuz beradi?","opts":["Monopsoniyada", "3-darajali diskriminatsiyada", "Oligopoliyada", "1-darajali (mukammal) narx diskriminatsiyasida"],"ans":3,"exp":"To'g'ri javob: C) 1-darajali (mukammal) narx diskriminatsiyasida"},
            {"q":"|E1| < |E2| bo'lsa, qaysi holat optimal?","opts":["P1 = P2", "Q1 = Q2", "P1 > P2", "P1 < P2"],"ans":2,"exp":"To'g'ri javob: C) P1 > P2"},
            {"q":"MR1=MR2 sharti bajarilmagan holatda firma nima qiladi?","opts":["Teng taqsimlaydi", "Ishlab chiqarishni to'xtatadi", "Yuqori MR bo'lgan bozorga ko'proq tovar yo'naltiradi", "Narxni oshiradi"],"ans":2,"exp":"To'g'ri javob: B) Yuqori MR bo'lgan bozorga ko'proq tovar yo'naltiradi"},
            {"q":"Narx diskriminatsiyasining ikkinchi darajasi qanday?","opts":["Har bir xaridorga alohida narx", "Geografik segmentatsiya", "Vaqtga qarab narx", "Sotib olingan miqdorga qarab turli narxlar"],"ans":3,"exp":"To'g'ri javob: C) Sotib olingan miqdorga qarab turli narxlar"},
            {"q":"Monopol hokimiyatning iqtisodiy mohiyati nima?","opts":["Xarajatlarni oshirish", "Narxni MC dan yuqori belgilash imkoniyati (L > 0)", "Faqat foyda olish", "Narxni past belgilash"],"ans":1,"exp":"To'g'ri javob: B) Narxni MC dan yuqori belgilash imkoniyati (L > 0)"},
            {"q":"Barbara monopol bozori: MR=40-0.5Q, MC=4. Optimal Q?","opts":["36", "54", "80", "72"],"ans":3,"exp":"To'g'ri javob: C) 72"},
            {"q":"Barbara monopol bozori: optimal Q=72. Firma foydasi (TR=40Q-0.25Q^2, TC=4Q)?","opts":["864", "1584", "1296", "1440"],"ans":2,"exp":"To'g'ri javob: B) 1296"},
            {"q":"3 ishchi->12 avtomobil, 4 ishchi->36 avtomobil. Oxirgi ishchining MPL?","opts":["24", "36", "12", "18"],"ans":0,"exp":"To'g'ri javob: C) 24"},
            {"q":"TC = 200 + 5Q. Chekli xarajat (MC)?","opts":["5", "200", "5Q", "200+5"],"ans":0,"exp":"To'g'ri javob: B) 5"},
            {"q":"TC = 500 + 10Q + 2Q^2. Chekli xarajat (MC)?","opts":["500 + 10Q", "10", "10Q + 2Q^2", "10 + 4Q"],"ans":3,"exp":"To'g'ri javob: C) 10 + 4Q"},
            {"q":"TC = 200 + 5Q. Doimiy xarajat (FC)?","opts":["200+5Q", "5Q", "5", "200"],"ans":3,"exp":"To'g'ri javob: C) 200"},
            {"q":"TC = 316 + 100q. Doimiy xarajat (FC)?","opts":["100q", "100", "316", "316+100q"],"ans":2,"exp":"To'g'ri javob: C) 316"},
            {"q":"TC = 316 + 100q. O'zgaruvchan xarajat (VC)?","opts":["316", "316+100q", "100", "100q"],"ans":3,"exp":"To'g'ri javob: D) 100q"},
            {"q":"TC = 500 + 10Q + 2Q^2. Doimiy xarajat (FC)?","opts":["10Q + 2Q^2", "500 + 10Q", "10 + 4Q", "500"],"ans":3,"exp":"To'g'ri javob: B) 500"},
            {"q":"TC(Q) dan hosila olinganda qanday xarajat yuzaga keladi?","opts":["O'zgaruvchan xarajat (VC)", "O'rtacha xarajat (AC)", "Chekli xarajat (MC)", "Doimiy xarajat (FC)"],"ans":2,"exp":"To'g'ri javob: C) Chekli xarajat (MC)"},
            {"q":"TR(Q) dan hosila olinganda qanday daromad yuzaga keladi?","opts":["Umumiy daromad", "Chekli daromad (MR)", "Soliqdan keyingi daromad", "O'rtacha daromad (AR)"],"ans":1,"exp":"To'g'ri javob: B) Chekli daromad (MR)"},
            {"q":"P = 100 - 2Q, MC = 4 + 2Q. Raqobatlashgan bozorda optimal Q?","opts":["24", "20", "30", "12"],"ans":0,"exp":"To'g'ri javob: C) 24"},
            {"q":"Q = KL. Omillar 2 barobarga oshirilsa, Q necha barobara ko'payadi?","opts":["8", "4", "2", "3"],"ans":1,"exp":"To'g'ri javob: C) 4"},
            {"q":"Q = KL. Omillar 3 barobarga oshirilsa, Q necha barobara ko'payadi?","opts":["6", "9", "12", "3"],"ans":1,"exp":"To'g'ri javob: C) 9"},
            {"q":"Q = 2KL. Omillar 2 barobarga oshirilsa, Q necha barobara ko'payadi?","opts":["4", "2", "8", "16"],"ans":0,"exp":"To'g'ri javob: B) 4"},
            {"q":"Q = 3KL. Omillar 3 barobarga oshirilsa, Q necha barobara ko'payadi?","opts":["27", "3", "9", "81"],"ans":2,"exp":"To'g'ri javob: B) 9"},
            {"q":"Qisqa muddatli oraliqda qaysi ishlab chiqarish omilini o'zgartirib bo'lmaydi?","opts":["Mehnat (L)", "Kapital (K)", "Xomashyo", "Energiya"],"ans":1,"exp":"To'g'ri javob: C) Kapital (K)"},
            {"q":"Musbat masshtab samarasi uchun qaysi shart bajarilishi kerak?","opts":["lambda = 1", "f(lambdaK,lambdaL) > lambda*f(K,L)", "f(lambdaK,lambdaL) = lambda*f(K,L)", "f(lambdaK,lambdaL) < lambda*f(K,L)"],"ans":1,"exp":"To'g'ri javob: C) f(lambdaK,lambdaL) > lambda*f(K,L)"},
            {"q":"Manfiy masshtab samarasi uchun qaysi shart?","opts":["f(lambdaK,lambdaL) < lambda*f(K,L)", "Barchasi", "f(lambdaK,lambdaL) = lambda*f(K,L)", "f(lambdaK,lambdaL) > lambda*f(K,L)"],"ans":0,"exp":"To'g'ri javob: C) f(lambdaK,lambdaL) < lambda*f(K,L)"},
            {"q":"Doimiy masshtab samarasi uchun qaysi shart?","opts":["f(lambdaK,lambdaL) > lambda*f(K,L)", "lambda = 0", "f(lambdaK,lambdaL) < lambda*f(K,L)", "f(lambdaK,lambdaL) = lambda*f(K,L)"],"ans":3,"exp":"To'g'ri javob: B) f(lambdaK,lambdaL) = lambda*f(K,L)"},
            {"q":"Q = f(K, L, M) formulasi nimani ifodalaydi?","opts":["Daromad funksiyasi", "Xarajat funksiyasi", "Uch omilli ishlab chiqarish funksiyasi", "Talab funksiyasi"],"ans":2,"exp":"To'g'ri javob: C) Uch omilli ishlab chiqarish funksiyasi"},
            {"q":"Izokvanta nima?","opts":["Talab chizig'i", "Taklif chizig'i", "Bir xil Q ni ta'minlaydigan K va L kombinatsiyalari", "Bir xil xarajat chizig'i"],"ans":2,"exp":"To'g'ri javob: B) Bir xil Q ni ta'minlaydigan K va L kombinatsiyalari"},
            {"q":"20 stanok+400 ishchi=100 ta / 15 stanok+500 ishchi=100 ta. 0 stanok bilan qancha ishchi?","opts":["600", "700", "800", "900"],"ans":2,"exp":"To'g'ri javob: C) 800"},
            {"q":"10 stanok+200 ishchi=80 ta / 5 stanok+300 ishchi=80 ta. 0 stanok bilan qancha ishchi?","opts":["300", "350", "400", "450"],"ans":2,"exp":"To'g'ri javob: C) 400"},
            {"q":"10 stanok+200 ishchi=800 ta / 5 stanok+300 ishchi=800 ta. Izokvanta funksiyasi?","opts":["5K + L = 250", "20K + L = 400", "10K + L = 300", "15K + L = 350"],"ans":1,"exp":"To'g'ri javob: B) 20K + L = 400"},
            {"q":"Ishlab chiqarish imkoniyatlari egri chizig'i (PPF) nima?","opts":["Mavjud resurslar bilan ikkita tovar maksimal kombinatsiyalari", "Bir xil xarajat chizig'i", "Izokvanta", "Befarqlik chizig'i"],"ans":0,"exp":"To'g'ri javob: C) Mavjud resurslar bilan ikkita tovar maksimal kombinatsiyalari"},
            {"q":"Mashinalar ishlab chiqarish hajmining ortishi muzlatkichlar hajmiga qanday ta'sir qiladi?","opts":["Oshiradi", "O'zgartirmaydi", "Ikki barobara oshiradi", "Kamaytiradi (PPF qonuni)"],"ans":3,"exp":"To'g'ri javob: C) Kamaytiradi (PPF qonuni)"},
            {"q":"'Limonlar bozori' atamasi iqtisodiyotga qaysi olim tomonidan kiritilgan?","opts":["J.M.Keynes", "George Akerlof", "M.Friedman", "A.Marshall"],"ans":1,"exp":"To'g'ri javob: C) George Akerlof"},
            {"q":"Akerlofning 'Limonlar bozori' modeli nechanchi yil maqolasida keltirilgan?","opts":["1975", "1965", "1970", "1960"],"ans":2,"exp":"To'g'ri javob: C) 1970"},
            {"q":"Akerlof 'Limonlar bozori'da sifati yuqori avtomashinalarga berilgan nom?","opts":["Limon", "Olma", "Oltin", "Shaftoli (Peaches)"],"ans":3,"exp":"To'g'ri javob: B) Shaftoli (Peaches)"},
            {"q":"Akerlof 'Limonlar bozori'da sifati past avtomashinalarga berilgan nom?","opts":["Gilos", "Shaftoli", "Banan", "Limon"],"ans":3,"exp":"To'g'ri javob: C) Limon"},
            {"q":"'Limonlar bozori' vujudga kelishiga qaysi omil sababchi?","opts":["Davlat aralashuvi", "Taklif kamligi", "Narxlar o'zgarmasligi", "Asimmetrik axborot — adverse selection"],"ans":3,"exp":"To'g'ri javob: B) Asimmetrik axborot — adverse selection"},
            {"q":"Bozorda asimmetrik axborot nimani anglatadi?","opts":["Bir tomon boshqadan ko'proq ma'lumotga ega bo'lishi", "Narxlar teng bo'lmagan bozor", "Ikki tomonlama monopoliya", "Firmalar soni ko'p bo'lishi"],"ans":0,"exp":"To'g'ri javob: B) Bir tomon boshqadan ko'proq ma'lumotga ega bo'lishi"},
            {"q":"Rezervatsiya narxi nimani anglatadi?","opts":["O'rtacha bozor narxi", "Minimal ish haqi", "Eng past bozor narxi", "Xaridorning to'lashga tayyor bo'lgan maksimal narxi"],"ans":3,"exp":"To'g'ri javob: B) Xaridorning to'lashga tayyor bo'lgan maksimal narxi"},
            {"q":"Asimmetrik axborot sharoitida bozorni qanday tovarlar egallaydi?","opts":["Sifatli tovarlar", "Sifatsiz (past sifatli) tovarlar", "O'rtacha sifatli tovarlar", "Xorijiy tovarlar"],"ans":1,"exp":"To'g'ri javob: C) Sifatsiz (past sifatli) tovarlar"},
            {"q":"Noqulay tanlov (adverse selection) nima?","opts":["Firmalarning tarmoqdan chiqishi", "Narxlarning tushishi", "Yaxshi mahsulotlar siqib chiqarilishi, sifatsizlar qolishi", "Monopolning yo'qolishi"],"ans":2,"exp":"To'g'ri javob: A) Yaxshi mahsulotlar siqib chiqarilishi, sifatsizlar qolishi"},
            {"q":"Gloomps: Q=20-2P, MC=0. Kartel sharoitida optimal umumiy Q?","opts":["10", "5", "8", "20"],"ans":0,"exp":"To'g'ri javob: C) 10"},
            {"q":"Oligopoliya hisoblanishi uchun tarmoqda kamida nechta firma bo'lishi kerak?","opts":["5", "1", "2", "10"],"ans":2,"exp":"To'g'ri javob: B) 2"},
            {"q":"Monopoliya modelining asosiy farazlaridan biri?","opts":["Ko'p sotuvchi", "MR = P", "Bozorda yagona sotuvchi; bozorga kirish to'siqlari mavjud", "Tovar differensiallashgan"],"ans":2,"exp":"To'g'ri javob: B) Bozorda yagona sotuvchi; bozorga kirish to'siqlari mavjud"},
            {"q":"Qaysi modelda firmalar narx orqali raqobat qilishadi?","opts":["Shtakelberg modeli", "Kurno modeli", "Bertran modeli", "Cournot-Bertran modeli"],"ans":2,"exp":"To'g'ri javob: C) Bertran modeli"},
            {"q":"Bertran modelida (MC1=MC2=const) narxlar jangidan so'ng firmalarning foydasi?","opts":["Nolga teng", "Kurno foydadan ko'p", "Monopol foydaga teng", "Manfiy"],"ans":0,"exp":"To'g'ri javob: C) Nolga teng"},
            {"q":"Kurno modelida har bir firma raqibining ishlab chiqarish hajmini qanday faraz qiladi?","opts":["Nolga tushadi deb", "Doimo o'sadi deb", "O'zgarmas deb", "Maksimal bo'ladi deb"],"ans":2,"exp":"To'g'ri javob: B) O'zgarmas deb"},
            {"q":"Kurno modelida firmalar qaysi o'zgaruvchini strategik tanlaydi?","opts":["Narxni", "Ish haqini", "Ishlab chiqarish hajmini", "Reklamani"],"ans":2,"exp":"To'g'ri javob: B) Ishlab chiqarish hajmini"},
            {"q":"Kurno modeli qanday bozor turini nazarda tutadi?","opts":["Mukammal raqobat", "Monopoliya", "Monopsoniya", "Oligopol bozori (asosan duopoliya)"],"ans":3,"exp":"To'g'ri javob: B) Oligopol bozori (asosan duopoliya)"},
            {"q":"Kurno modelida firmalar ishlab chiqaradigan mahsulot qanday?","opts":["Yuqori sifatli", "Har xil", "Bir xil (gomogen) mahsulot", "Differensiallashgan"],"ans":2,"exp":"To'g'ri javob: B) Bir xil (gomogen) mahsulot"},
            {"q":"Oligopoliyada narxning bir firma tomonidan pasaytirilishi?","opts":["Talab kamayadi", "Boshqa firmalar ham narxni pasaytiradi, narxlar jangi boshlanadi", "Foyda oshadi", "Boshqa firmalar e'tibor bermaydi"],"ans":1,"exp":"To'g'ri javob: B) Boshqa firmalar ham narxni pasaytiradi, narxlar jangi boshlanadi"},
            {"q":"Yetakchi firma avval, keyin izdosh firmalar harakatlanadigan model?","opts":["Shtakelberg modeli", "Kurno modeli", "Nash modeli", "Bertran modeli"],"ans":0,"exp":"To'g'ri javob: C) Shtakelberg modeli"},
            {"q":"Shtakelberg modelida firmalar qaysi omilni hisobga oladi?","opts":["Reklama xarajatini", "Ish haqini", "Ishlab chiqarish hajmini — ketma-ket qaror", "Narxni"],"ans":2,"exp":"To'g'ri javob: B) Ishlab chiqarish hajmini — ketma-ket qaror"},
            {"q":"Oligopoliyada tarmoqda lider firma bo'lsa qaysi model yaxshi natija beradi?","opts":["Nash", "Bertran", "Kurno", "Shtakelberg"],"ans":3,"exp":"To'g'ri javob: C) Shtakelberg"},
            {"q":"Oligopoliyada bir xil hajmdagi firmalar bo'lsa qaysi model yaxshi natija beradi?","opts":["Shtakelberg", "Kurno", "Bertran", "Monopol"],"ans":1,"exp":"To'g'ri javob: D) Kurno"},
            {"q":"Bertran modelida firmalar qaysi o'zgaruvchini strategik tanlaydi?","opts":["Hajmni", "Sifatni", "Narxni", "Xarajatni"],"ans":2,"exp":"To'g'ri javob: B) Narxni"},
            {"q":"Shtakelberg modelida (MC1=MC2=const) lider firma bozorning nechchi qismiga egalik qiladi?","opts":["1/2", "2/3", "1/3", "1/4"],"ans":1,"exp":"To'g'ri javob: D) 2/3"},
            {"q":"Shtakelberg modelida (MC1=MC2=const) ergashuvchi firma bozorning nechchi qismiga egalik qiladi?","opts":["1/2", "2/3", "1/3", "1/4"],"ans":2,"exp":"To'g'ri javob: B) 1/3"},
            {"q":"Shtakelberg modelida lider firma ergashuvchi firmaga nisbatan necha barobar ko'proq ishlab chiqaradi?","opts":["2 barobar", "4 barobar", "3 barobar", "1.5 barobar"],"ans":0,"exp":"To'g'ri javob: B) 2 barobar"},
            {"q":"Qaysi holatda lider firma ergashuvchi firmaga nisbatan kamroq tovar ishlab chiqarishi mumkin?","opts":["Lider firma MC1 ergashuvchi MC2 dan sezilarli yuqori bo'lsa", "Har doim mumkin", "Kurno modelida", "Hech qachon mumkin emas"],"ans":0,"exp":"To'g'ri javob: B) Lider firma MC1 ergashuvchi MC2 dan sezilarli yuqori bo'lsa"},
            {"q":"Shtakelberg modelida qaysi firma ko'proq yutib chiqadi?","opts":["Lider firma", "Tashqi firma", "Ikkisi teng", "Ergashuvchi firma"],"ans":0,"exp":"To'g'ri javob: B) Lider firma"},
            {"q":"Shtakelberg: lider foydasi 1000$. Ergashuvchi foydasi?","opts":["750$", "1000$", "250$", "500$"],"ans":3,"exp":"To'g'ri javob: B) 500$"},
            {"q":"Shtakelberg: lider foydasi 4000$. Ergashuvchi foydasi?","opts":["1500$", "4000$", "2000$", "1000$"],"ans":2,"exp":"To'g'ri javob: C) 2000$"},
            {"q":"Shtakelberg: lider foydasi 8000$. Ergashuvchi foydasi?","opts":["2000$", "3000$", "4000$", "8000$"],"ans":2,"exp":"To'g'ri javob: C) 4000$"},
            {"q":"Shtakelberg: lider foydasi 9000$. Ergashuvchi foydasi?","opts":["3000$", "9000$", "2250$", "4500$"],"ans":3,"exp":"To'g'ri javob: C) 4500$"},
            {"q":"Shtakelberg: lider foydasi 100$. Ergashuvchi foydasi?","opts":["75$", "25$", "100$", "50$"],"ans":3,"exp":"To'g'ri javob: B) 50$"},
            {"q":"Shtakelberg: lider foydasi 600$. Ergashuvchi foydasi?","opts":["600$", "400$", "300$", "150$"],"ans":2,"exp":"To'g'ri javob: B) 300$"},
            {"q":"Shtakelberg: lider foydasi 1600$. Ergashuvchi foydasi?","opts":["800$", "400$", "1200$", "1600$"],"ans":0,"exp":"To'g'ri javob: B) 800$"},
            {"q":"Shtakelberg: lider foydasi 4050$. Ergashuvchi foydasi?","opts":["2025$", "4050$", "3000$", "1012.5$"],"ans":0,"exp":"To'g'ri javob: B) 2025$"},
            {"q":"Shtakelberg: lider foydasi 6050$. Ergashuvchi foydasi?","opts":["6050$", "3025$", "4000$", "1512.5$"],"ans":1,"exp":"To'g'ri javob: B) 3025$"},
            {"q":"Shtakelberg: lider hajmi 10 mln dona. Ergashuvchi hajmi?","opts":["5 mln", "20 mln", "10 mln", "2.5 mln"],"ans":0,"exp":"To'g'ri javob: B) 5 mln"},
            {"q":"Shtakelberg: lider hajmi 100 mln dona. Ergashuvchi hajmi?","opts":["25 mln", "50 mln", "100 mln", "75 mln"],"ans":1,"exp":"To'g'ri javob: B) 50 mln"},
            {"q":"Shtakelberg: lider hajmi 50 mln dona. Ergashuvchi hajmi?","opts":["100 mln", "25 mln", "12.5 mln", "50 mln"],"ans":1,"exp":"To'g'ri javob: B) 25 mln"},
            {"q":"Shtakelberg: ergashuvchi hajmi 50 mln dona. Lider hajmi?","opts":["150 mln", "100 mln", "50 mln", "25 mln"],"ans":1,"exp":"To'g'ri javob: C) 100 mln"},
            {"q":"Shtakelberg: ergashuvchi hajmi 150 mln dona. Lider hajmi?","opts":["600 mln", "300 mln", "150 mln", "75 mln"],"ans":1,"exp":"To'g'ri javob: C) 300 mln"},
            {"q":"Shtakelberg: ergashuvchi hajmi 3 mln dona. Lider hajmi?","opts":["3 mln", "1.5 mln", "6 mln", "12 mln"],"ans":2,"exp":"To'g'ri javob: C) 6 mln"},
            {"q":"Shtakelberg: ergashuvchi foydasi 1000$. Lider foydasi?","opts":["2000$", "1000$", "500$", "4000$"],"ans":0,"exp":"To'g'ri javob: C) 2000$"},
            {"q":"Shtakelberg: ergashuvchi foydasi 2000$. Lider foydasi?","opts":["1000$", "4000$", "2000$", "8000$"],"ans":1,"exp":"To'g'ri javob: C) 4000$"},
            {"q":"P=20, MPL=12-2L, W=80. Foydani maksimal qiluvchi L?","opts":["5", "2", "3", "4"],"ans":3,"exp":"To'g'ri javob: C) 4"},
            {"q":"MRPL > W bo'lsa, firma qanday qaror qabul qiladi?","opts":["Ishlab chiqarishni kamaytiradi", "Ko'proq ishchi yollaydi", "Ish haqini kamaytiradi", "Ishchi yollashni to'xtatadi"],"ans":1,"exp":"To'g'ri javob: C) Ko'proq ishchi yollaydi"},
            {"q":"Agar oxirgi yollangan mehnat birligi uchun MRPL ish haqidan 15$ yuqori bo'lsa, firma nima qiladi?","opts":["Ish haqini oshiradi", "Ishchini qisqartiradi", "Ishlab chiqarishni to'xtatadi", "Ko'proq ishchi yollaydi"],"ans":3,"exp":"To'g'ri javob: B) Ko'proq ishchi yollaydi"},
            {"q":"Mehnatning chekli mahsulotining qiymati (VMP_L) qanday hisoblanadi?","opts":["VMP_L = MR x L", "VMP_L = P x MPL", "VMP_L = W x L", "VMP_L = TR / L"],"ans":1,"exp":"To'g'ri javob: B) VMP_L = P x MPL"},
            {"q":"Raqobatlashgan mehnat bozorida firma uchun mehnat taklif chizig'i qanday?","opts":["Pastga qiyshiq", "Gorizontal (cheksiz elastik)", "Vertikal", "O'ng tomonga qiyshiq"],"ans":1,"exp":"To'g'ri javob: B) Gorizontal (cheksiz elastik)"},
            {"q":"Mehnat bozorida monopsonik muvozanat sharti?","opts":["MRPL = W", "MFC_L = W", "MRPL = 0", "MFC_L = MRPL"],"ans":3,"exp":"To'g'ri javob: B) MFC_L = MRPL"},
            {"q":"Monopsonist mavjud bo'lsa, muvozanat bandlik darajasi raqobatlashgan bozor bilan solishtirganda?","opts":["Yuqori bo'ladi", "Nolga teng bo'ladi", "Teng bo'ladi", "Past bo'ladi"],"ans":3,"exp":"To'g'ri javob: C) Past bo'ladi"},
            {"q":"Monopsonik mehnat bozorida ish haqi qanday bo'ladi?","opts":["Raqobatlashgan darajaga teng", "Nolga teng", "Raqobatlashgan darajadan past", "Raqobatlashgan darajadan yuqori"],"ans":2,"exp":"To'g'ri javob: C) Raqobatlashgan darajadan past"},
            {"q":"Raqobatlashgan mehnat bozorida minimal ish haqi W_e dan yuqori belgilansa, bandlik darajasi?","opts":["Kamayadi — ishsizlik vujudga keladi", "O'zgarmaydi", "Ikki barobara oshadi", "Oshadi"],"ans":0,"exp":"To'g'ri javob: C) Kamayadi — ishsizlik vujudga keladi"},
            {"q":"Ikki tomonlama monopoliyada ish haqi?","opts":["Monopol darajada", "Raqobatlashgan darajada", "Noaniq — tomonlar kelishuviga bog'liq", "Nolga teng"],"ans":2,"exp":"To'g'ri javob: C) Noaniq — tomonlar kelishuviga bog'liq"},
            {"q":"MPL=6, MR=8, W=40. Bu holat firma uchun optimalmidmi?","opts":["Ha, optimal (48>40, lekin shart MR=MC)", "Yo'q, MRPL=48 > W=40, ko'proq ishchi yollash kerak", "Yo'q, ishchini qisqartirish kerak", "Aniqlab bo'lmaydi"],"ans":1,"exp":"To'g'ri javob: B) Yo'q, MRPL=48 > W=40, ko'proq ishchi yollash kerak"},
            {"q":"Chekli daromadning kamayish qonuniga ko'ra, ish vaqti uzayishi bilan MPL qanday o'zgaradi?","opts":["O'zgarmaydi", "Kamayadi", "Oshadi", "Nolga teng bo'ladi"],"ans":1,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"MPL pasayib borsa va MR o'zgarmas bo'lganda MRPL qanday funksiya?","opts":["Nolga teng", "O'zgarmas", "O'suvchi", "Pasayuvchi"],"ans":3,"exp":"To'g'ri javob: C) Pasayuvchi"},
            {"q":"Sutkada 24 soat, dam olish 8 soat. Ish vaqti?","opts":["8 soat", "16 soat", "24 soat", "12 soat"],"ans":1,"exp":"To'g'ri javob: C) 16 soat"},
            {"q":"Raqobatlashgan bozorda MR va P o'rtasidagi munosabat?","opts":["MR > P", "MR < P", "MR = P", "MR = 0"],"ans":2,"exp":"To'g'ri javob: C) MR = P"},
            {"q":"Minimal ish haqi kim tomonidan o'rnatiladi?","opts":["Firmalar ittifoqi", "Kasaba uyushmasi", "Davlat (hukumat)", "Xalqaro tashkilotlar"],"ans":2,"exp":"To'g'ri javob: C) Davlat (hukumat)"},
            {"q":"Minimal ish haqining oshishi ko'proq kimlarga salbiy ta'sir ko'rsatadi?","opts":["Yuqori malakali ishchilarga", "Yirik korxonalarga", "Davlat xizmatchilarga", "Kam malakali va yosh ishchilarga, kichik biznesga"],"ans":3,"exp":"To'g'ri javob: C) Kam malakali va yosh ishchilarga, kichik biznesga"},
            {"q":"Yuqori malakali mutaxassis oladigan ortiqcha ish haqi qanday ataladi?","opts":["Minimal ish haqi", "Mehnat mukofoti", "Iqtisodiy renta (economic rent)", "Nominal ish haqi"],"ans":2,"exp":"To'g'ri javob: B) Iqtisodiy renta (economic rent)"},
            {"q":"Ishchiga iqtisodiy renta nima uchun to'lanadi?","opts":["Staj uchun", "Tajribasi uchun", "Ko'p ishlashi uchun", "Noyob qobiliyat, ko'nikma yoki malakasi uchun"],"ans":3,"exp":"To'g'ri javob: B) Noyob qobiliyat, ko'nikma yoki malakasi uchun"},
            {"q":"Hududda yagona korxona bo'lib, shahar aholisini ish bilan ta'minlasa, bu qanday holat?","opts":["Monopsoniya", "Ikki tomonlama monopoliya", "Monopoliya", "Oligopoliya"],"ans":0,"exp":"To'g'ri javob: B) Monopsoniya"},
            {"q":"Mehnat bozori raqobatlashgan bo'lsa mehnat narxi qanday shakllanadi?","opts":["Firma belgilaydi", "Kasaba uyushmasi belgilaydi", "Davlat tomonidan belgilanadi", "Talab va taklif kesishmasida muvozanat ish haqi sifatida"],"ans":3,"exp":"To'g'ri javob: B) Talab va taklif kesishmasida muvozanat ish haqi sifatida"},
            {"q":"Ish vaqti va dam olish o'rtasidagi bog'liqlik?","opts":["To'g'ri proporsional", "Teskari — ish vaqti + dam olish = 24 soat", "Kvadratik bog'liqlik", "Bog'liqlik yo'q"],"ans":1,"exp":"To'g'ri javob: B) Teskari — ish vaqti + dam olish = 24 soat"},
            {"q":"Kapitalning qanday turlari bor?","opts":["Ichki va tashqi kapital", "Asosiy va aylanma kapital", "Qisqa va uzoq muddatli kapital", "Real va nominal kapital"],"ans":1,"exp":"To'g'ri javob: B) Asosiy va aylanma kapital"},
            {"q":"Kapital egasiga kapitalidan foydalanganligi uchun to'lanadigan narx?","opts":["Foyda", "Renta", "Foiz (ssuda foizi)", "Ish haqi"],"ans":2,"exp":"To'g'ri javob: D) Foiz (ssuda foizi)"},
            {"q":"Har bir ishlab chiqarish davrida o'z qiymatini tayyor mahsulotga o'tkazadigan kapital turi?","opts":["Aylanma kapital (ishchi kapital)", "Moliyaviy kapital", "Asosiy kapital", "Nomoddiy kapital"],"ans":0,"exp":"To'g'ri javob: B) Aylanma kapital (ishchi kapital)"},
            {"q":"Kapital eskirishining qanday turlari bor?","opts":["Jismoniy va ma'naviy (texnologik)", "Tez va sekin", "Real va nominal", "To'liq va qisman"],"ans":0,"exp":"To'g'ri javob: B) Jismoniy va ma'naviy (texnologik)"},
            {"q":"Kapital unumdorligining pasayishi kapital eskirishining qaysi turi?","opts":["Mexanik eskirish", "Jismoniy eskirish", "To'liq eskirish", "Ma'naviy (texnologik) eskirish"],"ans":3,"exp":"To'g'ri javob: C) Ma'naviy (texnologik) eskirish"},
            {"q":"... — uzoq muddatli oraliqda ishlatiladigan ishlab chiqarish resursi","opts":["Kapital (K)", "Xomashyo", "Mehnat (L)", "Energiya"],"ans":0,"exp":"To'g'ri javob: B) Kapital (K)"},
            {"q":"Nominal foiz stavkasi nima?","opts":["Inflyatsiyaga tuzatilgan stavka", "Davlat stavkasi", "Joriy pul birliklarida ifodalangan daromad normasi", "Real stavka + 10%"],"ans":2,"exp":"To'g'ri javob: B) Joriy pul birliklarida ifodalangan daromad normasi"},
            {"q":"Real foiz stavkasi nimani ifodalaydi?","opts":["Bank foizi", "Inflyatsiyaga ko'ra tuzatilmagan stavka", "Inflyatsiyaga ko'ra tuzatilgan stavka", "Diskont stavkasi"],"ans":2,"exp":"To'g'ri javob: B) Inflyatsiyaga ko'ra tuzatilgan stavka"},
            {"q":"Xarajat va daromadlarni bir xil boshlang'ich vaqtga keltirish?","opts":["Amortizatsiya", "Kapitallashtirish", "Diskontlash", "Indeksatsiya"],"ans":2,"exp":"To'g'ri javob: B) Diskontlash"},
            {"q":"Investitsiya 200000 so'm, bir yildan 240000 so'm. Rentabellik (r)?","opts":["20%", "15%", "25%", "10%"],"ans":0,"exp":"To'g'ri javob: C) 20%"},
            {"q":"i=10%. 1 yildan keyingi 100 so'mning bugungi qiymati?","opts":["90.9 so'm", "95 so'm", "90 so'm", "100 so'm"],"ans":0,"exp":"To'g'ri javob: B) 90.9 so'm"},
            {"q":"i=10%. 2 yildan keyingi 100 so'mning bugungi qiymati?","opts":["85 so'm", "90 so'm", "80 so'm", "82.6 so'm"],"ans":3,"exp":"To'g'ri javob: B) 82.6 so'm"},
            {"q":"NPV > 0 bo'lsa, loyiha uchun qanday qaror?","opts":["Amalga oshiriladi", "Qayta ko'rib chiqiladi", "Befarq", "Amalga oshirilmaydi"],"ans":0,"exp":"To'g'ri javob: B) Amalga oshiriladi"},
            {"q":"100 mln so'm, 3 yil, 10% diskont, yillik 10 mln so'm. NPV?","opts":["0", "-75.13 mln", "+24.87 mln", "+100 mln"],"ans":1,"exp":"To'g'ri javob: A) -75.13 mln"},
            {"q":"300 mln so'm, 2 yil, 5% diskont, yillik 900 mln so'm. NPV?","opts":["-300 mln", "+1373 mln", "0", "+1800 mln"],"ans":1,"exp":"To'g'ri javob: C) +1373 mln"},
            {"q":"Mamlakatda foiz stavkasi oshsa, investitsiya hajmi?","opts":["Oshadi", "O'zgarmaydi", "Ikki barobara oshadi", "Kamayadi"],"ans":3,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"Diskont normasi oshsa, uzoq muddatli daromadlarning bugungi qiymati?","opts":["O'zgarmaydi", "Oshadi", "Ikki barobara oshadi", "Kamayadi"],"ans":3,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"Inflyatsiya 0%, depozit stavkasi 10%, 50 mln so'm. Yillik foyda?","opts":["3 mln", "5 mln", "10 mln", "1 mln"],"ans":1,"exp":"To'g'ri javob: C) 5 mln"},
            {"q":"Real foiz 5%, nominal 5%. Inflyatsiya?","opts":["5%", "0%", "15%", "10%"],"ans":1,"exp":"To'g'ri javob: A) 0%"},
            {"q":"Cheklangan yer resurslaridan foydalanganlik uchun to'lov qanday nomlanadi?","opts":["Ish haqi", "Yer rentasi", "Soliq", "Foiz"],"ans":1,"exp":"To'g'ri javob: C) Yer rentasi"},
            {"q":"Barcha yer egalari yerning sifatidan qat'i nazar oladigan renta?","opts":["Monopol renta", "Absolyut renta", "Tabiiy renta", "Differensial renta"],"ans":1,"exp":"To'g'ri javob: C) Absolyut renta"},
            {"q":"Differensial renta qiymati nimaga bog'liq?","opts":["Yerga bo'lgan umumiy talabga", "Mulkdorlar soniga", "Yer sifati va joylashuviga", "Davlat siyosatiga"],"ans":2,"exp":"To'g'ri javob: B) Yer sifati va joylashuviga"},
            {"q":"Yer taklifi absolyut noelastik bo'lsa, narx ortishi ...","opts":["Faqat yer rentasini oshiradi, miqdor o'zgarmaydi", "Rentani kamaytiradi", "Miqdorni oshiradi", "Taklifni kamaytiradi"],"ans":0,"exp":"To'g'ri javob: B) Faqat yer rentasini oshiradi, miqdor o'zgarmaydi"},
            {"q":"Renta=5000 so'm, i=10%. Yer narxi?","opts":["5000", "25000", "500000", "50000"],"ans":3,"exp":"To'g'ri javob: C) 50000"},
            {"q":"Yerga talab Q=200-4R, taklif=100. Muvozanat renta?","opts":["20", "25", "10", "50"],"ans":1,"exp":"To'g'ri javob: C) 25"},
            {"q":"Yerga talab oshsa va yer taklifi o'zgarmasa, yer rentasi?","opts":["O'zgarmaydi", "Kamayadi", "Nolga tushadi", "Ortadi"],"ans":3,"exp":"To'g'ri javob: C) Ortadi"},
            {"q":"Yer taklifiga ta'sir etuvchi asosiy omillar?","opts":["Yer egalari soni", "Narx darajasi", "Yer taklifi mutlaq cheklangan va noelastik", "Foiz stavkasi"],"ans":2,"exp":"To'g'ri javob: A) Yer taklifi mutlaq cheklangan va noelastik"},
            {"q":"Yerga bo'lgan talabning asosan qanday turlari bor?","opts":["Ichki va tashqi talab", "Sanoat va qishloq xo'jaligi talabi", "Narx va narxsiz talab", "Qishloq xo'jaligi va qishloq xo'jaligidan tashqari (sanoat, qurilish)"],"ans":3,"exp":"To'g'ri javob: B) Qishloq xo'jaligi va qishloq xo'jaligidan tashqari (sanoat, qurilish)"},
            {"q":"Umumiy muvozanat nimani anglatadi?","opts":["Barcha bozorlar bir vaqtda muvozanatda bo'lishi", "Bitta firmaning optimal holati", "Faqat mehnat bozorida muvozanat", "Faqat tovar bozorida muvozanat"],"ans":0,"exp":"To'g'ri javob: B) Barcha bozorlar bir vaqtda muvozanatda bo'lishi"},
            {"q":"Qisman muvozanat tahlilining asosiy farazi qaysi?","opts":["Barcha bozorlar bir-biriga bog'liq", "Boshqa hamma narsalar o'zgarmaydi (ceteris paribus)", "Davlat aralashmaydi", "Inflyatsiya nolga teng"],"ans":1,"exp":"To'g'ri javob: B) Boshqa hamma narsalar o'zgarmaydi (ceteris paribus)"},
            {"q":"Pareto samarali holat qachon yuzaga keladi?","opts":["MC = AC bo'lganda", "Hech kim boshqanikini yomonlashtirmasdan o'zini yaxshilay olmasa", "TR maksimum bo'lganda", "Barcha firmalar foyda olganda"],"ans":1,"exp":"To'g'ri javob: B) Hech kim boshqanikini yomonlashtirmasdan o'zini yaxshilay olmasa"},
            {"q":"Shartnoma egri chizig'i nimani ifodalaydi?","opts":["Ishlab chiqarish imkoniyatlarini", "Pareto samarali bo'lgan barcha taqsimot nuqtalarini bog'laydigan egri chiziq", "Narx-miqdor bog'liqligini", "Izokvantalar to'plamini"],"ans":1,"exp":"To'g'ri javob: B) Pareto samarali bo'lgan barcha taqsimot nuqtalarini bog'laydigan egri chiziq"},
            {"q":"Iste'molda almashtirish samaradorligi qachon yuzaga keladi?","opts":["MRS_A > MRS_B bo'lganda", "MRS_A = MRS_B bo'lganda", "U1 = U2 bo'lganda", "P1 = P2 bo'lganda"],"ans":1,"exp":"To'g'ri javob: B) MRS_A = MRS_B bo'lganda"},
            {"q":"Nima uchun samarali taqsimot adolatli bo'lmasligi mumkin?","opts":["Pareto samarali holat boylikning teng bo'lmagan taqsimotini ham o'z ichiga olishi mumkin", "Davlat aralashadi", "Bozor ishlamaydi", "MC > P bo'ladi"],"ans":0,"exp":"To'g'ri javob: B) Pareto samarali holat boylikning teng bo'lmagan taqsimotini ham o'z ichiga olishi mumkin"},
            {"q":"Edgeworth qutisi nimani aks ettiradi?","opts":["Firma xarajatlari", "Bozor narxlari", "Ikkita tovarni ikki kishi o'rtasida taqsimlashning barcha variantlari", "Ishlab chiqarish hajmlari"],"ans":2,"exp":"To'g'ri javob: C) Ikkita tovarni ikki kishi o'rtasida taqsimlashning barcha variantlari"},
            {"q":"Umumiy muvozanatda taklifning kamayishi to'ldiruvchi tovar bozoridagi talabga ta'siri?","opts":["Kamayadi", "Ikki barobara oshadi", "Oshadi", "O'zgarmaydi"],"ans":0,"exp":"To'g'ri javob: B) Kamayadi"},
            {"q":"Umumiy muvozanatda taklifning kamayishi o'rnini bosuvchi tovar bozoridagi talabga ta'siri?","opts":["Nolga tushadi", "Kamayadi", "Oshadi", "O'zgarmaydi"],"ans":2,"exp":"To'g'ri javob: C) Oshadi"},
            {"q":"Qisman muvozanat va umumiy muvozanat farqi?","opts":["Qisman — bitta bozor, umumiy — barcha bozorlar birga", "Hech qanday farq yo'q", "Faqat nom farqi", "Qisman — ko'p bozor, umumiy — bitta"],"ans":0,"exp":"To'g'ri javob: B) Qisman — bitta bozor, umumiy — barcha bozorlar birga"},
            {"q":"Qaysi muvozanat turida biror bozordagi o'zgarish boshqa bozorlarga ta'sir qiladi?","opts":["Qisman muvozanat", "Monopol muvozanat", "Kurno muvozanati", "Umumiy muvozanat"],"ans":3,"exp":"To'g'ri javob: B) Umumiy muvozanat"},
            {"q":"Utilitarizm yondashuvi bo'yicha jamiyat farovonligi?","opts":["Bozor samaradorligi", "Barcha a'zolar nafliliklarining yig'indisi", "Eng kambag'al a'zoning nafliligiga teng", "Teng taqsimlash"],"ans":1,"exp":"To'g'ri javob: B) Barcha a'zolar nafliliklarining yig'indisi"},
            {"q":"Rols yondashuvi (maximin) bo'yicha jamiyat farovonligi?","opts":["Tenglik", "Eng kam ta'minlangan a'zo nafliligini maksimallashtirish", "Yig'indi maksimum bo'lganda", "Samaradorlik"],"ans":1,"exp":"To'g'ri javob: B) Eng kam ta'minlangan a'zo nafliligini maksimallashtirish"},
            {"q":"Egalitarizm yondashuvi asosiy g'oyasi?","opts":["Maksimal samaradorlik", "Bozor erkinligi", "Faqat teng imkoniyatlar", "Teng imkoniyat ham, teng natija ham"],"ans":3,"exp":"To'g'ri javob: C) Teng imkoniyat ham, teng natija ham"},
            {"q":"Klassik liberalizm yondashuvi asosiy g'oyasi?","opts":["Shaxsiy mulk huquqi va erkin bozor, davlat aralashuvi minimal", "Davlat aralashuvi kuchli bo'lishi", "Monopol nazorat", "Teng taqsimlash"],"ans":0,"exp":"To'g'ri javob: B) Shaxsiy mulk huquqi va erkin bozor, davlat aralashuvi minimal"},
            {"q":"Robinson: U=FC, Jumavoy: U=F+C. Har biriga 5 F va 5 C. Umumiy naflilik?","opts":["25", "35", "50", "30"],"ans":1,"exp":"To'g'ri javob: C) 35"},
            {"q":"Edgeworth qutisidagi shartnoma chiziqning shaklini qaysi omillar belgilaydi?","opts":["Narx darajasi", "Resurslar miqdori", "Iste'molchilarning naflilik funksiyalarining shakli (afzalliklari)", "Bozor holati"],"ans":2,"exp":"To'g'ri javob: B) Iste'molchilarning naflilik funksiyalarining shakli (afzalliklari)"},
            {"q":"Mahalladagi svetoforlar nima sababdan jamoat ne'mati hisoblanadi?","opts":["Davlat moliyalashtiradi", "Raqobat yo'q", "Non-excludable va non-rival xususiyatlari", "Narxi yo'q"],"ans":2,"exp":"To'g'ri javob: B) Non-excludable va non-rival xususiyatlari"},
            {"q":"Quyidagi ne'matlardan qaysi biri bozor orqali samarali tarzda almashilmaydi?","opts":["Oziq-ovqat", "Kiyim-kechak", "Avtomobil", "Jamoat ne'matlari (public goods)"],"ans":3,"exp":"To'g'ri javob: C) Jamoat ne'matlari (public goods)"},
            {"q":"Tashqi samaralarning asosiy turlarini belgilang.","opts":["Ichki va tashqi", "Monopol va raqobatli", "Ijobiy va salbiy tashqi samaralar", "Tabiiy va sun'iy"],"ans":2,"exp":"To'g'ri javob: B) Ijobiy va salbiy tashqi samaralar"},
            {"q":"Aloqador bo'lmagan uchinchi tomon boshidan kechirgan iqtisodiy faoliyatning xarajati yoki foydasi?","opts":["Monopol renta", "Ichki samaralar", "Tashqi ta'sir (eksternaliya)", "Subsidiya"],"ans":2,"exp":"To'g'ri javob: B) Tashqi ta'sir (eksternaliya)"},
            {"q":"Atmosferaga zararli gazlar miqdorini kamaytirishning qaysi usuli Pigou yondashuvi?","opts":["Emissiya kvotalari", "Reklamani taqiqlash", "Muzokaralar", "Ekologik soliq (Pigou solig'i)"],"ans":3,"exp":"To'g'ri javob: B) Ekologik soliq (Pigou solig'i)"},
            {"q":"Tashqi samaralarni yumshatish bo'yicha davlat siyosati namunalari?","opts":["Faqat soliqlar", "Pigou soliqlari, standartlar, mulk huquqlari (Coase), cap-and-trade", "Faqat subsidiyalar", "Faqat normativlar"],"ans":1,"exp":"To'g'ri javob: B) Pigou soliqlari, standartlar, mulk huquqlari (Coase), cap-and-trade"},
            {"q":"Tovar iste'mol qilish natijasida uchinchi shaxslarga ta'sir qilishni ifodalaydigan tushuncha?","opts":["Iqtisodiy renta", "Tashqi ta'sir (eksternaliya)", "Iste'molchi ortiqchaligi", "Monopol kuch"],"ans":1,"exp":"To'g'ri javob: B) Tashqi ta'sir (eksternaliya)"},
            {"q":"Bitta sotuvchi va ko'p xaridorlar qatnashadigan bozor?","opts":["Monopsoniya", "Monopoliya", "Ikki tomonlama monopoliya", "Oligopoliya"],"ans":1,"exp":"To'g'ri javob: C) Monopoliya"},
            {"q":"Bitta xaridor va ko'p sotuvchilar qatnashadigan bozor?","opts":["Monopsoniya", "Oligopoliya", "Monopoliya", "Oligopsoniya"],"ans":0,"exp":"To'g'ri javob: B) Monopsoniya"},
            {"q":"Monopolist sotuvchi + monopolist xaridor = ?","opts":["Monopolistik raqobat", "Oligopoliya", "Ikki tomonlama monopoliya", "Duopoliya"],"ans":2,"exp":"To'g'ri javob: C) Ikki tomonlama monopoliya"},
            {"q":"Oligopoliya so'zining ma'nosi?","opts":["Bir nechta sotuvchi", "Ko'p sotuvchi", "Ko'p xaridor", "Yagona xaridor"],"ans":0,"exp":"To'g'ri javob: B) Bir nechta sotuvchi"},
            {"q":"Qaysi bozor turida Kurno, Bertran va Shtakelberg modellarini qo'llash mumkin?","opts":["Mukammal raqobat", "Oligopoliya", "Monopoliya", "Monopsoniya"],"ans":1,"exp":"To'g'ri javob: C) Oligopoliya"},
            {"q":"Restoranlar, dorixonalar qaysi bozor turiga namuna?","opts":["Monopolistik raqobat", "Mukammal raqobat", "Oligopoliya", "Sof monopoliya"],"ans":0,"exp":"To'g'ri javob: C) Monopolistik raqobat"},
            {"q":"Monopolistik raqobat bozorining asosiy xususiyati?","opts":["Yagona sotuvchi", "Bir nechta firma, gomogen mahsulot", "Bozorga kirish to'siqlari kuchli", "Ko'p firma + differensiallashgan mahsulot"],"ans":3,"exp":"To'g'ri javob: B) Ko'p firma + differensiallashgan mahsulot"},
            {"q":"Bozordagi subyektlar o'rtasida bir tomon ko'proq axborotga ega bo'lishi?","opts":["Monopol kuch", "Tashqi ta'sir", "Narx diskriminatsiyasi", "Asimmetrik axborot"],"ans":3,"exp":"To'g'ri javob: C) Asimmetrik axborot"},
            {"q":"Sof monopoliya bozoriga teskari bozor turi qaysi?","opts":["Monopsoniya", "Monopolistik raqobat", "Oligopoliya", "Mukammal raqobat"],"ans":0,"exp":"To'g'ri javob: C) Monopsoniya"},
            {"q":"Tovar taklifining hammasi bir necha firma tomonidan bo'lib olingan bozor?","opts":["Monopsoniya", "Monopoliya", "Monopolistik raqobat", "Oligopoliya"],"ans":3,"exp":"To'g'ri javob: B) Oligopoliya"},
            {"q":"Kam sonli xaridorlar ishtirok etadigan bozor turi?","opts":["Monopsoniya", "Monopoliya", "Oligopoliya", "Oligopsoniya"],"ans":3,"exp":"To'g'ri javob: B) Oligopsoniya"},
            {"q":"Korxona raqobatchilaridan huquqiy cheklov vositasida himoyalangan bozor turi?","opts":["Tabiiy monopoliya", "Sun'iy monopoliya", "Huquqiy monopoliya", "Monopolistik raqobat"],"ans":2,"exp":"To'g'ri javob: B) Huquqiy monopoliya"},
            {"q":"O'rtacha xarajatlar butun bozorga bitta firma xizmat qilganda minimumga erishadigan tarmoq?","opts":["Mukammal raqobat", "Monopolistik raqobat", "Tabiiy monopoliya", "Oligopoliya"],"ans":2,"exp":"To'g'ri javob: B) Tabiiy monopoliya"},
            {"q":"Oligopolistik bozorning asosiy xususiyati?","opts":["Bir xil mahsulot", "Firmalar o'rtasidagi o'zaro bog'liqlik (interdependence)", "Ko'p firma", "Erkin kirish-chiqish"],"ans":1,"exp":"To'g'ri javob: B) Firmalar o'rtasidagi o'zaro bog'liqlik (interdependence)"},
            {"q":"Oligopolistik firmalar narxlarning qanday holatidan ko'proq manfaatdor?","opts":["Past narxlardan", "O'zgaruvchan narxlardan", "Barqaror yuqori narxlardan", "Nol narxdan"],"ans":2,"exp":"To'g'ri javob: B) Barqaror yuqori narxlardan"},
            {"q":"Firma qanday sharoitda monopol hokimiyatga ega bo'la oladi?","opts":["Ko'p firma bo'lganda", "Narx past bo'lganda", "Yagona sotuvchi, kirish to'siqlari, o'rnini bosuvchi tovar yo'q", "Foyda ko'p bo'lganda"],"ans":2,"exp":"To'g'ri javob: B) Yagona sotuvchi, kirish to'siqlari, o'rnini bosuvchi tovar yo'q"},
            {"q":"Lerner ko'rsatkichi nimani ifodalaydi?","opts":["Talab elastikligini", "Foydani", "Xarajatni", "Monopol hokimiyat darajasini: L=(P-MC)/P"],"ans":3,"exp":"To'g'ri javob: B) Monopol hokimiyat darajasini: L=(P-MC)/P"},
            {"q":"Xaridorlar qaysi holatda monopsonistik hokimiyatga ega bo'ladi?","opts":["Narx yuqori bo'lganda", "Bir yoki bir nechta katta xaridor mavjud va ular narxga ta'sir qila olganda", "Xaridorlar ko'p bo'lganda", "Taklif ko'p bo'lganda"],"ans":1,"exp":"To'g'ri javob: B) Bir yoki bir nechta katta xaridor mavjud va ular narxga ta'sir qila olganda"},
            {"q":"Sof monopoliya bozorida narx va MC o'rtasidagi munosabat?","opts":["P = 0", "P > MC", "P < MC", "P = MC"],"ans":1,"exp":"To'g'ri javob: C) P > MC"},
            {"q":"Monopol hokimiyatning jamiyat uchun ijobiy tomoni?","opts":["Barcha iste'molchilar ortiqcha oladi", "Narxlar pastroq bo'ladi", "Innovatsiya va tadqiqotlarga rag'bat", "Raqobat kuchayadi"],"ans":2,"exp":"To'g'ri javob: B) Innovatsiya va tadqiqotlarga rag'bat"},
            {"q":"Monopol hokimiyatga ega firma nima maqsadda narxni tushirishi mumkin?","opts":["Raqiblarni siqib chiqarish (predatory pricing)", "Xarajatlarni qoplash", "Zararni kamaytirish uchun", "Subsidiya olish"],"ans":0,"exp":"To'g'ri javob: B) Raqiblarni siqib chiqarish (predatory pricing)"},
            {"q":"Sof monopoliyaning vujudga kelishi uchun asosiy to'siq?","opts":["Texnologiya murakkabligi", "Bozorga kirish to'siqlari (huquqiy, tabiiy, strategik)", "Xaridorlar kamligi", "Narxlar juda past"],"ans":1,"exp":"To'g'ri javob: B) Bozorga kirish to'siqlari (huquqiy, tabiiy, strategik)"},
            {"q":"Monopolist firmaga potensial raqobat sifatida nimalar?","opts":["Hech narsa yo'q", "Import, yangi texnologiyalar, o'rnini bosuvchi tovarlar, potensial kiruvchi firmalar", "Faqat subsidiyalar", "Faqat import"],"ans":1,"exp":"To'g'ri javob: B) Import, yangi texnologiyalar, o'rnini bosuvchi tovarlar, potensial kiruvchi firmalar"},
            {"q":"Qaysi auksionda tovar narxi vaqt o'tgan sari kamayib boradi?","opts":["Yopiq tender", "Ikki tomonlama auksiyon", "Gollandiya auksioni", "Ingliz auksioni"],"ans":2,"exp":"To'g'ri javob: C) Gollandiya auksioni"},
            {"q":"Auksionning qaysi turida har bir ishtirokchi o'z narxini yopiq zarfda yozadi?","opts":["Gollandiya auksioni", "Ingliz auksioni", "Yopiq tender (sealed-bid)", "Ikki tomonlama auksiyon"],"ans":2,"exp":"To'g'ri javob: C) Yopiq tender (sealed-bid)"},
            {"q":"Auksiyon bozorlarining qanday turlari bor?","opts":["Faqat ochiq auksiyon", "Faqat yopiq tender", "Ingliz, gollandiya, yopiq tender, ikki tomonlama", "Faqat ingliz va gollandiya"],"ans":2,"exp":"To'g'ri javob: B) Ingliz, gollandiya, yopiq tender, ikki tomonlama"},
            {"q":"Ikki qismli tarif (two-part tariff) nimani anglatadi?","opts":["Ikkita tovar uchun narx", "Kirish to'lovi + foydalanish uchun narx", "Ikkita auksiyon", "Ikkita bozor segmenti"],"ans":1,"exp":"To'g'ri javob: B) Kirish to'lovi + foydalanish uchun narx"},
            {"q":"Mahsulotning qo'shimcha birligini sotib olish xarajati nima?","opts":["Umumiy xarajat (TC)", "Chekli omil xarajati (MFC)", "Doimiy xarajat (FC)", "O'rtacha xarajat (AC)"],"ans":1,"exp":"To'g'ri javob: C) Chekli omil xarajati (MFC)"},
            {"q":"Narx diskriminatsiyasi nima?","opts":["Narxlarni tushirish siyosati", "Bir xil mahsulot yoki xizmat turli xaridorlarga turli narxlarda sotilishi", "Monopol narxlash", "Bepul narxlash"],"ans":1,"exp":"To'g'ri javob: B) Bir xil mahsulot yoki xizmat turli xaridorlarga turli narxlarda sotilishi"},
            {"q":"1-darajali narx diskriminatsiyasiga misol?","opts":["Avtomobil dilerligida har bir xaridor bilan alohida narx kelishish", "Mavsumiy chegirma", "Optom savdo", "Supermarketda chegirma"],"ans":0,"exp":"To'g'ri javob: B) Avtomobil dilerligida har bir xaridor bilan alohida narx kelishish"},
            {"q":"Elektr energiyasida iste'mol hajmiga qarab turli tarif — bu qaysi narx diskriminatsiyasi?","opts":["1-darajali", "Auksiyon narx", "3-darajali", "2-darajali"],"ans":3,"exp":"To'g'ri javob: B) 2-darajali"},
            {"q":"Aholiga elektroenergiya iste'moli uchun narx belgilanishi qaysi daraja?","opts":["Mukammal diskriminatsiya", "1-darajali", "3-darajali", "2-darajali — iste'mol hajmiga qarab turli tariflar"],"ans":3,"exp":"To'g'ri javob: B) 2-darajali — iste'mol hajmiga qarab turli tariflar"},
            {"q":"Raqobatlashgan bozorning samaradorlik sharti?","opts":["P = MC (= min AC uzoq muddatda)", "MR = 0", "P = MR", "TR = TC"],"ans":0,"exp":"To'g'ri javob: B) P = MC (= min AC uzoq muddatda)"},
            {"q":"AC < P bo'lsa, firma qisqa muddatda?","opts":["Zararsiz ishlaydi", "Iqtisodiy foyda oladi", "Zarar ko'radi", "Tarmoqdan chiqadi"],"ans":1,"exp":"To'g'ri javob: B) Iqtisodiy foyda oladi"},
            {"q":"Tarmoq taklifi soliq natijasida?","opts":["Kamayadi (yuqoriga siljiydi)", "O'zgarmaydi", "Elastic bo'ladi", "Ko'payadi (pastga siljiydi)"],"ans":0,"exp":"To'g'ri javob: C) Kamayadi (yuqoriga siljiydi)"},
            {"q":"Uzoq muddatli oraliqda firmalarga solingan soliq natijasida?","opts":["Foyda oshadi", "Narx o'zgarmaydi", "Firmalar tarmoqdan chiqadi, taklif kamayadi, narx oshadi", "Firmalar tarmoqqa ko'proq kiradi"],"ans":2,"exp":"To'g'ri javob: B) Firmalar tarmoqdan chiqadi, taklif kamayadi, narx oshadi"},
            {"q":"Raqobatlashgan bozor muvozanatida jamiyat farovonligi?","opts":["Nolga teng", "Minimal", "O'rtacha", "Maksimal (DWL=0)"],"ans":3,"exp":"To'g'ri javob: C) Maksimal (DWL=0)"},
            {"q":"Iste'molchi 1000 so'm to'lashga tayyor, bozor narxi 500. Iste'molchi ortiqchaligi?","opts":["100", "1000", "500", "300"],"ans":2,"exp":"To'g'ri javob: C) 500"},
            {"q":"Ishlab chiqaruvchilar o'rtasidagi raqobatning asosiy maqsadi?","opts":["Importni kamaytirish", "Davlat bilan hamkorlik", "Xarajatlarni oshirish", "Ko'proq xaridor jalb qilish, ko'proq foyda olish"],"ans":3,"exp":"To'g'ri javob: B) Ko'proq xaridor jalb qilish, ko'proq foyda olish"},
            {"q":"Iste'molchilar o'rtasidagi raqobatning asosiy maqsadi?","opts":["Taklif oshirish", "Kerakli tovarni arzonroq narxda ko'proq miqdorda sotib olish", "Monopol kuch olish", "Narxlarni oshirish"],"ans":1,"exp":"To'g'ri javob: B) Kerakli tovarni arzonroq narxda ko'proq miqdorda sotib olish"},
            {"q":"Narxlar jangi qanday holatgacha davom etadi?","opts":["P = MC gacha", "P = AC gacha", "P = AR gacha", "P = 0 gacha"],"ans":0,"exp":"To'g'ri javob: C) P = MC gacha"},
            {"q":"Qaysi bozor turida kartellar vujudga keladi?","opts":["Mukammal raqobat", "Oligopoliya", "Monopsoniya", "Monopolistik raqobat"],"ans":1,"exp":"To'g'ri javob: C) Oligopoliya"},
            {"q":"Mehnat, kapital, yer va boshqa resurslar bozori umumiy holda qanday bozorni tashkil qiladi?","opts":["Moliya bozori", "Tovar va xizmatlar bozori", "Ishlab chiqarish omillari bozori (factor market)", "Valyuta bozori"],"ans":2,"exp":"To'g'ri javob: B) Ishlab chiqarish omillari bozori (factor market)"},
            {"q":"Qo'shimcha yollangan bir ishchidan olinadigan qo'shimcha daromad?","opts":["O'rtacha daromad", "Umumiy daromad", "Mehnatning chekli daromad mahsuloti (MRPL = MR x MPL)", "Nominal daromad"],"ans":2,"exp":"To'g'ri javob: B) Mehnatning chekli daromad mahsuloti (MRPL = MR x MPL)"},
            {"q":"Mehnatning chekli daromadliligi qanday aniqlanadi?","opts":["MRPL = P x L", "MRPL = TR / L", "MRPL = MR x MPL", "MRPL = W x L"],"ans":2,"exp":"To'g'ri javob: B) MRPL = MR x MPL"},
            {"q":"Ishlab chiqarish resurslari bozorida talab nima ta'sirida shakllanadi?","opts":["Faqat davlat siyosati", "Tayyor mahsulot bozorlaridagi holat (hosila talab)", "Import hajmi", "Faqat ish haqi darajasi"],"ans":1,"exp":"To'g'ri javob: B) Tayyor mahsulot bozorlaridagi holat (hosila talab)"},
            {"q":"Insonning noyob qobiliyati va bilimi asosida qanday bozor shakllanadi?","opts":["Mukammal raqobat", "Monopsoniya", "Monopoliya yoki monopolistik raqobat", "Oligopoliya"],"ans":2,"exp":"To'g'ri javob: B) Monopoliya yoki monopolistik raqobat"},
            {"q":"Alohida bir tovar bozorida shakllanadigan muvozanat qanday nomlanadi?","opts":["Umumiy muvozanat", "Monopol muvozanat", "Kurno muvozanati", "Qisman muvozanat (partial equilibrium)"],"ans":3,"exp":"To'g'ri javob: B) Qisman muvozanat (partial equilibrium)"},
            {"q":"Sof monopsoniya holatida yagona sotib oluvchi firma tovar narxini?","opts":["Oshirib yuboradi", "Belgilaydi (nazorat qiladi)", "O'zgartira olmaydi", "Nazorat qila olmaydi"],"ans":1,"exp":"To'g'ri javob: B) Belgilaydi (nazorat qiladi)"},
            {"q":"Monopolist o'z tovari narxini oshirsa, unga talab qanday?","opts":["Oshadi", "O'zgarmaydi", "Cheksiz oshadi", "Kamayadi"],"ans":3,"exp":"To'g'ri javob: C) Kamayadi"},
            {"q":"Oligopoliyada narxning bir firma tomonidan pasaytirilishi?","opts":["Talab kamayadi", "Boshqa firmalar ham narxni pasaytiradi", "Boshqa firmalar e'tibor bermaydi", "Foyda oshadi"],"ans":1,"exp":"To'g'ri javob: B) Boshqa firmalar ham narxni pasaytiradi"},
            {"q":"Ikki tomonlama monopoliyada ish haqi?","opts":["Monopol darajada", "Nolga teng", "Raqobatlashgan darajada", "Noaniq — tomonlar kelishuviga bog'liq"],"ans":3,"exp":"To'g'ri javob: C) Noaniq — tomonlar kelishuviga bog'liq"},
        ]
    },
    "pul_oraliq": {
        "cat": "pul",
        "uz" : "Oraliq test (314 savol)",
        "ru" : "Промежуточный тест (314 вопросов)",
        "questions": [
            {"q":"\"Pul va banklar\" fani qaysi turdagi fan hisoblanadi?","opts":["Texnik fan", "Nazariy fan", "Amaliy fan", "Huquqiy fan"],"ans":1,"exp":"To'g'ri javob: A) Nazariy fan"},
            {"q":"\"Pul va banklar\" fanining predmeti nima?","opts":["Faqat pul muomalasi", "Faqat kredit munosabatlari", "Pul, kredit va bank tizimi bilan bog'liq pul-kredit munosabatlari", "Faqat bank faoliyati"],"ans":2,"exp":"To'g'ri javob: A) Pul, kredit va bank tizimi bilan bog'liq pul-kredit munosabatlari"},
            {"q":"\"Kredit\" so'zi qaysi tildan olingan?","opts":["Italyancha \"banco\" – stol so'zidan", "Lotincha \"creditum\" – ssuda, qarz so'zidan", "Inglizcha \"credit\" – hisob so'zidan", "Fransuzcha \"credit\" – ishonch so'zidan"],"ans":1,"exp":"To'g'ri javob: A) Lotincha \"creditum\" – ssuda, qarz so'zidan"},
            {"q":"Bozor iqtisodiyotining asosida nima yotadi?","opts":["Faqat savdo munosabatlari", "Siyosiy munosabatlar", "Faqat ishlab chiqarish munosabatlari", "Tovar-pul munosabatlari"],"ans":3,"exp":"To'g'ri javob: A) Tovar-pul munosabatlari"},
            {"q":"\"Pul va banklar\" fani oldiga qo'yilgan asosiy vazifalar qatoriga nima kiradi?","opts":["Faqat matematik usullarni o'rganish", "Pulning mohiyati va pul muomalasi qonuniyatlarini o'rganish", "Faqat soliq tizimini o'rganish", "Faqat xorijiy tillarni o'rganish"],"ans":1,"exp":"To'g'ri javob: A) Pulning mohiyati va pul muomalasi qonuniyatlarini o'rganish"},
            {"q":"Moliyaviy bozorlar mazmuniga ko'ra nima hisoblanadi?","opts":["Faqat aksiyalar bozori", "Bo'sh moliyaviy resurslarni ularga ehtiyoj sezayotgan sub'ektlarga o'tkazuvchi mexanizm", "Faqat valyuta bozori", "Faqat obligatsiyalar bozori"],"ans":1,"exp":"To'g'ri javob: A) Bo'sh moliyaviy resurslarni ularga ehtiyoj sezayotgan sub'ektlarga o'tkazuvchi mexanizm"},
            {"q":"Frederik S. Mishkin fikricha qimmatli qog'ozlar bozori qanday maqsadda xizmat qiladi?","opts":["Faqat inflyatsiyani pasaytirish", "Faqat xorijiy investitsiyalarni jalb qilish", "Faqat davlat qarzlarini moliyalashtirish", "Pul oqimlaridan oqilona daromad olish maqsadida ularni foydalanuvchilarga etkazib berish"],"ans":3,"exp":"To'g'ri javob: A) Pul oqimlaridan oqilona daromad olish maqsadida ularni foydalanuvchilarga etkazib berish"},
            {"q":"Pul va banklar fanining maqsadi nima?","opts":["Faqat bank xodimlarini tayyorlash", "Faqat matematik hisob-kitoblarni o'rgatish", "Talabalarga pul, kredit, banklar va moliya bozori haqida nazariy va amaliy bilimlar berish", "Faqat xorijiy tajribani o'rganish"],"ans":2,"exp":"To'g'ri javob: A) Talabalarga pul, kredit, banklar va moliya bozori haqida nazariy va amaliy bilimlar berish"},
            {"q":"Moliya bozorlarining muvaffaqiyatli ishlashi nima bilan bog'liq?","opts":["Iqtisodiy o'sishning asosiy me'zoni hisoblanadi", "Faqat eksportni oshirish bilan", "Faqat import hajmini kamaytirish bilan", "Faqat davlat byudjetini to'ldirish bilan"],"ans":0,"exp":"To'g'ri javob: A) Iqtisodiy o'sishning asosiy me'zoni hisoblanadi"},
            {"q":"A.Smit pulga qanday ta'rif bergan?","opts":["\"Pul – bu davlat mulki\"", "\"Pul – bu tovarlarning qiymati\"", "\"Pul – bu muomalaning buyuk g'ildiragi\"", "\"Pul – bu faqat oltin\""],"ans":2,"exp":"To'g'ri javob: A) \"Pul – bu muomalaning buyuk g'ildiragi\""},
            {"q":"D.Yum pulga qanday baho bergan?","opts":["\"Pul – savdo-sotiq g'ildiragini erkin va yumshoq yurishiga imkoniyat yaratadigan vositadir\"", "\"Pul – bu tovar\"", "\"Pul – bu kapital\"", "\"Pul – bu boylik\""],"ans":0,"exp":"To'g'ri javob: A) \"Pul – savdo-sotiq g'ildiragini erkin va yumshoq yurishiga imkoniyat yaratadigan vositadir\""},
            {"q":"Tijorat banklari xo'jalik sub'ektlariga nima berishi muhim deb ko'rsatilgan?","opts":["Faqat valyuta operatsiyalari o'tkazish", "Faqat konsalting xizmati ko'rsatish", "Faqat sug'urta xizmati ko'rsatish", "Kreditlar berish va naqd pullarga bo'lgan talabni qondirish"],"ans":3,"exp":"To'g'ri javob: A) Kreditlar berish va naqd pullarga bo'lgan talabni qondirish"},
            {"q":"Bozor munosabatlari asosida nima yotadi?","opts":["Faqat narx raqobati", "Faqat davlat nazorati", "O'zaro ishonch va halollik", "Faqat qonun hujjatlari"],"ans":2,"exp":"To'g'ri javob: A) O'zaro ishonch va halollik"},
            {"q":"Dastlabki tanga pullar qayerda paydo bo'lgan?","opts":["Misrda miloddan avvalgi X asrda", "Rim imperiyasida miloddan avvalgi III asrda", "Xitoy va qadimgi Lidiya xonligida miloddan avvalgi VII asrda", "Yunonistonda miloddan avvalgi V asrda"],"ans":2,"exp":"To'g'ri javob: A) Xitoy va qadimgi Lidiya xonligida miloddan avvalgi VII asrda"},
            {"q":"Oltinga o'z tasvirini tushirib zarb qilgan birinchi shoh kim hisoblanadi?","opts":["Yuliy Sezar", "Iskandar Zulqarnayn", "Lidiya shohi Giges", "Aleksandr Makedonskiy"],"ans":3,"exp":"To'g'ri javob: A) Aleksandr Makedonskiy"},
            {"q":"O'zbekiston hududida birinchi metall tangalar kim tomonidan zarb etilgan?","opts":["Ahmoniy shoh Doro I tomonidan miloddan ilgarigi VI asrda", "Aleksandr Makedonskiy tomonidan IV asrda", "Xorazmshoh Tekash tomonidan XII asrda", "Amir Temur tomonidan XIV asrda"],"ans":0,"exp":"To'g'ri javob: A) Ahmoniy shoh Doro I tomonidan miloddan ilgarigi VI asrda"},
            {"q":"O'zbekistonda birinchi metall tangalar qanday nom bilan atalgan?","opts":["\"Darik\" – tilla tangalar", "\"Dinar\" – oltin tangalar", "\"Dirham\" – kumush tangalar", "\"Fuluslar\" – mis tangalar"],"ans":0,"exp":"To'g'ri javob: A) \"Darik\" – tilla tangalar"},
            {"q":"Islom imperiyasida xalifa Abdumalik qachon yagona pul tizimini joriy etdi?","opts":["750 yilda", "912 yilda", "830 yilda", "696 yilda"],"ans":3,"exp":"To'g'ri javob: A) 696 yilda"},
            {"q":"Islom imperiyasida yirik savdo uchun qanday tangalar zarb etilgan?","opts":["Mis fuluslar", "Vazni 2,8 gramm bo'lgan kumush dirhemlar", "Vazni 4,3 gramm bo'lgan oltin dinarlar", "Oltin misqollar"],"ans":2,"exp":"To'g'ri javob: A) Vazni 4,3 gramm bo'lgan oltin dinarlar"},
            {"q":"Dastlabki qog'oz pullar qachon va qayerda chiqarilgan?","opts":["XIV asrda Angliyada", "X asrning oxiri XI asrning boshlarida Xitoyda", "XIII asrda Fransiyada", "XII asrda Italiyada"],"ans":1,"exp":"To'g'ri javob: A) X asrning oxiri XI asrning boshlarida Xitoyda"},
            {"q":"O'zbekistonda dastlabki qog'oz pullar qachon muomalaga chiqarilgan?","opts":["1918 yildan boshlab Buxoro amirligida", "1924 yilda Sovet davrida", "1905 yilda Rossiya imperiyasi davrida", "1991 yilda mustaqillik e'lon qilinganidan keyin"],"ans":0,"exp":"To'g'ri javob: A) 1918 yildan boshlab Buxoro amirligida"},
            {"q":"O'zbekistonda muomalaga chiqarilgan dastlabki qog'oz pullar qanday atalgan?","opts":["So'm", "Rubl", "Tanga", "Manat"],"ans":2,"exp":"To'g'ri javob: A) Tanga"},
            {"q":"Yevropa maktabi pulning nechta funksiyasini belgilaydi?","opts":["4 ta", "3 ta", "2 ta", "5 ta"],"ans":3,"exp":"To'g'ri javob: A) 5 ta"},
            {"q":"Amerika maktabi pulning nechta funksiyasini tan oladi?","opts":["5 ta", "4 ta", "3 ta", "2 ta"],"ans":2,"exp":"To'g'ri javob: A) 3 ta"},
            {"q":"Qog'oz pul kim tomonidan muomalaga chiqariladi?","opts":["Davlat xazinachiligi", "Moliya vazirligi", "Markaziy bank", "Tijorat banklari"],"ans":1,"exp":"To'g'ri javob: A) Moliya vazirligi"},
            {"q":"AQShda 1 dollardan 10 dollargacha bo'lgan kupyuralar kim tomonidan muomalaga chiqariladi?","opts":["AQSh G'aznachiligi", "Moliya vazirligi", "Federal Zaxira Tizimi", "Kongress"],"ans":0,"exp":"To'g'ri javob: A) AQSh G'aznachiligi"},
            {"q":"O'zbekistondagi barcha pul birliklari nima bilan ta'minlanadi?","opts":["Oltin zaxirasi bilan", "O'zbekiston Respublikasi Markaziy banki aktivlari bilan", "Davlat mulki bilan", "Xorijiy valyuta zaxiralari bilan"],"ans":1,"exp":"To'g'ri javob: A) O'zbekiston Respublikasi Markaziy banki aktivlari bilan"},
            {"q":"Hozirda nechta valyuta xalqaro rezerv valyutasi hisoblanadi?","opts":["3 ta", "5 ta", "7 ta", "10 ta"],"ans":1,"exp":"To'g'ri javob: A) 5 ta"},
            {"q":"Jahon puli funksiyasini bajaruvchi valyutalar ro'yxatiga qaysi valyuta kirmaydi?","opts":["O'zbek so'mi", "AQSh dollari", "Yevro", "Yaponiya iyenasi"],"ans":0,"exp":"To'g'ri javob: A) O'zbek so'mi"},
            {"q":"Qiymatning oddiy shakli qaysi tuzumga xos?","opts":["Sotsialist jamiyatga", "Sanoat jamiyatiga", "Natural xo'jalik tuzumiga", "Bozor iqtisodiyotiga"],"ans":2,"exp":"To'g'ri javob: A) Natural xo'jalik tuzumiga"},
            {"q":"Qog'oz pullar muomalaga kira boshlashidan oldin ular bilan parallel ravishda nima bo'lgan?","opts":["Oltin va kumush tangalar muomalada bo'lgan", "Faqat tovar ayirboshlash bo'lgan", "Hech narsa bo'lmagan", "Faqat mis tangalar muomalada bo'lgan"],"ans":0,"exp":"To'g'ri javob: A) Oltin va kumush tangalar muomalada bo'lgan"},
            {"q":"Qog'oz pullarni kirib kelishining asosiy sabablaridan biri nima?","opts":["Davlatning buyrug'i", "Qimmatbaho metallarni olib yurish va saqlashda qiyinchiliklar", "Xalqning talabi", "Oltin topilmay qolishi"],"ans":1,"exp":"To'g'ri javob: A) Qimmatbaho metallarni olib yurish va saqlashda qiyinchiliklar"},
            {"q":"Dastlab pullar qayerda saqlanган?","opts":["Ibodatxonalarda", "Shaxsiy uylarda", "Savdo omborlarida", "Qal'alarda"],"ans":0,"exp":"To'g'ri javob: A) Ibodatxonalarda"},
            {"q":"Ilk zamonaviy banklar qayerda paydo bo'lgan?","opts":["Gollandiyada", "Angliyada", "Fransiyada", "Italiyada"],"ans":3,"exp":"To'g'ri javob: A) Italiyada"},
            {"q":"\"Bank\" so'zi qaysi tildan va qanday ma'noni anglatadi?","opts":["Lotincha \"bancus\" – skamya", "Inglizcha \"bank\" – omborhona", "Italyancha \"banco\" – stol", "Fransuzcha \"banque\" – hisob"],"ans":2,"exp":"To'g'ri javob: A) Italyancha \"banco\" – stol"},
            {"q":"X asrda Italiyaning qaysi shaharlari jahon savdo markazlari edi?","opts":["Rim, Milan, Genuya", "Florensiya, Turin, Bolonya", "Venetsiya, Rim, Neapol", "Genuya, Venesiya, Florensiya"],"ans":3,"exp":"To'g'ri javob: A) Genuya, Venesiya, Florensiya"},
            {"q":"Bank tizimi nima?","opts":["Faqat Markaziy bank", "Faqat tijorat banklari", "Barcha moliya institutlari", "Mamlakat bank tizimida faoliyat yuritayotgan banklarning yig'indisi"],"ans":3,"exp":"To'g'ri javob: A) Mamlakat bank tizimida faoliyat yuritayotgan banklarning yig'indisi"},
            {"q":"Kredit tizimi nima?","opts":["Faqat xususiy moliya institutlari", "Faqat Markaziy bank tizimi", "Mamlakatdagi banklar va nobank kredit tashkilotlarining yig'indisi", "Faqat banklar tizimi"],"ans":2,"exp":"To'g'ri javob: A) Mamlakatdagi banklar va nobank kredit tashkilotlarining yig'indisi"},
            {"q":"Bozor munosabatlari sharoitida bank tizimi odatda necha pog'onali bo'ladi?","opts":["1 pog'onali", "4 pog'onali", "3 pog'onali", "2 pog'onali"],"ans":3,"exp":"To'g'ri javob: A) 2 pog'onali"},
            {"q":"Evropa Markaziy banki qachon tashkil etilgan?","opts":["2000 yilda", "1985 yilda", "1998 yilda", "1990 yilda"],"ans":2,"exp":"To'g'ri javob: A) 1998 yilda"},
            {"q":"Evropa Markaziy bankining tashkil etilishi bilan dunyoda necha pog'onali bank tizimi paydo bo'ldi?","opts":["5 pog'onali", "3 pog'onali", "4 pog'onali", "2 pog'onali"],"ans":1,"exp":"To'g'ri javob: A) 3 pog'onali"},
            {"q":"Bank tizimining elementlari qatoriga nima kiradi?","opts":["Faqat Markaziy bank va tijorat banklari", "Faqat xorijiy banklar", "Qonunchilik asoslari, Markaziy bank, tijorat banklari, infratuzilma, nazorat tizimi", "Faqat qonunchilik va nazorat"],"ans":2,"exp":"To'g'ri javob: A) Qonunchilik asoslari, Markaziy bank, tijorat banklari, infratuzilma, nazorat tizimi"},
            {"q":"Tijorat banklarini tartibga soluvchi asosiy qonun qaysi?","opts":["\"Markaziy bank to'g'risida\"gi qonun", "\"Soliq kodeksi\"", "\"Banklar va bank faoliyati to'g'risida\"gi qonun", "\"Fuqarolik kodeksi\""],"ans":2,"exp":"To'g'ri javob: A) \"Banklar va bank faoliyati to'g'risida\"gi qonun"},
            {"q":"O'zbekistonda tijorat banklari mulk shakliga ko'ra necha turga bo'linadi?","opts":["2 turga: davlat va xususiy", "3 turga: davlat, xususiy, xorijiy", "5 turga", "4 turga: davlat, aksiyadorlik-tijorat, xususiy, xorijiy kapital ishtirokidagi"],"ans":3,"exp":"To'g'ri javob: A) 4 turga: davlat, aksiyadorlik-tijorat, xususiy, xorijiy kapital ishtirokidagi"},
            {"q":"Ibodatxonalardan keyinchalik qanday moliyaviy xizmat ko'rsatish boshlangan?","opts":["Faqat valyuta almashtirish", "Faqat sug'urta xizmati", "Kassa va hisob-kitob xizmati", "Faqat kredit berish"],"ans":2,"exp":"To'g'ri javob: A) Kassa va hisob-kitob xizmati"},
            {"q":"Ilk banklardagi transferit nima?","opts":["Kredit shartnomasi", "Pul o'tkazma", "Depozit hujjati", "Omonatchilarning mablag'lari va to'lovlari hisobi yuritiladigan jadval"],"ans":3,"exp":"To'g'ri javob: A) Omonatchilarning mablag'lari va to'lovlari hisobi yuritiladigan jadval"},
            {"q":"O'zbekistonda 2022 yil 1 yanvar holatiga ko'ra nechta tijorat banki mavjud?","opts":["40 ta", "25 ta", "28 ta", "32 ta"],"ans":3,"exp":"To'g'ri javob: A) 32 ta"},
            {"q":"Tijorat banklari mijozlariga ko'ra qanday turlarga bo'linadi?","opts":["Milliy, xorijiy, xalqaro banklar", "Oddiy, ixtisoslashgan, universal banklar", "Katta, o'rta, kichik banklar", "Ulgurji, chakana, aralash banklar"],"ans":3,"exp":"To'g'ri javob: A) Ulgurji, chakana, aralash banklar"},
            {"q":"O'zbekiston Respublikasi Tashqi iqtisodiy faoliyat Milliy banki qachon tuzildi?","opts":["1991 yil 7 sentyabrda", "1990 yil 15 oktyabrda", "1992 yil 1 yanvarda", "1993 yil 5 martda"],"ans":0,"exp":"To'g'ri javob: A) 1991 yil 7 sentyabrda"},
            {"q":"\"Banklar va bank faoliyati to'g'risida\"gi qonun qachon qabul qilingan?","opts":["1994 yil 13 iyunda", "1997 yil 30 sentyabrda", "1995 yil 21 dekabrda", "1996 yil 25 aprelda"],"ans":3,"exp":"To'g'ri javob: A) 1996 yil 25 aprelda"},
            {"q":"\"O'zbekiston Respublikasining Markaziy banki to'g'risida\"gi qonun qachon qabul qilingan?","opts":["1997 yil 15 fevralda", "1996 yil 25 aprelda", "1994 yil 1 yanvarda", "1995 yil 21 dekabrda"],"ans":3,"exp":"To'g'ri javob: A) 1995 yil 21 dekabrda"},
            {"q":"1994 yilda O'zbekistonda inflyatsiyaning yillik darajasi qancha edi?","opts":["27,6 foiz", "1132 foiz", "100 foiz", "500 foiz"],"ans":1,"exp":"To'g'ri javob: A) 1132 foiz"},
            {"q":"1997 yilga kelib O'zbekistonda inflyatsiya darajasi qancha bo'ldi?","opts":["15 foiz", "50 foiz", "1132 foiz", "27,6 foiz"],"ans":3,"exp":"To'g'ri javob: A) 27,6 foiz"},
            {"q":"O'zbekiston Respublikasi bank tizimi qanday tuzilishga ega?","opts":["Bir pog'onali: faqat Markaziy bank", "Ikki pog'onali: birinchi pog'onada Markaziy bank, ikkinchi pog'onada tijorat banklari", "Uch pog'onali", "To'rt pog'onali"],"ans":1,"exp":"To'g'ri javob: A) Ikki pog'onali: birinchi pog'onada Markaziy bank, ikkinchi pog'onada tijorat banklari"},
            {"q":"2022 yil 1 yanvar holatiga ko'ra O'zbekiston kredit tizimida nechta kredit tashkiloti mavjud?","opts":["165 ta", "100 ta", "200 ta", "50 ta"],"ans":0,"exp":"To'g'ri javob: A) 165 ta"},
            {"q":"Markaziy bankning asosiy maqsadi nima?","opts":["Kreditlar berish", "Foyda olish", "Davlat byudjetini to'ldirish", "Narxlar, bank tizimi va to'lov tizimlarining barqarorligini ta'minlash"],"ans":3,"exp":"To'g'ri javob: A) Narxlar, bank tizimi va to'lov tizimlarining barqarorligini ta'minlash"},
            {"q":"Markaziy bank qanday mulkchilik shakliga ega?","opts":["Kooperativ mulk", "Xususiy mulk", "Davlatning mutlaq mulki", "Aksiyadorlik jamiyati"],"ans":2,"exp":"To'g'ri javob: A) Davlatning mutlaq mulki"},
            {"q":"Bankning ustav kapitali eng kam miqdori qancha bo'lishi lozim?","opts":["100 mlrd. so'm", "50 mlrd. so'm", "10 mlrd. so'm", "200 mlrd. so'm"],"ans":0,"exp":"To'g'ri javob: A) 100 mlrd. so'm"},
            {"q":"\"2020–2025 yillarga mo'ljallangan bank tizimini isloh qilish strategiyasi\" nima ko'zlagan?","opts":["Davlat ulushi bo'lmagan banklar aktivlari ulushini 15 foizdan 60 foizga oshirish", "Barcha banklarni davlat mulkiga o'tkazish", "Bank tizimini tugatish", "Xorijiy banklar ulushini kamaytirish"],"ans":0,"exp":"To'g'ri javob: A) Davlat ulushi bo'lmagan banklar aktivlari ulushini 15 foizdan 60 foizga oshirish"},
            {"q":"Pul mablag'larini omonatlarga jalb etish bo'yicha faoliyat bilan shug'ullanishga faqat kimlar haqli?","opts":["Faqat banklar", "Barcha moliya institutlari", "Markaziy bank", "Moliya vazirligi"],"ans":0,"exp":"To'g'ri javob: A) Faqat banklar"},
            {"q":"Banklar qanday faoliyat bilan shug'ullanishga haqli emas?","opts":["Kredit berish", "Hisob-kitob xizmati ko'rsatish", "Depozit jalb qilish", "Bevosita ishlab chiqarish, savdo va sug'urta faoliyati"],"ans":3,"exp":"To'g'ri javob: A) Bevosita ishlab chiqarish, savdo va sug'urta faoliyati"},
            {"q":"O'zbekiston bank tizimining rivojlanishida muhim muammo sifatida nima ko'rsatilgan?","opts":["Milliy valyutaning qadrsizlanish sur'atining yuqoriligi", "Xorijiy investitsiyalar yo'qligi", "Texnologiyalar etishmasligi", "Bank sonining kamligi"],"ans":0,"exp":"To'g'ri javob: A) Milliy valyutaning qadrsizlanish sur'atining yuqoriligi"},
            {"q":"Dunyodagi birinchi Markaziy bank qaysi va qachon tashkil etilgan?","opts":["Shvesiyaning Riskbanki, 1668 yilda", "Fransiyaning Markaziy banki, 1800 yilda", "Gollandiyaning Markaziy banki, 1600 yilda", "Angliyaning Markaziy banki, 1694 yilda"],"ans":0,"exp":"To'g'ri javob: A) Shvesiyaning Riskbanki, 1668 yilda"},
            {"q":"Dunyoda birinchi bo'lib banknotani emissiya qilgan Markaziy bank qaysi?","opts":["Angliyaning Markaziy banki, 1694 yilda", "AQShning Federal Zaxira Tizimi, 1913 yilda", "Shvesiyaning Riskbanki, 1668 yilda", "Fransiyaning Markaziy banki, 1800 yilda"],"ans":0,"exp":"To'g'ri javob: A) Angliyaning Markaziy banki, 1694 yilda"},
            {"q":"Dunyoning nechta davlatida Markaziy bank yo'q?","opts":["1 ta davlatda", "10 ta davlatda", "5 ta davlatda", "3 ta davlatda"],"ans":3,"exp":"To'g'ri javob: A) 3 ta davlatda"},
            {"q":"Markaziy banki bo'lmagan davlatlar qaysilar?","opts":["Saudiya Arabistoni, Singapur, Lixtenshteyn", "Shveytsariya, Lyuksemburg, Monako", "Kayman orollari, Bermuda, Gibraltar", "Vatikan, San-Marino, Andorra"],"ans":0,"exp":"To'g'ri javob: A) Saudiya Arabistoni, Singapur, Lixtenshteyn"},
            {"q":"Stokgolm bankini kim tashkil etgan?","opts":["Shvesiya parlamenti", "Shvesiya qiroli Karl X", "Gollandiyalik savdogar Yoxan Palmstrux", "Riga general-gubernatori Delagardi"],"ans":2,"exp":"To'g'ri javob: A) Gollandiyalik savdogar Yoxan Palmstrux"},
            {"q":"Stokgolm bankining kredit dalerlari qachon muomalaga chiqarilgan?","opts":["1654 yilda", "1668 yilda", "1657 yilda", "1661 yilda"],"ans":3,"exp":"To'g'ri javob: A) 1661 yilda"},
            {"q":"Palmstruxning asosiy xatosi nima bo'ldi?","opts":["Xorijiy valutada kredit berdi", "Bankni davlatga sotdi", "Qirolga juda ko'p kredit berdi", "Muomalaga chiqarilgan kredit dalerlari bankning depozit bazasidan 67,5 marta ko'p edi"],"ans":3,"exp":"To'g'ri javob: A) Muomalaga chiqarilgan kredit dalerlari bankning depozit bazasidan 67,5 marta ko'p edi"},
            {"q":"Markaziy banklarning paydo bo'lishining asosiy sababi nima?","opts":["Foyda olish maqsadi", "Xalqaro bosim", "Naqd pul emissiyasini markazlashtirish zarurligi", "Xalqning talabi"],"ans":2,"exp":"To'g'ri javob: A) Naqd pul emissiyasini markazlashtirish zarurligi"},
            {"q":"V. Smit fikricha Markaziy banklarning paydo bo'lish asosiy sababi nima?","opts":["Inflyatsiyani pasaytirish", "Milliy daromadni pul muomalasi mexanizmlari orqali davlat foydasiga qayta taqsimlash ehtiyoji", "Banknotalar ishlab chiqarish", "Xorijiy investitsiyalarni jalb qilish"],"ans":1,"exp":"To'g'ri javob: A) Milliy daromadni pul muomalasi mexanizmlari orqali davlat foydasiga qayta taqsimlash ehtiyoji"},
            {"q":"Fiskal hokimiyat qaysi organ?","opts":["Moliya vazirligi – soliq-byudjet siyosatiga javob beradi", "Parlament", "Markaziy bank", "Prezident"],"ans":0,"exp":"To'g'ri javob: A) Moliya vazirligi – soliq-byudjet siyosatiga javob beradi"},
            {"q":"Markaziy bankning emission funksiyasi nimani anglatadi?","opts":["Markaziy bank obligatsiyalar chiqaradi", "Markaziy bank aksiyalar chiqaradi", "Markaziy bank barcha moliya operatsiyalarini bajaradi", "Markaziy bank naqd pullarni emissiya qilish bo'yicha monopol mavqeiga ega"],"ans":3,"exp":"To'g'ri javob: A) Markaziy bank naqd pullarni emissiya qilish bo'yicha monopol mavqeiga ega"},
            {"q":"Markaziy bankning \"banklarning banki\" funksiyasiga nima kiradi?","opts":["Faqat kreditlar berish", "Faqat pul chiqarish", "Tijorat banklari uchun so'nggi pog'onadagi kreditor bo'lish va nazorat qilish", "Faqat hisobvaraqlar ochish"],"ans":2,"exp":"To'g'ri javob: A) Tijorat banklari uchun so'nggi pog'onadagi kreditor bo'lish va nazorat qilish"},
            {"q":"Majburiy zaxira ajratmalari summasi O'zbekistonda qanday olinadi?","opts":["Tijorat banklarining balansidan olib qo'yiladi", "Xorijiy hisobvaraqlarda saqlanadi", "Hukumat byudjetiga o'tkaziladi", "Tijorat banklarining balansida qoladi"],"ans":0,"exp":"To'g'ri javob: A) Tijorat banklarining balansidan olib qo'yiladi"},
            {"q":"AQSh va Evropada majburiy zaxira ajratmalari summasi qayerda qoladi?","opts":["Xorijiy banklarda", "Hukumat hisobvaraqlarida", "Tijorat banklarining balansida", "Markaziy bank balansida"],"ans":2,"exp":"To'g'ri javob: A) Tijorat banklarining balansida"},
            {"q":"Markaziy bankning \"davlatning banki\" funksiyasiga nima kiradi?","opts":["Faqat xorijiy valyuta boshqaruvi", "Faqat pul chiqarish", "Hukumatga kredit berish, byudjet kassa ijrosini amalga oshirish, maslahat berish", "Faqat nazorat qilish"],"ans":2,"exp":"To'g'ri javob: A) Hukumatga kredit berish, byudjet kassa ijrosini amalga oshirish, maslahat berish"},
            {"q":"Valyuta diversifikatsiyasi deganda nima tushuniladi?","opts":["Valyutani oltin bilan almashtirish", "Bir vaqtning o'zida bir nechta xorijiy valutada zahiralar tashkil qilish", "Xorijiy banklar bilan hamkorlik", "Faqat bir valyutada zahiralar saqlash"],"ans":1,"exp":"To'g'ri javob: A) Bir vaqtning o'zida bir nechta xorijiy valutada zahiralar tashkil qilish"},
            {"q":"Hozirgi kunda nechta etakchi valyuta mavjud?","opts":["5 ta", "10 ta", "7 ta (AQSh dollari, evro, yapon iyenasi, funt sterling, shveytsariya franki, kanada dollari, avst...", "3 ta"],"ans":2,"exp":"To'g'ri javob: A) 7 ta (AQSh dollari, evro, yapon iyenasi, funt sterling, shveytsariya franki, kanada dollari, avstraliya dollari)"},
            {"q":"Gold svop operatsiyasi nima?","opts":["Oltinni spot sharti bo'yicha sotish va uni forvard sharti bo'yicha sotib olish", "Oltinni kredit bilan sotib olish", "Oltinni ko'paytirish operatsiyasi", "Oltinni depozitga qo'yish"],"ans":0,"exp":"To'g'ri javob: A) Oltinni spot sharti bo'yicha sotish va uni forvard sharti bo'yicha sotib olish"},
            {"q":"Tijorat banki qanday ta'riflanadi?","opts":["Faqat depozitlar qabul qiluvchi tashkilot", "O'z xarajatlarini daromadlari hisobidan moliyalashtiradigan va yuridik shaxs maqomiga ega kredit ...", "Davlatga tegishli moliya instituti", "Faqat kreditlar beruvchi tashkilot"],"ans":1,"exp":"To'g'ri javob: A) O'z xarajatlarini daromadlari hisobidan moliyalashtiradigan va yuridik shaxs maqomiga ega kredit muassasasi"},
            {"q":"O'zbekistonda bank muassislari bankdan qachon chiqib ketish huquqiga ega emas?","opts":["Hech qachon", "Faqat bankrotlik holatida", "Bank ro'yxatga olingan kundan boshlab 1 yil mobaynida", "Bank tashkil etilganidan boshlab 5 yil mobaynida"],"ans":2,"exp":"To'g'ri javob: A) Bank ro'yxatga olingan kundan boshlab 1 yil mobaynida"},
            {"q":"Tijorat bankining boshqaruv organlariga nima kiradi?","opts":["Faqat bank direktori", "Faqat aksiyadorlar", "Markaziy bank va bank boshqaruvi", "Aksiyadorlarning umumiy yig'ilishi, bank Kengashi, Bank Boshqaruvi"],"ans":3,"exp":"To'g'ri javob: A) Aksiyadorlarning umumiy yig'ilishi, bank Kengashi, Bank Boshqaruvi"},
            {"q":"O'zbekistonda Bank kengashi a'zolari kamida necha kishidan iborat bo'lishi lozim?","opts":["3 kishi", "10 kishi", "7 kishi", "5 kishi"],"ans":3,"exp":"To'g'ri javob: A) 5 kishi"},
            {"q":"Tijorat banklari qanday faoliyat turlariga qat'iyan man etiladi?","opts":["Ishlab chiqarish, savdo va sug'urta faoliyati", "Valyuta operatsiyalari", "Kredit berish va depozit qabul qilish", "Hisob-kitob xizmatlari"],"ans":0,"exp":"To'g'ri javob: A) Ishlab chiqarish, savdo va sug'urta faoliyati"},
            {"q":"Tijorat banki tijorat faoliyatini boshlash uchun nimadan olishi kerak?","opts":["Prezidentdan farmon", "Moliya vazirligidan ruxsatnoma", "Markaziy bankdan Bosh lisenziya", "Parlamentdan qaror"],"ans":2,"exp":"To'g'ri javob: A) Markaziy bankdan Bosh lisenziya"},
            {"q":"2017 yilgа qadar O'zbekistonda tijorat banklari nechta Bosh lisenziya olishi kerak edi?","opts":["2 ta Bosh lisenziya", "1 ta Bosh lisenziya", "5 ta Bosh lisenziya", "3 ta Bosh lisenziya"],"ans":0,"exp":"To'g'ri javob: A) 2 ta Bosh lisenziya"},
            {"q":"Tijorat banklari qanday 3 asosiy funksiyani bajaradi?","opts":["Kredit berish, omonat qabul qilish, hisob yuritish", "Pul chiqarish, nazorat qilish, maslahat berish", "Investitsiya qilish, sug'urtalash, savdo qilish", "Bo'sh pul mablag'larini to'plash, transformasiya qilish, pul aylanmasini boshqarish"],"ans":3,"exp":"To'g'ri javob: A) Bo'sh pul mablag'larini to'plash, transformasiya qilish, pul aylanmasini boshqarish"},
            {"q":"Tijorat banklari emitent sifatida qanday emission qimmatli qog'ozlarni muomalaga chiqaradi?","opts":["Faqat veksellar", "Aksiyalar, obligasiyalar, opsionlar", "Faqat obligatsiyalar", "Faqat aksiyalar"],"ans":1,"exp":"To'g'ri javob: A) Aksiyalar, obligasiyalar, opsionlar"},
            {"q":"Tijorat banklari qanday noеmission qimmatli qog'ozlar chiqaradi?","opts":["Faqat obligatsiyalar", "Faqat cheklar", "Faqat veksellar", "Depozit sertifikatlari va jamg'arma sertifikatlari"],"ans":3,"exp":"To'g'ri javob: A) Depozit sertifikatlari va jamg'arma sertifikatlari"},
            {"q":"Tijorat banki tomonidan to'plangan pul mablag'lari asosan qaysi ikki yo'nalishga transformasiya qilinadi?","opts":["Kreditlar va qimmatli qog'ozlar sotib olishga", "Faqat qimmatli qog'ozlarga", "Faqat kreditlarga", "Faqat depozitlarga"],"ans":0,"exp":"To'g'ri javob: A) Kreditlar va qimmatli qog'ozlar sotib olishga"},
            {"q":"Pul aylanmasini boshqarish funksiyasi doirasida tijorat banki nima qiladi?","opts":["Faqat kredit berish", "Naqd pullarni qabul qilish va berish, naqd pulsiz hisob-kitoblar, plastik kartalar", "Faqat naqd pul berish", "Faqat aksiyalar chiqarish"],"ans":1,"exp":"To'g'ri javob: A) Naqd pullarni qabul qilish va berish, naqd pulsiz hisob-kitoblar, plastik kartalar"},
            {"q":"2018 yil 1 yanvar holatiga O'zbekistondagi tijorat banklaridan nechta xorijiy kapital ishtirokidagi bank bo'lgan?","opts":["10 ta", "7 ta", "3 ta", "5 ta"],"ans":3,"exp":"To'g'ri javob: A) 5 ta"},
            {"q":"Pul massasi nima?","opts":["Faqat xorijiy valyutalar", "Faqat bank hisobvaraqlardagi pullar", "Faqat naqd pullar", "Jismoniy va yuridik shaxslarga hamda davlatga tegishli naqd va naqdsiz pul mablag'larining yig'in..."],"ans":3,"exp":"To'g'ri javob: A) Jismoniy va yuridik shaxslarga hamda davlatga tegishli naqd va naqdsiz pul mablag'larining yig'indisi"},
            {"q":"Pul muomalasini tartibga solish kimga yuklatilgan?","opts":["Tijorat banklariga", "Hukumatga", "Markaziy banklarga", "Moliya vazirligiga"],"ans":2,"exp":"To'g'ri javob: A) Markaziy banklarga"},
            {"q":"Pul multiplikatori nimani ko'rsatadi?","opts":["Inflyatsiya darajasini", "Muomaladagi pul massasini qay darajada o'sib yoki kamayib borayotganini", "Valyuta kursini", "Foiz stavkasini"],"ans":1,"exp":"To'g'ri javob: A) Muomaladagi pul massasini qay darajada o'sib yoki kamayib borayotganini"},
            {"q":"Pul bazasiga nima kiradi?","opts":["Faqat majburiy zaxiralar", "Faqat naqd pullar", "Faqat xorijiy valyutalar", "Naqd pullar, majburiy zaxira ajratmalari va tijorat banklarining Markaziy bankdagi vakillik hisob..."],"ans":3,"exp":"To'g'ri javob: A) Naqd pullar, majburiy zaxira ajratmalari va tijorat banklarining Markaziy bankdagi vakillik hisobvaraqlari"},
            {"q":"Monetizatsiya koeffitsienti haqida Xalqaro valyuta fondi qanday tavsiya beradi?","opts":["Bu ko'rsatkich 10% bo'lishi kerak", "Bu ko'rsatkich 70% bo'lishi kerak", "Bu ko'rsatkich 30% bo'lishi kerak", "Bu ko'rsatkich 50% bo'lishi kerak"],"ans":2,"exp":"To'g'ri javob: A) Bu ko'rsatkich 30% bo'lishi kerak"},
            {"q":"Jahon banki ekspertlari monetizatsiya koeffitsienti qancha bo'lishi kerak deydi?","opts":["60%", "40%", "30%", "20%"],"ans":1,"exp":"To'g'ri javob: A) 40%"},
            {"q":"O'zbekistonda 2020 yil 1-yanvar holatiga monetizatsiya koeffisienti qancha?","opts":["10%", "40%", "30%", "17%"],"ans":3,"exp":"To'g'ri javob: A) 17%"},
            {"q":"Pul agregatlari nima?","opts":["Bank operatsiyalari turlari", "Kredit shakllari", "Pul massasini muqobil o'lchash imkoniyatini beruvchi ko'rsatkichlar", "Pul turlari"],"ans":2,"exp":"To'g'ri javob: A) Pul massasini muqobil o'lchash imkoniyatini beruvchi ko'rsatkichlar"},
            {"q":"AQShda pul massasini aniqlash uchun nechta pul agregati ishlatiladi?","opts":["4 ta", "5 ta", "2 ta", "3 ta"],"ans":0,"exp":"To'g'ri javob: A) 4 ta"},
            {"q":"M1 agregati nimani o'z ichiga oladi?","opts":["Naqd pullar va muddatli depozitlar", "Barcha bank depozitlari", "Faqat naqd pullar", "Muomaladagi naqd pullar va joriy bank schyotlaridagi mablag'lar"],"ans":3,"exp":"To'g'ri javob: A) Muomaladagi naqd pullar va joriy bank schyotlaridagi mablag'lar"},
            {"q":"M2 agregati nimadan iborat?","opts":["M1 va xorijiy valyutalar", "Faqat muddatli depozitlar", "M1 agregati va tijorat banklaridagi muddatli va jamg'arma qo'yilmalaridan (4 yilgacha)", "Barcha kredit muassasalari mablag'lari"],"ans":2,"exp":"To'g'ri javob: A) M1 agregati va tijorat banklaridagi muddatli va jamg'arma qo'yilmalaridan (4 yilgacha)"},
            {"q":"M3 agregati nimani o'z ichiga oladi?","opts":["Barcha xorijiy valyutalar", "M1 va davlat obligatsiyalari", "Faqat naqd pullar", "M2 agregati va ixtisoslashgan kredit muassasalaridagi jamg'arma qo'yilmalari"],"ans":3,"exp":"To'g'ri javob: A) M2 agregati va ixtisoslashgan kredit muassasalaridagi jamg'arma qo'yilmalari"},
            {"q":"M4 agregati nimadan iborat?","opts":["M3 agregati va yillik tijorat banklarining depozitli sertifikatlari", "M2 va davlat zayomlari", "Faqat xorijiy valyutalar", "M1 va jamg'arma obligatsiyalari"],"ans":0,"exp":"To'g'ri javob: A) M3 agregati va yillik tijorat banklarining depozitli sertifikatlari"},
            {"q":"Kvazi pullar nima?","opts":["Oltin va kumush", "Naqd pullar", "Likvid aktivlar bo'lib, tez orada pulga aylanishi mumkin bo'lgan mablag'lar", "Xorijiy valyutalar"],"ans":2,"exp":"To'g'ri javob: A) Likvid aktivlar bo'lib, tez orada pulga aylanishi mumkin bo'lgan mablag'lar"},
            {"q":"Rezerv pullarga nima kiradi?","opts":["Faqat xorijiy valyutalar", "Faqat oltin zaxirasi", "Faqat naqd pullar", "Markaziy bankdan tashqaridagi naqd pullar, majburiy zaxiradagi mablag'lar, tijorat banklarining v..."],"ans":3,"exp":"To'g'ri javob: A) Markaziy bankdan tashqaridagi naqd pullar, majburiy zaxiradagi mablag'lar, tijorat banklarining vakillik hisobvaraqlari"},
            {"q":"Muomala uchun zarur pul miqdorini kamaytirish uchun qanday choralar ko'riladi?","opts":["Iste'mol kreditini rivojlantirish, naqd pulsiz hisob-kitoblarni rivojlantirish, pullar muomala te...", "Faqat inflyatsiyani pasaytirish", "Faqat foiz stavkasini oshirish", "Faqat bank sonini kamaytirish"],"ans":0,"exp":"To'g'ri javob: A) Iste'mol kreditini rivojlantirish, naqd pulsiz hisob-kitoblarni rivojlantirish, pullar muomala tezligini oshirish"},
            {"q":"Pul muomalasini tashkil qilish va tartibga solish qanday omillarga asoslanadi?","opts":["Faqat Markaziy bank qarorlari", "Faqat xorijiy tajriba", "Faqat qonunlar", "Pul-tovar munosabatlari, tovarsiz pul harakati, me'yoriy-huquqiy asoslar va institutlar"],"ans":3,"exp":"To'g'ri javob: A) Pul-tovar munosabatlari, tovarsiz pul harakati, me'yoriy-huquqiy asoslar va institutlar"},
            {"q":"Pul tizimi nima?","opts":["Mamlakatda tarixan taркib topgan va milliy qonunchilik bilan tasdiqlangan pul muomalasini tashkil...", "Faqat tangalar tizimi", "Faqat elektron to'lovlar tizimi", "Faqat banknotalar tizimi"],"ans":0,"exp":"To'g'ri javob: A) Mamlakatda tarixan taркib topgan va milliy qonunchilik bilan tasdiqlangan pul muomalasini tashkil qilish shakli"},
            {"q":"Pul tizimining objektiv asosiga nima kiradi?","opts":["Xalqaro standartlar", "Markaziy bank qarorlari", "Qonunlar va nizomlar", "Tovar-pul munosabatlarining rivojlanganlik darajasi"],"ans":3,"exp":"To'g'ri javob: A) Tovar-pul munosabatlarining rivojlanganlik darajasi"},
            {"q":"Pul tizimining sub'ektiv asosiga nima kiradi?","opts":["Inflyatsiya darajasi", "Iqtisodiy rivojlanish darajasi", "To'lov hujjatlari va vositalarini qonunchilikda belgilab qo'yilishi", "Valyuta kursi"],"ans":2,"exp":"To'g'ri javob: A) To'lov hujjatlari va vositalarini qonunchilikda belgilab qo'yilishi"},
            {"q":"Pul tizimining funksional jihati nima?","opts":["Faqat tijorat banklari faoliyati", "Faqat Markaziy bank faoliyati", "Pul muomalasini tashkil qilish tamoyillari, shakllari va usullarining yig'indisi", "Pul muomalasini tashkil qiluvchi institutlar majmui"],"ans":2,"exp":"To'g'ri javob: A) Pul muomalasini tashkil qilish tamoyillari, shakllari va usullarining yig'indisi"},
            {"q":"Pul tizimining institutsional jihatiga qaysi institutlar kiradi?","opts":["Markaziy bank, tijorat banklari, kliring markazlari, hisob uylari", "Faqat tijorat banklari", "Faqat xorijiy banklar", "Faqat Markaziy bank"],"ans":0,"exp":"To'g'ri javob: A) Markaziy bank, tijorat banklari, kliring markazlari, hisob uylari"},
            {"q":"Bimetalizm nima?","opts":["Faqat elektron pullar tizimi", "Faqat qog'oz pullar tizimi", "Ikki noyob metaldan (oltin va kumush) pul sifatida foydalanishga asoslangan pul tizimi", "Faqat oltin asosidagi pul tizimi"],"ans":2,"exp":"To'g'ri javob: A) Ikki noyob metaldan (oltin va kumush) pul sifatida foydalanishga asoslangan pul tizimi"},
            {"q":"Bimetalizm qaysi asrlarda qo'llanilgan?","opts":["XIX – XX asrlarda", "XVI – XVIII asrlarda", "XX – XXI asrlarda", "X – XII asrlarda"],"ans":1,"exp":"To'g'ri javob: A) XVI – XVIII asrlarda"},
            {"q":"Biметализмнинг параллел валюта тизимида нима бўлади?","opts":["Faqat kumush tangalar muomalada bo'ladi", "Davlat oltin va kumush tangalar o'rtasidagi nisbatni belgilamaydi, bu nisbat bozorda o'rnatiladi", "Faqat oltin tangalar muomalada bo'ladi", "Davlat nisbatni o'zi belgilaydi"],"ans":1,"exp":"To'g'ri javob: A) Davlat oltin va kumush tangalar o'rtasidagi nisbatni belgilamaydi, bu nisbat bozorda o'rnatiladi"},
            {"q":"Biметализмнинг иккиёқлама валюта тизимида нима бўлади?","opts":["Faqat yevro ishlatiladi", "Nisbat bozorda o'rnatiladi", "Faqat dollar ishlatiladi", "Davlat oltin va kumush tangalar o'rtasidagi nisbatni belgilaydi"],"ans":3,"exp":"To'g'ri javob: A) Davlat oltin va kumush tangalar o'rtasidagi nisbatni belgilaydi"},
            {"q":"Biметализмнинг оқсоқланувчи валюта тизимида нима бўлади?","opts":["Oltin tangalar erkin zarb etiladi, kumush tangalar esa yopiq rejimda zarb etiladi", "Ikkalasi ham erkin zarb etiladi", "Ikkalasi ham yopiq zarb etiladi", "Faqat qog'oz pullar ishlatiladi"],"ans":0,"exp":"To'g'ri javob: A) Oltin tangalar erkin zarb etiladi, kumush tangalar esa yopiq rejimda zarb etiladi"},
            {"q":"Monometalizm nima?","opts":["Bir metal (oltin yoki kumush) ning pul vazifasini bajarishi", "Ikki metaldan foydalanish", "Elektron pul tizimi", "Qog'oz pullar tizimi"],"ans":0,"exp":"To'g'ri javob: A) Bir metal (oltin yoki kumush) ning pul vazifasini bajarishi"},
            {"q":"Pul tizimining barqarorligi nimani anglatadi?","opts":["Oltin bilan ta'minlanganlik", "Pulning barcha funksiyalarini to'liq bajarilishini ta'minlash", "Inflyatsiyaning yo'qligi", "Pul kursining o'zgarmasligi"],"ans":1,"exp":"To'g'ri javob: A) Pulning barcha funksiyalarini to'liq bajarilishini ta'minlash"},
            {"q":"Pul tizimining elastikligi nimani anglatadi?","opts":["Iqtisodiyotning pul mablag'lariga bo'lgan talabini o'zgarishiga o'z vaqtida javob bera olish", "Yangi pullarni chiqarish", "Pul kursining o'zgarishi", "Valyuta almashinuvi"],"ans":0,"exp":"To'g'ri javob: A) Iqtisodiyotning pul mablag'lariga bo'lgan talabini o'zgarishiga o'z vaqtida javob bera olish"},
            {"q":"Baho masktabi nima?","opts":["Tovarlar narxining ko'rsatkichi", "Milliy valyutaning oltin bilan ta'minlanishi", "Inflyatsiya darajasi", "Valyuta kursi"],"ans":1,"exp":"To'g'ri javob: A) Milliy valyutaning oltin bilan ta'minlanishi"},
            {"q":"Yamayya jahon valyuta tizimida qachon oltin demonetizatsiyasi amalga oshirildi?","opts":["1944 yilda", "1976–1978 yillarda", "2000 yilda", "1990 yilda"],"ans":1,"exp":"To'g'ri javob: A) 1976–1978 yillarda"},
            {"q":"Oltin demonetizatsiyasi qanday oqibatga olib keldi?","opts":["Baho masktabi bekor qilindi, muomaladagi pullar Markaziy bank aktivlari bilan ta'minlanadi", "Valyuta kurslari barqarorlashdi", "Oltin qiymati oshdi", "Barcha mamlakatlar oltin standartiga o'tdi"],"ans":0,"exp":"To'g'ri javob: A) Baho masktabi bekor qilindi, muomaladagi pullar Markaziy bank aktivlari bilan ta'minlanadi"},
            {"q":"Ilk banklar qanday asosiy xatarni (riskni) kamaytirish uchun garov talab qilgan?","opts":["Bozor riskini kamaytirish uchun", "Valyuta riskini kamaytirish uchun", "Likvidlik riskini kamaytirish uchun", "Ssuda operatsiyalarida kredit riskini kamaytirish uchun"],"ans":3,"exp":"To'g'ri javob: A) Ssuda operatsiyalarida kredit riskini kamaytirish uchun"},
            {"q":"Garov sifatida nimalар qabul qilingan?","opts":["Faqat oltin", "Faqat tovarlar", "Qimmatbaho metallar, ko'chmas mulk, kemalar", "Faqat er-mulk"],"ans":2,"exp":"To'g'ri javob: A) Qimmatbaho metallar, ko'chmas mulk, kemalar"},
            {"q":"Pul muomalasi qonuni nimani taqozo qiladi?","opts":["Faqat foiz stavkasini belgilashni", "Muomala uchun zarur pul miqdorini aniqlashni", "Faqat inflyatsiyani belgilashni", "Faqat valyuta kursini belgilashni"],"ans":1,"exp":"To'g'ri javob: A) Muomala uchun zarur pul miqdorini aniqlashni"},
            {"q":"Barklays bank (Angliya) aktivlarida eng katta ulushni nima tashkil etadi?","opts":["Berilgan kreditlar – 35,9%", "Qimmatli qog'ozlarga qilingan investitsiyalar – 46,7%", "Naqd pullar – 8,4%", "Asosiy vositalar – 5,9%"],"ans":1,"exp":"To'g'ri javob: A) Qimmatli qog'ozlarga qilingan investitsiyalar – 46,7%"},
            {"q":"Nobank moliya-kredit muassasalariga quyidagilardan qaysi biri kirmaydi?","opts":["Tijorat banklari", "Kredit uyushmalari", "Lombardlar", "Mikrokredit tashkilotlari"],"ans":0,"exp":"To'g'ri javob: A) Tijorat banklari"},
            {"q":"Nobank moliya-kredit muassasalarining zarurligi qaysi omil bilan belgilanadi?","opts":["Markaziy bank nazoratisiz ishlashi", "Faqat xorijiy valyutada ishlashi", "Alohida bank operatsiyasini tijorat bankiga qaraganda tez va arzon bajara olishi", "Depozit qabul qilish imkoniyati"],"ans":2,"exp":"To'g'ri javob: A) Alohida bank operatsiyasini tijorat bankiga qaraganda tez va arzon bajara olishi"},
            {"q":"Tijorat banklari ko'p hollarda kichik summadagi operatsiyalarni nima sababli amalga oshirishdan manfaatdor bo'lmaydi?","opts":["Texnik imkoniyat yo'qligi sababli", "Markaziy bank ruxsati bo'lmaganligidan", "Qonun taqiqlaganligi sababli", "Daromad miqdori kamligi sababli"],"ans":3,"exp":"To'g'ri javob: A) Daromad miqdori kamligi sababli"},
            {"q":"NMKM resurslarining dastlabki manbai nima hisoblanadi?","opts":["Grantlar", "Kreditlar", "Ustav kapitali", "Depozitlar"],"ans":2,"exp":"To'g'ri javob: A) Ustav kapitali"},
            {"q":"O'zbekistonda 2017 yil 1 oktyabrdan boshlab mikrokredit tashkilotlari uchun ustav kapitalining eng kam miqdori qancha?","opts":["1 mlrd. so'm", "2 mlrd. so'm", "500 mln. so'm", "5 mlrd. so'm"],"ans":1,"exp":"To'g'ri javob: A) 2 mlrd. so'm"},
            {"q":"O'zbekistonda 2017 yil 1 oktyabrdan boshlab lombardlar uchun ustav kapitalining eng kam miqdori qancha?","opts":["500 mln. so'm", "100 mln. so'm", "2 mlrd. so'm", "1 mlrd. so'm"],"ans":0,"exp":"To'g'ri javob: A) 500 mln. so'm"},
            {"q":"Kredit uyushmalarida qanday resurs manbalari mavjud?","opts":["Ustav kapitali va a'zolaridan qabul qilingan depozitlar", "Ustav kapitali va davlat subsidiyalari", "Faqat ustav kapitali", "Ustav kapitali va obligatsiyalar"],"ans":0,"exp":"To'g'ri javob: A) Ustav kapitali va a'zolaridan qabul qilingan depozitlar"},
            {"q":"Kredit uyushmalarining o'ziga xos xususiyati nima?","opts":["Davlatdan subsidiya oladi", "Barcha jismoniy shaxslardan depozit qabul qiladi", "Yuridik shaxslardan depozit qabul qiladi", "Faqat o'zining a'zolaridan depozitlar qabul qilish huquqiga ega"],"ans":3,"exp":"To'g'ri javob: A) Faqat o'zining a'zolaridan depozitlar qabul qilish huquqiga ega"},
            {"q":"Mikrokredit tashkilotlari qanday moliyaviy manbalar hisobidan faoliyat olib boradi?","opts":["Faqat depozitlar hisobidan", "Davlat byudjeti mablag'lari hisobidan", "Depozitlar va kreditlar hisobidan", "Ustav kapitali va moliyaviy grantlar hisobidan"],"ans":3,"exp":"To'g'ri javob: A) Ustav kapitali va moliyaviy grantlar hisobidan"},
            {"q":"Mikrokredit qanday mablag' deb ta'riflanadi?","opts":["Tadbirkorlik faoliyatini amalga oshirish uchun eng kam ish haqining ming barobari miqdoridan oshm...", "Jismoniy shaxslarga beriladigan istalgan miqdordagi kredit", "Tadbirkorlik faoliyatini amalga oshirish uchun eng kam ish haqining yuz barobari miqdoridan oshma...", "Eng kam ish haqining ikki ming barobari miqdoridan oshmaydigan lizing krediti"],"ans":0,"exp":"To'g'ri javob: A) Tadbirkorlik faoliyatini amalga oshirish uchun eng kam ish haqining ming barobari miqdoridan oshmaydigan kredit"},
            {"q":"Mikroqarz nima?","opts":["Eng kam ish haqining ikki ming barobari miqdoridagi lizing", "Jismoniy shaxslarga eng kam ish haqining yuz barobari miqdoridan oshmaydigan miqdorda beriladigan...", "Yuridik shaxslarga beriladigan qarz", "Tadbirkorlik uchun eng kam ish haqining ming barobari miqdoridagi kredit"],"ans":1,"exp":"To'g'ri javob: A) Jismoniy shaxslarga eng kam ish haqining yuz barobari miqdoridan oshmaydigan miqdorda beriladigan qarz"},
            {"q":"Mikrolizing nima?","opts":["Tadbirkorlik faoliyatini amalga oshirish uchun eng kam ish haqining ikki ming barobari miqdoridan...", "Jismoniy shaxslarga beriladigan qarz", "Eng kam ish haqining yuz barobari miqdoridagi qarz", "Eng kam ish haqining ming barobari miqdoridagi kredit"],"ans":0,"exp":"To'g'ri javob: A) Tadbirkorlik faoliyatini amalga oshirish uchun eng kam ish haqining ikki ming barobari miqdoridan oshmaydigan lizing krediti"},
            {"q":"Lombardlar qanday operatsiyalarni amalga oshiradi?","opts":["Faqat pul mablag'lari garovida kredit beradi", "Ko'chmas mulk garovida kredit beradi", "Zargarlik buyumlari va qimmatli qog'ozlarni garovga olish yo'li bilan kreditlar beradi", "A'zolariga kredit beradi"],"ans":2,"exp":"To'g'ri javob: A) Zargarlik buyumlari va qimmatli qog'ozlarni garovga olish yo'li bilan kreditlar beradi"},
            {"q":"2021 yilning 1 yanvar holatiga ko'ra O'zbekistonda nechta lombard mavjud edi?","opts":["67 ta", "62 ta", "55 ta", "69 ta"],"ans":0,"exp":"To'g'ri javob: A) 67 ta"},
            {"q":"2021 yilning 1 yanvar holatiga ko'ra lombardlar tomonidan berilgan kreditlarning jami summasi qancha edi?","opts":["947 267 mln. so'm", "109 311 mln. so'm", "162 285 mln. so'm", "495 795 mln. so'm"],"ans":2,"exp":"To'g'ri javob: A) 162 285 mln. so'm"},
            {"q":"2021 yilning 1 oktyabr holatiga ko'ra O'zbekistonda nechta mikrokredit tashkiloti faoliyat yuritardi?","opts":["69 ta", "61 ta", "67 ta", "75 ta"],"ans":0,"exp":"To'g'ri javob: A) 69 ta"},
            {"q":"Mikrokredit tashkilotlari tomonidan berilgan mikrokreditlar va mikrolizingning 2021 yil 1 oktyabr holatida jami summasi qancha edi?","opts":["602 135 mln. so'm", "495 795 mln. so'm", "162 285 mln. so'm", "947 267 mln. so'm"],"ans":3,"exp":"To'g'ri javob: A) 947 267 mln. so'm"},
            {"q":"Kredit agentliklarining resurs manbalari nimalardan iborat?","opts":["Depozitlar va ustav kapitali", "Davlat grantlari va ustav kapitali", "Ustav kapitali va ipoteka qimmatli qog'ozlarini sotishdan olingan mablag'lar", "Faqat ustav kapitali"],"ans":2,"exp":"To'g'ri javob: A) Ustav kapitali va ipoteka qimmatli qog'ozlarini sotishdan olingan mablag'lar"},
            {"q":"Kredit agentliklari qanday faoliyat olib boradi?","opts":["Kichik biznesga kredit beradi", "Aholidan depozit qabul qiladi", "Ipoteka qimmatli qog'ozlarini chiqarish yo'li bilan tijorat banklarining ipoteka kreditlarini qay...", "Valyuta almashtirish operatsiyalarini amalga oshiradi"],"ans":2,"exp":"To'g'ri javob: A) Ipoteka qimmatli qog'ozlarini chiqarish yo'li bilan tijorat banklarining ipoteka kreditlarini qayta moliyalashtiradi"},
            {"q":"Hisob-kitob muassasalari qanday manbalar hisobidan faoliyat olib boradi?","opts":["Davlat byudjeti va ustav kapitali hisobidan", "Depozitlar va ustav kapitali hisobidan", "Ustav kapitali va hisob-kitoblarda ishtirok etuvchi banklardan olingan avans to'lovlari hisobidan", "Faqat ustav kapitali hisobidan"],"ans":2,"exp":"To'g'ri javob: A) Ustav kapitali va hisob-kitoblarda ishtirok etuvchi banklardan olingan avans to'lovlari hisobidan"},
            {"q":"Taraqqiy etgan davlatlarda kredit uyushmalari kredit berishda qaysi printsiplariga e'tibor qaratishmaydi?","opts":["Qaytarishlik va muddatlilik prinsiplariga", "Barcha printsiplariga", "Ta'minlanganlik va maqsadlilik prinsiplariga", "Foiz to'lashlilik va muddatlilik prinsiplariga"],"ans":2,"exp":"To'g'ri javob: A) Ta'minlanganlik va maqsadlilik prinsiplariga"},
            {"q":"Lizing shartnomasida qanday shartlardan biri bajarilishi kerak?","opts":["Lizing ob'ekti har yili qayta baholanishi kerak", "Lizing shartnamasi muddati tugagach, lizing ob'ekti lizing oluvchining mulki bo'lib o'tsa", "Lizing shartnamasi faqat 1 yilga tuzilishi mumkin", "Lizing oluvchi har oyda hisobot taqdim etishi kerak"],"ans":1,"exp":"To'g'ri javob: A) Lizing shartnamasi muddati tugagach, lizing ob'ekti lizing oluvchining mulki bo'lib o'tsa"},
            {"q":"Mikrokredit tashkilotiga lицензия olish uchun lицензия berganlik uchun qancha davlat boji undiriladi?","opts":["BHMning 4 barobari miqdorida", "BHMning 1 barobari miqdorida", "BHMning 2 barobari miqdorida", "BHMning 10 barobari miqdorida"],"ans":2,"exp":"To'g'ri javob: A) BHMning 2 barobari miqdorida"},
            {"q":"Lombard lицензiyasini olish uchun qancha davlat boji undiriladi?","opts":["BHMning 5 barobari miqdorida", "BHMning 4 barobari miqdorida", "BHMning 1 barobari miqdorida", "BHMning 2 barobari miqdorida"],"ans":1,"exp":"To'g'ri javob: A) BHMning 4 barobari miqdorida"},
            {"q":"Mikrokredit tashkilotining ustav fondi nechta foizgacha boshqa mol-mulkdan shakllantirilishi mumkin?","opts":["O'n foizidan oshmaydigan boshqa mol-mulkdan", "O'ttiz foizidan oshmaydigan boshqa mol-mulkdan", "Yigirma foizidan oshmaydigan boshqa mol-mulkdan", "Elli foizidan oshmaydigan boshqa mol-mulkdan"],"ans":2,"exp":"To'g'ri javob: A) Yigirma foizidan oshmaydigan boshqa mol-mulkdan"},
            {"q":"Lizing shartnomasida lizing tо'lovlarining jami summasi lizing ob'ekti qiymatining necha foizidan ortiq bo'lsa, shartnoma lizing hisoblanadi?","opts":["80 foizidan ortiq bo'lsa", "90 foizidan ortiq bo'lsa", "50 foizidan ortiq bo'lsa", "70 foizidan ortiq bo'lsa"],"ans":1,"exp":"To'g'ri javob: A) 90 foizidan ortiq bo'lsa"},
            {"q":"Lombard boshqaruv organi rahbari uchun bank-moliya sohasida necha yildan kam bo'lmagan ish tajribasi talab qilinadi?","opts":["Ikki yildan kam bo'lmagan", "Uch yildan kam bo'lmagan", "Bir yildan kam bo'lmagan", "Besh yildan kam bo'lmagan"],"ans":0,"exp":"To'g'ri javob: A) Ikki yildan kam bo'lmagan"},
            {"q":"Markaziy bank mikrokredit tashkiloti litsenziyasi amal qilishini tо'xtatib turish uchun belgilagan muddat qancha bo'lishi mumkin?","opts":["Uch oydan oshmasligi kerak", "Bir yildan oshmasligi kerak", "Olti oydan oshmasligi kerak", "Ikki oydan oshmasligi kerak"],"ans":2,"exp":"To'g'ri javob: A) Olti oydan oshmasligi kerak"},
            {"q":"Mikrokredit tashkiloti davlat ro'yxatidan o'tkazilgandan so'ng litsenziya olish uchun necha oydan kechiktirmay Markaziy bankka murojaat qilishi kerak?","opts":["Olti oydan kechiktirmay", "Bir oydan kechiktirmay", "Uch oydan kechiktirmay", "Ikki oydan kechiktirmay"],"ans":1,"exp":"To'g'ri javob: A) Bir oydan kechiktirmay"},
            {"q":"Quyidagi shaxslardan qaysi biri mikrokredit tashkilotining muassisi bo'la olmaydi?","opts":["Davlat organlari, siyosiy partiyalar, kasaba uyushmalari va diniy tashkilotlar", "Xorijiy yuridik shaxslar", "Xususiy kompaniyalar", "Jismoniy shaxslar"],"ans":0,"exp":"To'g'ri javob: A) Davlat organlari, siyosiy partiyalar, kasaba uyushmalari va diniy tashkilotlar"},
            {"q":"Bank inqirozi deganda nima tushuniladi?","opts":["Banklar faoliyatidagi risklarning kuchayishi natijasida ularning aktivlari sifatining pasayishi v...", "Faqat foiz stavkalarining oshib ketishi", "Faqat banklar sonining kamayishi", "Faqat kreditlarning qaytmasligi"],"ans":0,"exp":"To'g'ri javob: A) Banklar faoliyatidagi risklarning kuchayishi natijasida ularning aktivlari sifatining pasayishi va moliyaviy holatining yomonlashishi"},
            {"q":"Lotin Amerikasi mamlakatlarida bank inqirozlari 1980 yildan so'ng qanday sababdan yuzaga keldi?","opts":["Aholining depozitlarini ommaviy yechib olishi tufayli", "Xorijiy valyuta taqchilligi sababli", "Moliyaviy liberallashtirish natijasida banklar xususiylashtirildi, nazorat bo'shashtirildi va mal...", "Soliq yukining oshishi sababli"],"ans":2,"exp":"To'g'ri javob: A) Moliyaviy liberallashtirish natijasida banklar xususiylashtirildi, nazorat bo'shashtirildi va malakasiz xodimlar kreditlar berdi"},
            {"q":"2001 yilda Argentinada bank inqirozi qanday sababdan yuzaga keldi?","opts":["Markaziy bank diskont stavkasini oshirdi", "Tijorat banklari davlatning yirik summadagi qimmatli qog'ozlarini sotib olishga majbur qilindi, k...", "Xorijiy investitsiyalar to'xtatildi", "Aholining daromadlari keskin kamaydi"],"ans":1,"exp":"To'g'ri javob: A) Tijorat banklari davlatning yirik summadagi qimmatli qog'ozlarini sotib olishga majbur qilindi, keyin ularning bozor bahosi tushdi"},
            {"q":"Bank inqirozining sabablari qatorida transformatsiya riski nima deb tushuniladi?","opts":["Foiz stavkalarining oshishi", "Qisqa muddatli depozitlar hisobiga uzoq muddatli kreditlar berish natijasida likvidlilik muammosi...", "Valyuta kursining tebranishi", "Inflyatsiyaning kuchayishi"],"ans":1,"exp":"To'g'ri javob: A) Qisqa muddatli depozitlar hisobiga uzoq muddatli kreditlar berish natijasida likvidlilik muammosi yuzaga kelishi"},
            {"q":"XVF ekspertlarining tadqiqotiga ko'ra bank inqiroziga olib keladigan ko'rsatkich qanday?","opts":["Kreditlar YaIMga nisbatan 50 foizga yetganda yillik o'sish sur'ati 20 foizdan yuqori bo'lsa", "Kreditlar YaIMga nisbatan 80 foizga yetganda yillik o'sish sur'ati 50 foizdan yuqori bo'lsa", "Kreditlar YaIMga nisbatan 30 foizga yetganda yillik o'sish sur'ati 10 foizdan yuqori bo'lsa", "Kreditlar YaIMga nisbatan 60 foizga yetganda yillik o'sish sur'ati 30 foizdan yuqori bo'lsa"],"ans":3,"exp":"To'g'ri javob: A) Kreditlar YaIMga nisbatan 60 foizga yetganda yillik o'sish sur'ati 30 foizdan yuqori bo'lsa"},
            {"q":"Moliya bozoridagi noaniqlikning kuchayishi bank inqiroziga qanday olib keladi?","opts":["Bir necha bankning bankrot bo'lishi natijasida boshqa banklar kreditlashni keskin kamaytiradilar", "Davlat byudjeti defisiti oshadi", "Inflyatsiya darajasi pasayadi", "Aholining ishsizligi ortadi"],"ans":0,"exp":"To'g'ri javob: A) Bir necha bankning bankrot bo'lishi natijasida boshqa banklar kreditlashni keskin kamaytiradilar"},
            {"q":"2008 yilgi jahon moliyaviy-iqtisodiy inqirozi qanday natijaga olib keldi?","opts":["Barcha mamlakatlar valyuta kursini qat'iy belgilashdi", "Bazel'-III nomli yangi bitim yuzaga keldi va 2010 yil 12 sentyabrdan kuchga kirdi", "Tijorat banklari davlat tasarrufiga o'tdi", "XVF yangi valyuta tizimini joriy etdi"],"ans":1,"exp":"To'g'ri javob: A) Bazel'-III nomli yangi bitim yuzaga keldi va 2010 yil 12 sentyabrdan kuchga kirdi"},
            {"q":"2008 yilgi inqirozda AQSh FZTning diskont stavkasi qancha qilib tushirildi?","opts":["0,25 foizgacha", "2 foizgacha", "0,5 foizgacha", "1 foizgacha"],"ans":0,"exp":"To'g'ri javob: A) 0,25 foizgacha"},
            {"q":"2008 yilgi inqirozda AQSh FZT tijorat banklariga qancha kredit berdi?","opts":["1 trln. dollar", "5 trln. dollar", "500 mlrd. dollar", "2 trln. dollar"],"ans":3,"exp":"To'g'ri javob: A) 2 trln. dollar"},
            {"q":"2017 yilda O'zbekiston yirik tijorat banklarining ustav kapitaliga qancha mablag' qo'yildi?","opts":["500 mln. AQSh dollari", "1 mlrd. AQSh dollari", "200 mln. AQSh dollari", "300 mln. AQSh dollari"],"ans":0,"exp":"To'g'ri javob: A) 500 mln. AQSh dollari"},
            {"q":"2017 yilda O'zbekiston tijorat banklarining ustav kapitaliga mablag' qaysi manba hisobidan qo'yildi?","opts":["Xalqaro Valyuta Fondi mablag'lari hisobidan", "O'zbekiston Respublikasining Tiklanish va taraqqiyot jamg'armasi mablag'lari hisobidan", "Jahon Banki mablag'lari hisobidan", "Davlat byudjeti mablag'lari hisobidan"],"ans":1,"exp":"To'g'ri javob: A) O'zbekiston Respublikasining Tiklanish va taraqqiyot jamg'armasi mablag'lari hisobidan"},
            {"q":"Bank inqirozi oqibatlarini bartaraf etish yo'llari qatoriga nima kirmaydi?","opts":["Tijorat banklari faoliyatini nazorat qilish bo'yicha talablarni kuchaytirish", "Muammoli aktivlarni davlat tomonidan sotib olinishi", "Soliq stavkalarini keskin oshirish", "Past diskont stavkalarida kreditlar berish"],"ans":2,"exp":"To'g'ri javob: A) Soliq stavkalarini keskin oshirish"},
            {"q":"1982 yilda Meksika hukumati o'zini bankrot deb e'lon qilganda qanday vaziyat yuzaga keldi?","opts":["AQSh Meksikaga harbiy yordam berdi", "Meksika so'mi keskin qadrsizlandi", "AQSh banklari og'ir ahvolga tushdi, chunki AQSh banklari Meksikaga bergan kreditlari uchun Meksik...", "Meksikaga xorijiy investitsiyalar to'xtadi"],"ans":2,"exp":"To'g'ri javob: A) AQSh banklari og'ir ahvolga tushdi, chunki AQSh banklari Meksikaga bergan kreditlari uchun Meksika hukumati kafolat bergan edi"},
            {"q":"Meksika bank inqirozini hal qilish uchun qancha mablag' oldi?","opts":["Jahon bankidan 2 mlrd. dollar", "XVFdan 5 mlrd. dollar", "AQSh va Yevropa Ittifoqidan 4,5 mlrd. dollar, Yaponiyadan 3,0 mlrd. dollar", "AQShdan 10 mlrd. dollar"],"ans":2,"exp":"To'g'ri javob: A) AQSh va Yevropa Ittifoqidan 4,5 mlrd. dollar, Yaponiyadan 3,0 mlrd. dollar"},
            {"q":"Tijorat banklarining muammoli aktivlarini davlat tomonidan sotib olinishi usuli qaysi mamlakatlarda qo'llanilgan?","opts":["Xitoy, Hindiston, Braziliya", "Yaponiya, Germaniya, AQSh", "Fransiya, Italiya, Ispaniya", "Rossiya, Ukraina, Belarus"],"ans":1,"exp":"To'g'ri javob: A) Yaponiya, Germaniya, AQSh"},
            {"q":"Xalqaro valyuta munosabatlari deganda nima tushuniladi?","opts":["Faqat banklararo to'lovlar", "Valyutalarning jahon iqtisodiyotidagi harakatlari natijasida yuzaga keladigan moliyaviy munosabatlar", "Faqat eksport-import operatsiyalari", "Faqat xalqaro kreditlar"],"ans":1,"exp":"To'g'ri javob: A) Valyutalarning jahon iqtisodiyotidagi harakatlari natijasida yuzaga keladigan moliyaviy munosabatlar"},
            {"q":"Valyuta davlatlararo harakatlanishi uchun qanday shartlar bajarilishi kerak?","opts":["Faqat katta iqtisodiyotga ega mamlakatning valyutasi bo'lishi kerak", "Faqat oltin bilan ta'minlangan bo'lishi kerak", "Faqat XVF a'zo mamlakatlarida muomalada bo'lishi kerak", "Xalqaro to'lov vositasi vazifasini bajara olishi va xalqaro valyuta bozorlarida oldi-sotdi qilini..."],"ans":3,"exp":"To'g'ri javob: A) Xalqaro to'lov vositasi vazifasini bajara olishi va xalqaro valyuta bozorlarida oldi-sotdi qilinishi kerak"},
            {"q":"Hozirgi davrda dunyoda nechta valyuta xalqaro miqyosda to'lov vositasi vazifasini bajara oladi?","opts":["10 ta", "3 ta", "7 ta", "5 ta"],"ans":2,"exp":"To'g'ri javob: A) 7 ta"},
            {"q":"Xalqaro miqyosda to'lov vositasi vazifasini bajara oladigan 7 ta valyuta qatoriga qaysi biri kirmaydi?","opts":["Yaponiya ieni", "Kanada dollari", "AQSh dollari", "Xitoy yuani"],"ans":3,"exp":"To'g'ri javob: A) Xitoy yuani"},
            {"q":"XVFdan xalqaro rezerv valyuta maqomiga ega 5 ta valyuta qatoriga qaysi biri kirmaydi?","opts":["AQSh dollari", "Yaponiya ieni", "Shveysariya franki", "Xitoy yuani"],"ans":2,"exp":"To'g'ri javob: A) Shveysariya franki"},
            {"q":"XVF valyutaga xalqaro rezerv maqomni berish uchun nechta omilni hisobga oladi?","opts":["4 ta omilni", "5 ta omilni", "2 ta omilni", "3 ta omilni"],"ans":0,"exp":"To'g'ri javob: A) 4 ta omilni"},
            {"q":"Xitoy yuani xalqaro rezerv valyuta sifatida qachon tan olindi?","opts":["2005 yil 30 iyunda", "2010 yil 1 yanvardan", "2020 yil 1 martdan", "2015 yil 30 noyabrda"],"ans":3,"exp":"To'g'ri javob: A) 2015 yil 30 noyabrda"},
            {"q":"Erkin ishlatiladigan valyuta deganda nima tushuniladi?","opts":["Faqat oltinga erkin ayirbosh qilinadigan valyuta", "Davlat tomonidan boshqariladigan valyuta", "Faqat xalqaro bozorlarда sotiluvchi valyuta", "To'lov balansining joriy operatsiyalar bo'limida valyutaviy cheklashlar bo'lmagan mamlakatning puli"],"ans":3,"exp":"To'g'ri javob: A) To'lov balansining joriy operatsiyalar bo'limida valyutaviy cheklashlar bo'lmagan mamlakatning puli"},
            {"q":"\"Erkin almashiniladigan valyuta\" nomi qachon \"erkin ishlatiladigan valyuta\" nomiga o'zgartirildi?","opts":["1978 yildan boshlab XVF nomini o'zgartirdi", "1967 yildan boshlab", "1990 yildan boshlab", "1944 yildan boshlab"],"ans":0,"exp":"To'g'ri javob: A) 1978 yildan boshlab XVF nomini o'zgartirdi"},
            {"q":"Yapon ieniga nisbatan qanday koeffitsient qo'llaniladi?","opts":["0,1 koeffitsienti qo'llaniladi", "1 koeffitsienti qo'llaniladi", "100 koeffitsienti qo'llaniladi", "10 koeffitsienti qo'llaniladi"],"ans":3,"exp":"To'g'ri javob: A) 10 koeffitsienti qo'llaniladi"},
            {"q":"AQSh dollari, yevro, funt sterling va boshqa yetakchi valyutalarga qanday koeffitsient qo'llaniladi?","opts":["1 koeffitsienti qo'llaniladi", "0,01 koeffitsienti qo'llaniladi", "100 koeffitsienti qo'llaniladi", "10 koeffitsienti qo'llaniladi"],"ans":0,"exp":"To'g'ri javob: A) 1 koeffitsienti qo'llaniladi"},
            {"q":"Xalqaro valyuta operatsiyalarining asosiy qismi (necha foizdan ortiq) qaysi valyutalar orqali amalga oshiriladi?","opts":["70 foizdan ortiq – barcha erkin valyutalar orqali", "80 foizdan ortiq – xalqaro rezerv valyuta maqomiga ega etakchi valyutalar orqali", "60 foizdan ortiq – yevro orqali", "50 foizdan ortiq – AQSh dollari orqali"],"ans":1,"exp":"To'g'ri javob: A) 80 foizdan ortiq – xalqaro rezerv valyuta maqomiga ega etakchi valyutalar orqali"},
            {"q":"O'zbekiston Respublikasi qonuniga ko'ra valyuta boyliklariga nimalar kiradi?","opts":["Faqat chet el valyutasi", "Faqat xorijiy banklar hisobvaraqlari", "Chet el valyutasi, chet el valyutasidagi qimmatli qog'ozlar, to'lov hujjatlari va sof quyma oltin", "Faqat oltin va qimmatli metallar"],"ans":2,"exp":"To'g'ri javob: A) Chet el valyutasi, chet el valyutasidagi qimmatli qog'ozlar, to'lov hujjatlari va sof quyma oltin"},
            {"q":"Banklararo vakillik munosabatlarining necha turi mavjud?","opts":["4 tur", "2 tur: bir tomonlama va ikki tomonlama", "3 tur", "1 tur"],"ans":1,"exp":"To'g'ri javob: A) 2 tur: bir tomonlama va ikki tomonlama"},
            {"q":"Bir tomonlama vakillik munosabatlarining xususiyati nima?","opts":["Faqat bittasi \"Nostro\" yoki \"Vostro\" vakillik hisobvarag'iga ega bo'ladi", "Ikkala bank ham \"Vostro\" vakillik hisobvarag'iga ega bo'ladi", "Har ikkala bank \"Nostro\" vakillik hisobvarag'iga ega bo'ladi", "Hech qaysi bank vakillik hisobvarag'iga ega emas"],"ans":0,"exp":"To'g'ri javob: A) Faqat bittasi \"Nostro\" yoki \"Vostro\" vakillik hisobvarag'iga ega bo'ladi"},
            {"q":"O'zbekiston Respublikasining tijorat banklari xorijiy banklar bilan qanday vakillik munosabatlariga ega?","opts":["Hech qanday vakillik munosabatlariga ega emas", "Faqat Rossiya banklari bilan vakillik munosabatlariga ega", "Ikki tomonlama vakillik munosabatlariga ega", "Bir tomonlama – respublika banklari xorijiy banklarda \"Nostro\" vakillik hisobvarag'iga ega, xorij..."],"ans":3,"exp":"To'g'ri javob: A) Bir tomonlama – respublika banklari xorijiy banklarda \"Nostro\" vakillik hisobvarag'iga ega, xorijiy banklar esa O'zbekiston banklarida \"Vostro\"ga ega emas"},
            {"q":"Valyuta kurslarining nechta rejimi mavjud?","opts":["2 ta: qat'iy va erkin", "5 ta", "3 ta: qat'iy belgilangan, erkin suzish va boshqariladigan suzish", "4 ta"],"ans":2,"exp":"To'g'ri javob: A) 3 ta: qat'iy belgilangan, erkin suzish va boshqariladigan suzish"},
            {"q":"Jahon valyuta tizimi nima?","opts":["Faqat XVF ning qoidalar to'plami", "Faqat oltin zaxiralarini boshqarish tizimi", "Xalqaro valyuta munosabatlarini tashkil qilishning davlat-huquqiy shakli bo'lib, davlatlararo kel...", "Faqat valyuta kurslarini belgilash mexanizmi"],"ans":2,"exp":"To'g'ri javob: A) Xalqaro valyuta munosabatlarini tashkil qilishning davlat-huquqiy shakli bo'lib, davlatlararo kelishuv natijasida tashkil topadi"},
            {"q":"Birinchi jahon valyuta tizimi qachon va qayerda tashkil topdi?","opts":["1867 yilda Parijda bo'lib o'tgan davlatlararo konferensiyada", "1922 yilda Genuyadа", "1976 yilda Yamaykada", "1944 yilda Bretton-Vudsda"],"ans":0,"exp":"To'g'ri javob: A) 1867 yilda Parijda bo'lib o'tgan davlatlararo konferensiyada"},
            {"q":"Birinchi jahon valyuta tizimining asosiy natijasi nima edi?","opts":["Oltin-moneta standarti joriy qilindi, valyutalar oltinga erkin ayirbosh qilinar edi", "XVF tashkil etildi", "Erkin suzish rejimi joriy qilindi", "Oltin-deviz standarti joriy qilindi"],"ans":0,"exp":"To'g'ri javob: A) Oltin-moneta standarti joriy qilindi, valyutalar oltinga erkin ayirbosh qilinar edi"},
            {"q":"Ikkinchi jahon valyuta tizimi qachon va qayerda tashkil topdi?","opts":["1867 yilda Parijda", "1922 yilda Italiyaning Genuya shahrida", "1944 yilda AQShning Bretton-Vuds shahrida", "1976 yilda Yamaykada"],"ans":1,"exp":"To'g'ri javob: A) 1922 yilda Italiyaning Genuya shahrida"},
            {"q":"Ikkinchi jahon valyuta tizimida qanday standart joriy qilindi?","opts":["Qog'oz pul standarti joriy qilindi", "SDR standarti joriy qilindi", "Oltin-deviz standarti joriy qilindi", "Oltin-moneta standarti joriy qilindi"],"ans":2,"exp":"To'g'ri javob: A) Oltin-deviz standarti joriy qilindi"},
            {"q":"Uchinchi jahon valyuta tizimi (Bretton-Vuds) qachon tashkil topdi?","opts":["1867 yilda Parijda", "1976 yilda Yamaykada", "1922 yilda Genuyadа", "1944 yilda AQShning Bretton-Vuds shahrida"],"ans":3,"exp":"To'g'ri javob: A) 1944 yilda AQShning Bretton-Vuds shahrida"},
            {"q":"Bretton-Vuds tizimida milliy valyuta kursining paritetga nisbatan tebranish yo'lakchasi qancha belgilandi?","opts":["±2%", "±5%", "±0,5%", "±1%"],"ans":3,"exp":"To'g'ri javob: A) ±1%"},
            {"q":"Bretton-Vuds tizimining eng muhim yangiligi nima edi?","opts":["Tarixda birinchi marta davlatlararo valyuta va kredit munosabatlarini tartibga soluvchi organ – X...", "SDR (maxsus qarz olish huquqlari) joriy etildi", "Oltin standarti bekor qilindi", "Erkin suzish rejimi joriy etildi"],"ans":0,"exp":"To'g'ri javob: A) Tarixda birinchi marta davlatlararo valyuta va kredit munosabatlarini tartibga soluvchi organ – Xalqaro valyuta fondi tashkil etildi"},
            {"q":"To'rtinchi jahon valyuta tizimi qachon va qayerda tashkil topdi?","opts":["1922 yilda Genuyadа", "1976-1978 yillarda Yamaykada", "1944 yilda Bretton-Vudsda", "1999 yilda Yevropada"],"ans":1,"exp":"To'g'ri javob: A) 1976-1978 yillarda Yamaykada"},
            {"q":"To'rtinchi jahon valyuta tizimida (Yamayka) oltinni demonetizatsiya qilish nima degani?","opts":["Oltindan davlatlar o'rtasidagi munosabatlarda to'lov vositasi sifatida foydalanish ta'qiqlandi, f...", "Oltin narxi XVF tomonidan belgilanadi", "Oltindan faqat Markaziy banklar foydalanishi mumkin", "Oltin tamoman muomaladan chiqarildi"],"ans":0,"exp":"To'g'ri javob: A) Oltindan davlatlar o'rtasidagi munosabatlarda to'lov vositasi sifatida foydalanish ta'qiqlandi, faqat tezavrlash maqsadlarida ishlatiladi"},
            {"q":"To'rtinchi jahon valyuta tizimida qaysi valyutalarga bosh rezerv valyuta maqomi berildi?","opts":["Fransuz franki va italyan lirasiga", "Faqat AQSh dollariga", "Faqat yevro va funt sterlingga", "Germaniya markasi va Yaponiya ieniga"],"ans":3,"exp":"To'g'ri javob: A) Germaniya markasi va Yaponiya ieniga"},
            {"q":"SDRning valyuta savatida 2016 yildan boshlab Xitoy yuanining ulushi qancha?","opts":["30,93%", "8,09%", "10,92%", "8,33%"],"ans":2,"exp":"To'g'ri javob: A) 10,92%"},
            {"q":"SDRning valyuta savatida 2016 yildan boshlab AQSh dollarining ulushi qancha?","opts":["41,73%", "39%", "44%", "37,4%"],"ans":0,"exp":"To'g'ri javob: A) 41,73%"},
            {"q":"SDRning valyuta savatida 2016 yildan boshlab yevroning ulushi qancha?","opts":["34%", "30,93%", "37,4%", "41,73%"],"ans":1,"exp":"To'g'ri javob: A) 30,93%"},
            {"q":"Xalqaro valyuta munosabatlarining yuzaga kelish asoslarida \"konversion operatsiyalari\" nima?","opts":["Import bo'yicha to'lovni amalga oshirishda va eksport tushumini milliy valyutaga ayirboshlash orq...", "Faqat valyuta kursini hisoblash", "Faqat oltin bilan savdo qilish", "Faqat akkreditiv orqali to'lovlar"],"ans":0,"exp":"To'g'ri javob: A) Import bo'yicha to'lovni amalga oshirishda va eksport tushumini milliy valyutaga ayirboshlash orqali to'lovlarni o'tkazish"},
            {"q":"AQShda oltin zahirasi 2018 yilda qancha tonna edi va u oltin-valyuta zahirasida qancha ulushni egalladi?","opts":["8133,5 tonna, ulushi 75,0%", "3372,2 tonna, ulushi 70,3%", "2436,0 tonna, ulushi 63,4%", "2451,8 tonna, ulushi 67,8%"],"ans":0,"exp":"To'g'ri javob: A) 8133,5 tonna, ulushi 75,0%"},
            {"q":"Rossiyaning oltin zahirasi 2018 yilda qancha edi?","opts":["1054,1 tonna", "788,6 tonna", "384,4 tonna", "1909,8 tonna"],"ans":3,"exp":"To'g'ri javob: A) 1909,8 tonna"},
            {"q":"Xitoyning oltin zahirasi 2018 yilda qancha edi?","opts":["395,0 tonna", "2436,0 tonna", "1054,1 tonna", "1842,6 tonna"],"ans":3,"exp":"To'g'ri javob: A) 1842,6 tonna"},
            {"q":"Valyuta munosabatlari yuzaga kelishi uchun asoslar qatoriga nima kirmaydi?","opts":["Davlatlar o'rtasida grantlarning taqsimlanishi", "Mamlakat ichki savdo aylanmasi", "Tovar va xizmatlarni eksport qilinishi", "Xalqaro kreditlarning olinishi va berilishi"],"ans":1,"exp":"To'g'ri javob: A) Mamlakat ichki savdo aylanmasi"},
            {"q":"Tijorat bankining operatsiyasi deganda nima tushuniladi?","opts":["Faqat pul chiqarish", "Faqat depozit qabul qilish", "Faqat kredit berish jarayoni", "Ma'lum bir bank mahsulotini yaratish maqsadida amalga oshirilgan harakatlar"],"ans":3,"exp":"To'g'ri javob: A) Ma'lum bir bank mahsulotini yaratish maqsadida amalga oshirilgan harakatlar"},
            {"q":"An'anaviy bank mahsulotlariga quyidagilardan qaysi biri kirmaydi?","opts":["Faktoring va forfeyting", "Hisob-kitoblar", "Depozitlar va kreditlar", "Valyuta ayirboshlash"],"ans":0,"exp":"To'g'ri javob: A) Faktoring va forfeyting"},
            {"q":"Noan'anaviy bank mahsulotlariga quyidagilar kiradi:","opts":["Faktoring, forfeyting, trast, kafolat", "Hisob-kitoblar", "Qimmatliklarni saqlash", "Depozitlar va kreditlar"],"ans":0,"exp":"To'g'ri javob: A) Faktoring, forfeyting, trast, kafolat"},
            {"q":"Tijorat bankining passiv operatsiyalari deganda nima tushuniladi?","opts":["Faqat investitsiya operatsiyalari", "Bankning kapitalini shakllantirish va resurslar jalb qilish operatsiyalari", "Faqat kredit berish operatsiyalari", "Faqat valyuta almashtirish"],"ans":1,"exp":"To'g'ri javob: A) Bankning kapitalini shakllantirish va resurslar jalb qilish operatsiyalari"},
            {"q":"Bazel' standartiga ko'ra tijorat bankining regulyativ kapitali nechta qismdan iborat?","opts":["2 qismdan: birinchi va ikkinchi darajali kapital", "3 qismdan", "1 qismdan", "4 qismdan"],"ans":0,"exp":"To'g'ri javob: A) 2 qismdan: birinchi va ikkinchi darajali kapital"},
            {"q":"Dunyoning nechta mamlakatida Bazel' qo'mitasining talablaridan foydalaniladi?","opts":["50 mamlakatda", "150 dan ortiq mamlakatda", "200 mamlakatda", "100 mamlakatda"],"ans":1,"exp":"To'g'ri javob: A) 150 dan ortiq mamlakatda"},
            {"q":"Tijorat banklari birinchi darajali kapitaliga nima kiradi?","opts":["Faqat joriy yil foydasi", "Faqat ustav kapitali", "Faqat zaxira kapitali", "Ustav kapitalining to'langan qismi, qo'shilgan kapital, zaxira kapitali, taqsimlanmagan foyda"],"ans":3,"exp":"To'g'ri javob: A) Ustav kapitalining to'langan qismi, qo'shilgan kapital, zaxira kapitali, taqsimlanmagan foyda"},
            {"q":"Tijorat banklari ikkinchi darajali kapitaliga nima kiradi?","opts":["Faqat ustav kapitali", "Zararlarni qoplash uchun zaxira, subordinatsiyalashgan qarz majburiyatlari, qayta baholash zaxirasi", "Faqat taqsimlanmagan foyda", "Faqat aksiyalar"],"ans":1,"exp":"To'g'ri javob: A) Zararlarni qoplash uchun zaxira, subordinatsiyalashgan qarz majburiyatlari, qayta baholash zaxirasi"},
            {"q":"Tijorat banklarida depozit hisobraqamlarining necha turi mavjud?","opts":["4 tur", "2 tur", "5 tur", "3 tur: talab qilib olinadigan, muddatli, jamg'arma"],"ans":3,"exp":"To'g'ri javob: A) 3 tur: talab qilib olinadigan, muddatli, jamg'arma"},
            {"q":"Talab qilib olinadigan depozitlar AQShda qanday nomlanadi?","opts":["Joriy depozitlar", "Jiro depozitlar", "Depoziti do vostrebovaniya", "Transaksion depozitlar"],"ans":3,"exp":"To'g'ri javob: A) Transaksion depozitlar"},
            {"q":"Talab qilib olinadigan depozitlar Germaniyada qanday nomlanadi?","opts":["Jiro depozitlar", "Muddatli depozitlar", "Joriy depozitlar", "Transaksion depozitlar"],"ans":0,"exp":"To'g'ri javob: A) Jiro depozitlar"},
            {"q":"Depozit bazasining yetarliligini aniqlash formulasi qanday?","opts":["DBE = JD - TQOD", "DBE = (TQOD : JD) x 100%", "DBE = (JD : TQOD) x 100%", "DBE = TQOD + JD"],"ans":1,"exp":"To'g'ri javob: A) DBE = (TQOD : JD) x 100%"},
            {"q":"Agar depozit bazasining yetarliligi ko'rsatkichi qancha bo'lsa, bank depozit bazasi yetarli hisoblanadi?","opts":["30 foizdan oshmasa", "10 foizdan oshmasa", "70 foizdan oshmasa", "50 foizdan oshmasa"],"ans":0,"exp":"To'g'ri javob: A) 30 foizdan oshmasa"},
            {"q":"Tijorat banklari qimmatli qog'ozlar bozorida qanday rollarda ishtirok etadi?","opts":["Emitent, investor va vositachi sifatida", "Faqat vositachi sifatida", "Faqat emitent sifatida", "Faqat investor sifatida"],"ans":0,"exp":"To'g'ri javob: A) Emitent, investor va vositachi sifatida"},
            {"q":"Tijorat banklarining bir emitentning qimmatli qog'ozlariga qilgan investitsiyalari birinchi darajali kapitalning necha foizidan oshmasligi kerak?","opts":["25 foizidan", "10 foizidan", "50 foizidan", "15 foizidan"],"ans":3,"exp":"To'g'ri javob: A) 15 foizidan"},
            {"q":"Tijorat bankining oldi-sotdi uchun mo'ljallangan qimmatli qog'ozlarga investitsiyalari birinchi darajali kapitalning necha foizidan oshmasligi kerak?","opts":["25 foizidan", "30 foizidan", "15 foizidan", "50 foizidan"],"ans":0,"exp":"To'g'ri javob: A) 25 foizidan"},
            {"q":"Tijorat bankining barcha emitentlarning qimmatli qog'ozlariga jami investitsiyalari birinchi darajali kapitalning necha foizidan oshmasligi kerak?","opts":["25 foizidan", "75 foizidan", "50 foizidan", "15 foizidan"],"ans":2,"exp":"To'g'ri javob: A) 50 foizidan"},
            {"q":"Tijorat banklarining aktiv operatsiyalari turiga nima kirmaydi?","opts":["Kredit (ssuda) operatsiyalari", "Kassa operatsiyalari", "Investitsion operatsiyalar", "Ustav kapitalini shakllantirish"],"ans":3,"exp":"To'g'ri javob: A) Ustav kapitalini shakllantirish"},
            {"q":"Investitsion operatsiyalar nima maqsadda amalga oshiriladi?","opts":["Daromad olish va likvidlikni ta'minlash maqsadida", "Faqat daromad olish maqsadida", "Faqat likvidlikni ta'minlash maqsadida", "Faqat xavfni kamaytirish maqsadida"],"ans":0,"exp":"To'g'ri javob: A) Daromad olish va likvidlikni ta'minlash maqsadida"},
            {"q":"Kassa operatsiyalari nima?","opts":["Investitsiya operatsiyalari", "Valyuta almashtirish operatsiyalari", "Kredit berish operatsiyalari", "Naqd pullarni qabul qilish va berish operatsiyalari"],"ans":3,"exp":"To'g'ri javob: A) Naqd pullarni qabul qilish va berish operatsiyalari"},
            {"q":"Tijorat banklari qanday valyuta operatsiyalarini bajaradi?","opts":["Faqat forvard operatsiyalar", "Faqat spot operatsiyalar", "Spot, muddatli (forvard, opsion, fyuchers) va svop operatsiyalari", "Faqat svop operatsiyalar"],"ans":2,"exp":"To'g'ri javob: A) Spot, muddatli (forvard, opsion, fyuchers) va svop operatsiyalari"},
            {"q":"Hisob-kitob operatsiyalari deganda nima tushuniladi?","opts":["Faqat pul kiritish", "Faqat to'lov amalga oshirish", "Miiozlarning hisobvaraqlariga pul kiritish va to'lovlarni amalga oshirish", "Faqat valyuta almashtirish"],"ans":2,"exp":"To'g'ri javob: A) Miiozlarning hisobvaraqlariga pul kiritish va to'lovlarni amalga oshirish"},
            {"q":"Banklar tomonidan beriladigan kafolatlarning necha turi mavjud?","opts":["4 tur", "1 tur", "2 tur: to'lov majburiyatlari va tovarlar sifati bo'yicha", "3 tur"],"ans":2,"exp":"To'g'ri javob: A) 2 tur: to'lov majburiyatlari va tovarlar sifati bo'yicha"},
            {"q":"Anderrayting operatsiyasi nima?","opts":["Bank mijozlarning topshirig'i bilan qimmatli qog'ozlarni o'z nomidan bozorga joylashtirishi", "Valyuta almashtirish", "Depozit qabul qilish", "Kredit berish operatsiyasi"],"ans":0,"exp":"To'g'ri javob: A) Bank mijozlarning topshirig'i bilan qimmatli qog'ozlarni o'z nomidan bozorga joylashtirishi"},
            {"q":"\"Inflyasiya\" so'zi qaysi tildan olingan va nima ma'noni anglatadi?","opts":["Italyancha \"inflazione\" – qadrsizlanish", "Inglizcha \"inflation\" – narx oshishi", "Fransuzcha \"inflation\" – pul muomalasi", "Lotincha \"inflatio\" – ko'pchish, bo'rtish"],"ans":3,"exp":"To'g'ri javob: A) Lotincha \"inflatio\" – ko'pchish, bo'rtish"},
            {"q":"Inflyasiya nima?","opts":["Faqat narxlarning oshishi", "Muomaladagi pul massasining ko'payishi natijasida pulning qadrsizlanishi", "Faqat eksportning kamayishi", "Faqat ishlab chiqarishning pasayishi"],"ans":1,"exp":"To'g'ri javob: A) Muomaladagi pul massasining ko'payishi natijasida pulning qadrsizlanishi"},
            {"q":"K. Marks inflyasiya haqida nima degan?","opts":["Inflyasiyaning sababi faqat davlat byudjeti defisiti", "Tovarlar baholarining oshishi natijasida pul massasi ko'payadi va pul qadrsizlanadi", "Pul massasining ko'payishi narxlarni oshiradi", "Inflyasiya faqat urush davrida yuzaga keladi"],"ans":1,"exp":"To'g'ri javob: A) Tovarlar baholarining oshishi natijasida pul massasi ko'payadi va pul qadrsizlanadi"},
            {"q":"M. Fridmen inflyasiya haqida nima degan?","opts":["Inflyasiya faqat moliyaviy inqirozlarda bo'ladi", "Muomaladagi pullarning ko'payishi tovarlar baholarining oshishiga olib keladi", "Inflyasiyaning sababi faqat ish haqining oshishi", "Narxlarning oshishi pul massasini ko'paytiradi"],"ans":1,"exp":"To'g'ri javob: A) Muomaladagi pullarning ko'payishi tovarlar baholarining oshishiga olib keladi"},
            {"q":"Inflyasiyaning namoyon bo'lish shakllariga nima kirmaydi?","opts":["Milliy pul tovarlar va xizmatlarga nisbatan qadrsizlanishi", "Milliy pul xorijiy valyutalarga nisbatan qadrsizlanishi", "Milliy valyuta oltinga nisbatan qadrsizlanishi", "Milliy pulning oltin zahiralariga nisbatan qadrsizlanishi"],"ans":3,"exp":"To'g'ri javob: A) Milliy pulning oltin zahiralariga nisbatan qadrsizlanishi"},
            {"q":"Talab inflyasiyasi qachon yuzaga keladi?","opts":["Ish haqi oshganda", "Tovarlar ishlab chiqarish ularga bo'lgan talabni qondira olmasa, pul taklifi keskin oshsa", "Import qimmatlashganda", "Ishlab chiqarish xarajatlari oshib ketganda"],"ans":1,"exp":"To'g'ri javob: A) Tovarlar ishlab chiqarish ularga bo'lgan talabni qondira olmasa, pul taklifi keskin oshsa"},
            {"q":"Taklif (chiqim) inflyasiyasi nima bilan bog'liq?","opts":["Tovarlarni ishlab chiqarish uchun zarur xarajatlarning oshib ketishi bilan", "Talab oshishi bilan", "Import kamayishi bilan", "Pul emissiyasi bilan"],"ans":0,"exp":"To'g'ri javob: A) Tovarlarni ishlab chiqarish uchun zarur xarajatlarning oshib ketishi bilan"},
            {"q":"XVF ekspertlariga ko'ra qanday inflyasiya mo'tadil hisoblanadi?","opts":["Yillik darajasi 5 foizdan oshmasa", "Yillik darajasi 3 foizdan oshmasa", "Yillik darajasi 10 foizdan oshmasa", "Yillik darajasi 1 foizdan oshmasa"],"ans":1,"exp":"To'g'ri javob: A) Yillik darajasi 3 foizdan oshmasa"},
            {"q":"Yevrohudud mamlakatlari uchun inflyasiyaning yillik sur'ati qancha bo'lishi kerak?","opts":["5 foizdan oshmasligi kerak", "3 foizdan oshmasligi kerak", "1 foizdan oshmasligi kerak", "2 foizdan oshmasligi kerak"],"ans":3,"exp":"To'g'ri javob: A) 2 foizdan oshmasligi kerak"},
            {"q":"Sudraluvchi inflyasiyada baholarning yillik o'sish sur'ati qancha?","opts":["5 foizdan 10 foizgacha", "3 foizdan 5 foizgacha", "10 foizdan 50 foizgacha", "50 foizdan yuqori"],"ans":0,"exp":"To'g'ri javob: A) 5 foizdan 10 foizgacha"},
            {"q":"Yo'rg'alovchi inflyasiyada baholarning yillik o'sish sur'ati qancha?","opts":["50 foizdan 100 foizgacha", "10 foizdan 50 foizgacha", "3 foizdan 10 foizgacha", "100 foizdan yuqori"],"ans":1,"exp":"To'g'ri javob: A) 10 foizdan 50 foizgacha"},
            {"q":"Giperinflyasiyada tovarlar baholarining oylik o'sish sur'ati qancha?","opts":["25 foizga yetadi", "50 foizga yetadi va undan oshadi (yillik 600 foiz)", "100 foizga yetadi", "10 foizga yetadi"],"ans":1,"exp":"To'g'ri javob: A) 50 foizga yetadi va undan oshadi (yillik 600 foiz)"},
            {"q":"Germaniyada 1923 yildagi giperinflyasiyada narxlar necha martaga oshdi?","opts":["1,3 trillion martaga", "100 ming martaga", "1 million martaga", "1 milliard martaga"],"ans":0,"exp":"To'g'ri javob: A) 1,3 trillion martaga"},
            {"q":"Germaniyada 1923 yilda pul islohoti paytida nisbat qanday edi?","opts":["1 yangi marka = 100 million eski marka", "1 yangi marka = 1 trillion eski marka", "1 yangi marka = 1 milliard eski marka", "1 yangi marka = 1 million eski marka"],"ans":1,"exp":"To'g'ri javob: A) 1 yangi marka = 1 trillion eski marka"},
            {"q":"Lokal inflyasiya nima?","opts":["Tovarlar bilan birga eksport qilinadigan inflyasiya", "Alohida bitta davlatda yoki bitta hududda yuzaga kelgan inflyasiya", "Yashirincha yuz beradigan inflyasiya", "Bir nechta mamlakatda bir vaqtda yuz beradigan inflyasiya"],"ans":1,"exp":"To'g'ri javob: A) Alohida bitta davlatda yoki bitta hududda yuzaga kelgan inflyasiya"},
            {"q":"Jahon inflyasiyasi nima?","opts":["Bitta mamlakatda yuz beradigan inflyasiya", "Import orqali kirib keladigan inflyasiya", "Eksport orqali tarqaladigan inflyasiya", "Bir vaqtning o'zida bir nechta mamlakatda yuz beradigan inflyasiya"],"ans":3,"exp":"To'g'ri javob: A) Bir vaqtning o'zida bir nechta mamlakatda yuz beradigan inflyasiya"},
            {"q":"1985 yilda AQSh va Yaponiya savdo urushining sababi nima edi?","opts":["Valyuta kursi farqi", "Import kvotasi muammosi", "Inflyasiya darajalari o'rtasidagi farq – inflyasiya AQShda Yaponiyaga nisbatan yuqori edi", "Soliq siyosatidagi farq"],"ans":2,"exp":"To'g'ri javob: A) Inflyasiya darajalari o'rtasidagi farq – inflyasiya AQShda Yaponiyaga nisbatan yuqori edi"},
            {"q":"Inflyasiyaning ijtimoiy oqibatlariga nima kirmaydi?","opts":["Aholining turmush darajasi pasayishi", "YaIMning o'sishi sekinlashishi", "Ishsizlik darajasining oshishi", "Aholining bank jamg'armalari qadrsizlanishi"],"ans":1,"exp":"To'g'ri javob: A) YaIMning o'sishi sekinlashishi"},
            {"q":"Inflyasiyaning iqtisodiy oqibatlariga nima kiradi?","opts":["Korxonalarning moliyaviy barqarorligi pasayishi, amortizasiya real qiymatining pasayishi", "Aholining turmush darajasi pasayishi", "Banklar ishonchining pasayishi", "Ishsizlikning oshishi"],"ans":0,"exp":"To'g'ri javob: A) Korxonalarning moliyaviy barqarorligi pasayishi, amortizasiya real qiymatining pasayishi"},
            {"q":"Inflyasion targetlash rejimi nimani nazarda tutadi?","opts":["Faqat pul massasini cheklash", "Faqat foiz stavkasini oshirish", "Faqat maqsadni belgilash", "Maqsadli ko'rsatkichni belgilash, muddatini belgilash va OAVda e'lon qilish"],"ans":3,"exp":"To'g'ri javob: A) Maqsadli ko'rsatkichni belgilash, muddatini belgilash va OAVda e'lon qilish"},
            {"q":"Inflyasion targetlashni muvaffaqiyatli qo'llagan davlatlar qatoriga qaysi kirmaydi?","opts":["Buyuk Britaniya", "Yangi Zelandiya", "Xitoy", "Kanada"],"ans":2,"exp":"To'g'ri javob: A) Xitoy"},
            {"q":"Qaysi mamlakatlarda inflyasiyaning maqsadli ko'rsatkichi Markaziy bank va Moliya vazirligining kelishuvi asosida ishlab chiqildi?","opts":["Avstraliya va Finlandiya", "Buyuk Britaniya va Fransiya", "Shvesiya va Ispaniya", "Kanada va Yangi Zelandiya"],"ans":3,"exp":"To'g'ri javob: A) Kanada va Yangi Zelandiya"},
            {"q":"Kanada va Yangi Zelandiyada maqsadli ko'rsatkichga erishish uchun qancha muddat belgilandi?","opts":["24 oylik muddat", "6 oylik muddat", "18 oylik muddat", "12 oylik muddat"],"ans":2,"exp":"To'g'ri javob: A) 18 oylik muddat"},
            {"q":"Davlat byudjeti defisiti YaIMga nisbatan qancha foizdan oshmasligi kerak?","opts":["5 foizdan oshmasligi kerak", "1 foizdan oshmasligi kerak", "10 foizdan oshmasligi kerak", "3 foizdan oshmasligi kerak"],"ans":3,"exp":"To'g'ri javob: A) 3 foizdan oshmasligi kerak"},
            {"q":"Byudjet defisitining YaIMdagi ulushini 1 foizli punktga qisqarishi inflyasiyani qancha pasaytiradi?","opts":["10 foizli punktga", "5 foizli punktga", "3 foizli punktga", "8,75 foizli punktga"],"ans":3,"exp":"To'g'ri javob: A) 8,75 foizli punktga"},
            {"q":"Yevropa Markaziy banki qaysi pul agregatining o'sishini nazorat qiladi?","opts":["M3 pul agregatini", "M0 pul agregatini", "M1 pul agregatini", "M2 pul agregatini"],"ans":0,"exp":"To'g'ri javob: A) M3 pul agregatini"},
            {"q":"AQSh, Rossiya, Qozog'iston va O'zbekiston Markaziy banklari qaysi pul agregatini nazorat qiladi?","opts":["M4 pul agregatini", "M1 pul agregatini", "M3 pul agregatini", "M2 pul agregatini"],"ans":3,"exp":"To'g'ri javob: A) M2 pul agregatini"},
            {"q":"Ish haqining o'sishini cheklash usuli qaysi mamlakatlarda muammo keltirib chiqargan?","opts":["Hindiston va Xitoyda", "Meksika va Pol'shada fuqarolar chet elga ishlashga ketishgan", "Fransiya va Germaniyada", "Rossiya va Ukrainada"],"ans":1,"exp":"To'g'ri javob: A) Meksika va Pol'shada fuqarolar chet elga ishlashga ketishgan"},
            {"q":"O'zbekiston milliy valyutasi – so'm qachon muomalaga kiritilgan?","opts":["1994 yilning 1 iyulidan", "1995 yil 1 yanvardan", "1991 yil 1 sentyabrdan", "1992 yil 1 iyulidan"],"ans":0,"exp":"To'g'ri javob: A) 1994 yilning 1 iyulidan"},
            {"q":"O'zbekiston dastlab rubl' hududida qolishining sabablari qatoriga nima kirmaydi?","opts":["Rossiyadan importni rublda to'lash zaruriyati", "Ikki pog'onali bank tizimi mavjud emasligi", "Pul muomalasini boshqarish tajribasining yo'qligi", "Milliy valyuta etarli miqdorda tayyorlanmagan edi"],"ans":3,"exp":"To'g'ri javob: A) Milliy valyuta etarli miqdorda tayyorlanmagan edi"},
            {"q":"O'zbekistonda so'mning valyuta pariteti qaysi valyutaga nisbatan aniqlanadi?","opts":["AQSh dollariga nisbatan", "Rossiya rubliga nisbatan", "Xitoy yuaniga nisbatan", "Yevro nisbatan"],"ans":0,"exp":"To'g'ri javob: A) AQSh dollariga nisbatan"},
            {"q":"O'zbekiston Respublikasi Prezidentining 2017 yil 2 sentyabrdagi PF-5177-sonli farmoniga muvofiq qanday o'zgarish bo'ldi?","opts":["Yagona valyuta zonasi tashkil etildi", "Valyuta siyosati liberallashtirildi, milliy valyuta kursi bozor mexanizmlari orqali belgilanadi", "So'm oltin bilan ta'minlandi", "Xorijiy valyuta muomaladan chiqarildi"],"ans":1,"exp":"To'g'ri javob: A) Valyuta siyosati liberallashtirildi, milliy valyuta kursi bozor mexanizmlari orqali belgilanadi"},
            {"q":"O'zbekistonda tijorat banklari o'rtasidagi barcha to'lovlar nima orqali o'tadi?","opts":["Xalqaro banklar orqali", "Markaziy bank orqali, chunki tijorat banklarining nostro vakillik hisobvaraqlari Markaziy bankda ...", "Davlat xazinachiligi orqali", "Kliring markazi orqali"],"ans":1,"exp":"To'g'ri javob: A) Markaziy bank orqali, chunki tijorat banklarining nostro vakillik hisobvaraqlari Markaziy bankda ochilgan"},
            {"q":"O'zbekistonda naqd pulsiz hisob-kitoblarda to'lov topshiriqnomalari qancha ulushni egallaydi?","opts":["50,1%", "30%", "20%", "70%"],"ans":0,"exp":"To'g'ri javob: A) 50,1%"},
            {"q":"\"Markaziy bank to'g'risida\"gi qonunning 32-moddasiga ko'ra milliy pul tizimi nimalardan iborat?","opts":["Bank tizimi va pul muomalasi", "Pul birligi, pul muomalasini tashkil etish va tartibga solish", "Faqat pul birligi", "Faqat pul muomalasi"],"ans":1,"exp":"To'g'ri javob: A) Pul birligi, pul muomalasini tashkil etish va tartibga solish"},
            {"q":"O'zbekistonda qanday to'lovlar ketma-ketligi qo'llaniladi?","opts":["To'lovlarning kalendar' ketma-ketligi", "To'lovlarning maqsadli ketma-ketligi", "To'lovlarning tartib raqami bo'yicha ketma-ketligi", "To'lovlarning hajm bo'yicha ketma-ketligi"],"ans":1,"exp":"To'g'ri javob: A) To'lovlarning maqsadli ketma-ketligi"},
            {"q":"2017-2021 yillarda O'zbekistonni rivojlantirishning Harakatlar strategiyasida pul tizimi bo'yicha qanday vazifalar belgilangan?","opts":["Faqat naqd pullarni qisqartirish", "Faqat oltin zaxiralarini oshirish", "Pul-kredit siyosatini takomillashtirish, valyutani tartibga solishda bozor mexanizmlari joriy etish", "Faqat inflyasiyani pasaytirish"],"ans":2,"exp":"To'g'ri javob: A) Pul-kredit siyosatini takomillashtirish, valyutani tartibga solishda bozor mexanizmlari joriy etish"},
            {"q":"Naqdsiz pul aylanmasi nima?","opts":["Faqat Markaziy bank operatsiyalari", "Faqat xorijiy valyuta operatsiyalari", "Faqat naqd pullarni ko'chirish", "Pul mablag'larini tijorat banklaridagi hisobvaraqlar bo'yicha ko'chirish va o'zaro talablarni voz..."],"ans":3,"exp":"To'g'ri javob: A) Pul mablag'larini tijorat banklaridagi hisobvaraqlar bo'yicha ko'chirish va o'zaro talablarni voz kechish"},
            {"q":"Naqdsiz pul aylanmasini tashkil qilish prinsiplari qatoriga nima kirmaydi?","opts":["To'lovchining roziligi bilan to'lovlar amalga oshirilishi", "To'lovlarning muddatliligi", "Naqd pullar miqdorini belgilash printsipi", "Qonunchilik asoslarining mavjudligi"],"ans":2,"exp":"To'g'ri javob: A) Naqd pullar miqdorini belgilash printsipi"},
            {"q":"Naqd pulsiz hisob-kitob shakllariga nima kirmaydi?","opts":["Akkreditiv", "Chek", "To'lov topshiriqnomasi", "Veksel"],"ans":3,"exp":"To'g'ri javob: A) Veksel"},
            {"q":"2020 yil holatiga ko'ra muomаladagi naqd pullar tarkibida 50 000 so'mlik banknotalar qancha ulushni tashkil etgan?","opts":["27,3 foiz", "15,7 foiz", "38,8 foiz", "16,1 foiz"],"ans":2,"exp":"To'g'ri javob: A) 38,8 foiz"},
            {"q":"2020 yil holatiga ko'ra muomаladagi naqd pullar tarkibida 100 000 so'mlik banknotalar qancha ulushni tashkil etgan?","opts":["27,3 foiz", "38,8 foiz", "16,1 foiz", "15,7 foiz"],"ans":0,"exp":"To'g'ri javob: A) 27,3 foiz"},
            {"q":"Pul islohoti nima?","opts":["Faqat yangi pullar chiqarish", "Faqat eski pullarni muomaladan chiqarish", "Davlat tomonidan pul muomalasini tartibga solish va pul tizimini mustahkamlash maqsadida amalga o...", "Faqat valyuta kursini o'zgartirish"],"ans":2,"exp":"To'g'ri javob: A) Davlat tomonidan pul muomalasini tartibga solish va pul tizimini mustahkamlash maqsadida amalga oshiriladigan chora-tadbirlar yig'indisi"},
            {"q":"Pul islohotini amalga oshirish zarurligi sabablariga nima kirmaydi?","opts":["Texnologiyalarni rivojlantirish zarurligi", "Inflyasiya ta'sirida pul muomalasining izdan chiqishi", "Yangi davlatning paydo bo'lishi", "Yagona valyutaga asoslangan iqtisodiy hududning paydo bo'lishi"],"ans":0,"exp":"To'g'ri javob: A) Texnologiyalarni rivojlantirish zarurligi"},
            {"q":"Sobiq SSSR o'rnida nechta mustaqil davlat paydo bo'ldi?","opts":["12 ta", "10 ta", "15 ta", "20 ta"],"ans":2,"exp":"To'g'ri javob: A) 15 ta"},
            {"q":"Sobiq Yugoslaviya o'rnida nechta mustaqil davlat paydo bo'ldi?","opts":["7 ta", "5 ta", "3 ta", "10 ta"],"ans":0,"exp":"To'g'ri javob: A) 7 ta"},
            {"q":"Naqd pulsiz yevro qachondan muomalaga kiritildi?","opts":["2000 yil 1 yanvardan", "1998 yil 1 yanvardan", "1999 yil 1 yanvardan", "2002 yil 1 yanvardan"],"ans":2,"exp":"To'g'ri javob: A) 1999 yil 1 yanvardan"},
            {"q":"Naqd yevro qachondan muomalaga kiritildi?","opts":["2001 yil 1 yanvardan", "1999 yil 1 yanvardan", "2000 yil 1 yanvardan", "2002 yil 1 yanvardan"],"ans":3,"exp":"To'g'ri javob: A) 2002 yil 1 yanvardan"},
            {"q":"Hozirgi kunda yevrohududga nechta davlat a'zo?","opts":["19 ta", "15 ta", "27 ta", "12 ta"],"ans":0,"exp":"To'g'ri javob: A) 19 ta"},
            {"q":"Pul islohotini muvaffaqiyatli amalga oshirish shartlariga nima kirmaydi?","opts":["Mamlakatda siyosiy barqarorlik bo'lishi", "Aholining bankka ishonchi yuqori bo'lishi", "Milliy valyuta kursining barqarorligi", "Tovarlar ishlab chiqarish hajmining o'sishi"],"ans":1,"exp":"To'g'ri javob: A) Aholining bankka ishonchi yuqori bo'lishi"},
            {"q":"Denominatsiya nima?","opts":["Milliy valyutaning xorijiy valyutaga nisbatan qadrsizlanishi", "Milliy valyuta qiymatining rasmiy ko'tarilishi", "Pulni muomaladan butunlay olib tashlash", "Pul nominalini pasaytirish, eski pulning yangi pulga ma'lum nisbatda almashtirilishi"],"ans":3,"exp":"To'g'ri javob: A) Pul nominalini pasaytirish, eski pulning yangi pulga ma'lum nisbatda almashtirilishi"},
            {"q":"Nullifikatsiya nima?","opts":["Eski pul belgilarini muomaladan olish va ozroq miqdorda yangilarini chiqarish", "Pul nominalini pasaytirish", "Pul massasini ko'paytirish", "Milliy valyuta kursini rasmiy ko'tarish"],"ans":0,"exp":"To'g'ri javob: A) Eski pul belgilarini muomaladan olish va ozroq miqdorda yangilarini chiqarish"},
            {"q":"Revalvatsiya nima?","opts":["Pul nominalini kamaytirish", "Milliy pul birligi qiymatining rasmiy tartibda xorijiy valyuta yoki metallga nisbatan ko'tarilishi", "Milliy pul birligi qiymatining pasayishi", "Yangi valyuta kiritish"],"ans":1,"exp":"To'g'ri javob: A) Milliy pul birligi qiymatining rasmiy tartibda xorijiy valyuta yoki metallga nisbatan ko'tarilishi"},
            {"q":"Devalvatsiya nima?","opts":["Pul birligi qiymatining rasmiy ko'tarilishi", "Pul nominalini kamaytirish", "Pul birligi qiymatining rasmiy tartibda xorijiy valyuta yoki metallga nisbatan pasaytirilishi", "Yangi pul chiqarish"],"ans":2,"exp":"To'g'ri javob: A) Pul birligi qiymatining rasmiy tartibda xorijiy valyuta yoki metallga nisbatan pasaytirilishi"},
            {"q":"Tarixdagi eng katta denominatsiya qaysi mamlakatda o'tkazilgan?","opts":["1946 yili Vengriyada – 400 oktillion penge 1 forintga almashtirilgan", "1923 yili Germaniyada", "1993 yili Rossiyada", "1944 yili Gretsiyada"],"ans":0,"exp":"To'g'ri javob: A) 1946 yili Vengriyada – 400 oktillion penge 1 forintga almashtirilgan"},
            {"q":"Rossiyada 1922-23 yillarda denominatsiya qanday nisbatda o'tkazilgan?","opts":["100 rubl – 1 yangi rublga", "1 milliard rubl – 1 yangi rublga", "1 ming rubl – 1 yangi rublga", "1 million rubl – 1 yangi rublga"],"ans":3,"exp":"To'g'ri javob: A) 1 million rubl – 1 yangi rublga"},
            {"q":"Gretsiyada 1944 yil noyabrda denominatsiya qanday nisbatda o'tkazilgan?","opts":["1 million draxma – 1 yangi draxmaga", "50 milliard draxma – 1 yangi draxmaga", "100 million draxma – 1 yangi draxmaga", "1 milliard draxma – 1 yangi draxmaga"],"ans":1,"exp":"To'g'ri javob: A) 50 milliard draxma – 1 yangi draxmaga"},
            {"q":"Vatanimizdagi ilk denominatsiya qachon va qayerda bo'lgan?","opts":["1918 yili Samarqandda", "1920 yili Farg'onada", "1922 yili Buxoroda – pulning nominali yuz marta kamaytirilgan", "1924 yili Toshkentda"],"ans":2,"exp":"To'g'ri javob: A) 1922 yili Buxoroda – pulning nominali yuz marta kamaytirilgan"},
            {"q":"O'zbekistonda so'm-kupon qachon muomaladan chiqarilgan?","opts":["1994 yil 1 avgustdan – 1000:1 nisbatda so'mga almashtirilgan", "1992 yil 1 sentyabrdan", "1993 yil 1 yanvardan", "1995 yil 1 iyuldan"],"ans":0,"exp":"To'g'ri javob: A) 1994 yil 1 avgustdan – 1000:1 nisbatda so'mga almashtirilgan"},
            {"q":"1993 yilda O'zbekistonda inflyasiyaning yillik darajasi qancha bo'lgan?","opts":["100 foiz bo'lgan", "200 foiz bo'lgan", "1000 (ming) foizdan oshgan", "500 foiz bo'lgan"],"ans":2,"exp":"To'g'ri javob: A) 1000 (ming) foizdan oshgan"},
            {"q":"Deinflyasion siyosat nimani o'z ichiga oladi?","opts":["Faqat pul massasini kamaytirish", "Faqat foiz stavkasini oshirish", "Faqat soliqlarni ko'paytirish", "Davlat xarajatlarini qisqartirish, foiz stavkalarini oshirish, soliq yukini kuchaytirish, pul mas..."],"ans":3,"exp":"To'g'ri javob: A) Davlat xarajatlarini qisqartirish, foiz stavkalarini oshirish, soliq yukini kuchaytirish, pul massasini cheklash"},
            {"q":"Daromadlar siyosati nima?","opts":["Narx-navo va ish haqi ustidan davlat nazorati va ularning o'sishini cheklash yoki \"muzlatish\"", "Faqat soliqlarni oshirish", "Faqat narxlarni belgilash", "Faqat ish haqini cheklash"],"ans":0,"exp":"To'g'ri javob: A) Narx-navo va ish haqi ustidan davlat nazorati va ularning o'sishini cheklash yoki \"muzlatish\""},
            {"q":"Kredit so'zi lotincha qaysi so'zdan olingan?","opts":["\"Creditum\" – ssuda, qarz; ayrimlari \"credo\" – ishonaman deydi", "\"Credere\" – bermoq", "\"Creditor\" – ssuda beruvchi", "\"Credibilis\" – ishonchli"],"ans":0,"exp":"To'g'ri javob: A) \"Creditum\" – ssuda, qarz; ayrimlari \"credo\" – ishonaman deydi"},
            {"q":"Kreditning boshqa iqtisodiy kategoriyalar bilan aloqadorligining uchinchi sababi nima?","opts":["Ular bir xil muddatga beriladi", "Ular bozor munosabatlari doirasida amal qiladi va bozor qonunlariga bo'ysunadi", "Ularning hammasi davlat tomonidan tartibga solinadi", "Ular bir xil sub'ektlarga tegishli"],"ans":1,"exp":"To'g'ri javob: A) Ular bozor munosabatlari doirasida amal qiladi va bozor qonunlariga bo'ysunadi"},
            {"q":"Kreditning ahamiyatini belgilovchi omillarga nima kirmaydi?","opts":["Kredit inflyasiyani to'liq yo'q qiladi", "Kredit xo'jalik yurituvchi sub'ektlar faoliyatini rivojlantirish imkonini beradi", "Kredit aholining turmush farovonligini oshirish imkonini beradi", "Kredit iqtisodiyotdagi to'lovlar uzluksizligini ta'minlaydi"],"ans":0,"exp":"To'g'ri javob: A) Kredit inflyasiyani to'liq yo'q qiladi"},
            {"q":"Kredit va pul o'rtasidagi asosiy farq nima?","opts":["Kreditda qiymat qarama-qarshi harakatda bo'lmaydi, qarz oluvchi ma'lum muddatdan so'ng qaytaradi", "Pul ham kredit hisoblanadi", "Kredit faqat banklararo beriladi", "Kredit faqat pul shaklida beriladi"],"ans":0,"exp":"To'g'ri javob: A) Kreditda qiymat qarama-qarshi harakatda bo'lmaydi, qarz oluvchi ma'lum muddatdan so'ng qaytaradi"},
            {"q":"Kredit va moliya o'rtasidagi asosiy farq nima?","opts":["Kredit mablag'larining egasi o'zgarmaydi (kreditor mулкдор saqlanadi), moliyada mablag' egasi o'z...", "Kredit faqat pulda, moliya faqat tovarda bo'ladi", "Kredit davlat tomonidan, moliya xususiy sektorda beriladi", "Kredit qaytarilmaydi, moliya qaytariladi"],"ans":0,"exp":"To'g'ri javob: A) Kredit mablag'larining egasi o'zgarmaydi (kreditor mулкдор saqlanadi), moliyada mablag' egasi o'zgaradi"},
            {"q":"Ссуда фонди нима?","opts":["Markaziy bankning aktivlari", "Jamiyatdagi qarzga beriluvchi qiymatning maqsadga yo'naltirilgan harakati bilan bog'liq ishlab ch...", "Faqat banklarning zaxiralari", "Davlatning qarz mablag'lari"],"ans":1,"exp":"To'g'ri javob: A) Jamiyatdagi qarzga beriluvchi qiymatning maqsadga yo'naltirilgan harakati bilan bog'liq ishlab chiqarish munosabatlari majmuasi"},
            {"q":"Professor Sh.Abdullaeva ta'rifiga ko'ra kredit nima?","opts":["Shartnomasiz berilgan pul mablag'lari", "Vaqtincha bo'sh turgan pul mablag'larini ma'lum muddatga, haq to'lash sharti bilan qarzga olish v...", "Faqat bank tomonidan beriladigan ssuda", "Davlat tomonidan beriladigan subsidiya"],"ans":1,"exp":"To'g'ri javob: A) Vaqtincha bo'sh turgan pul mablag'larini ma'lum muddatga, haq to'lash sharti bilan qarzga olish va qaytarib berish yuzasidan kelib chiqqan munosabatlar"},
            {"q":"Kredit tamoyillariga nima kiradi?","opts":["Qaytarishlik, to'lovlilik, ta'minlanganlik, muddatlilik va maqsadlilik", "Faqat qaytarishlik va muddatlilik", "Faqat to'lovlilik va ta'minlanganlik", "Faqat maqsadlilik"],"ans":0,"exp":"To'g'ri javob: A) Qaytarishlik, to'lovlilik, ta'minlanganlik, muddatlilik va maqsadlilik"},
            {"q":"Kreditning funksiyalariga nima kiradi?","opts":["Faqat nazorat qilish", "Faqat kredit berish", "Faqat pul chiqarish", "Qayta taqsimlash, haqiqiy pullarni kredit operatsiyalari bilan almashtirish, muomala xarajatlarin..."],"ans":3,"exp":"To'g'ri javob: A) Qayta taqsimlash, haqiqiy pullarni kredit operatsiyalari bilan almashtirish, muomala xarajatlarini tejash"},
            {"q":"Kredit qonunlariga nima kiradi?","opts":["Faqat qaytuvчanlik qonuni", "Qaytuvчanlik, tenglik, saqlanuvчanlik va vaqt qonunlari", "Faqat to'lovlilik qonuni", "Faqat muddatlilik qonuni"],"ans":1,"exp":"To'g'ri javob: A) Qaytuvчanlik, tenglik, saqlanuvчanlik va vaqt qonunlari"},
            {"q":"Kreditning makroiqtisodiy chegaralariga nima kiradi?","opts":["Faqat foiz stavkasi darajasi", "Faqat bank likvidligi", "Faqat mijozning kreditga layoqatliligi", "YaIM hajmi, kredit tizimining rivojlanishi, pul-kredit siyosati maqsadlari, bozor munosabatlari d..."],"ans":3,"exp":"To'g'ri javob: A) YaIM hajmi, kredit tizimining rivojlanishi, pul-kredit siyosati maqsadlari, bozor munosabatlari darajasi"},
            {"q":"Kreditning mikroiqtisodiy chegaralariga nima kiradi?","opts":["Mijozning kreditga layoqatliligi va bank likvidligi", "Faqat xalqaro standartlar", "Faqat davlat siyosati", "Faqat YaIM hajmi"],"ans":0,"exp":"To'g'ri javob: A) Mijozning kreditga layoqatliligi va bank likvidligi"},
            {"q":"O'zbekistonda kredit muddati bo'yicha qanday tasniflash qo'llaniladi?","opts":["Faqat uzoq muddatli", "Qisqa muddatli (1 yilgacha) va uzoq muddatli (1 yildan ortiq)", "Faqat qisqa muddatli", "Qisqa (1 yilgacha), o'rta (1-3 yil), uzoq (3 yildan ortiq)"],"ans":1,"exp":"To'g'ri javob: A) Qisqa muddatli (1 yilgacha) va uzoq muddatli (1 yildan ortiq)"},
            {"q":"AQShda kredit muddatlari qanday tasniflangan?","opts":["Qisqa – 3 yilgacha, o'rta – 3-10 yil, uzoq – 10 yildan ortiq", "Qisqa – 2 yilgacha, o'rta – 2-7 yil, uzoq – 7 yildan ortiq", "Qisqa – 1 yilgacha, o'rta – 1-3 yil, uzoq – 3 yildan ortiq", "Qisqa – 1 yilgacha, o'rta – 1-6 yil, uzoq – 6 yildan ortiq"],"ans":3,"exp":"To'g'ri javob: A) Qisqa – 1 yilgacha, o'rta – 1-6 yil, uzoq – 6 yildan ortiq"},
            {"q":"Buyuk Britaniyada kredit muddatlari qanday tasniflangan?","opts":["Qisqa – 1 yilgacha, o'rta – 1-3 yil, uzoq – 3 yildan ortiq", "Qisqa – 2 yilgacha, o'rta – 2-5 yil, uzoq – 5 yildan ortiq", "Qisqa – 3 yilgacha, o'rta – 3-10 yil, uzoq – 10 yildan ortiq", "Qisqa – 1 yilgacha, o'rta – 1-6 yil, uzoq – 6 yildan ortiq"],"ans":2,"exp":"To'g'ri javob: A) Qisqa – 3 yilgacha, o'rta – 3-10 yil, uzoq – 10 yildan ortiq"},
            {"q":"Ssuda kapitalining shakllanish jarayoniga nima kiradi?","opts":["Faqat xorijiy investitsiyalar", "Davlat, yuridik va jismoniy shaxslarning bo'sh mablag'larini vaqtincha foydalanishga berishi", "Faqat davlat mablag'lari", "Faqat bank zaxiralari"],"ans":1,"exp":"To'g'ri javob: A) Davlat, yuridik va jismoniy shaxslarning bo'sh mablag'larini vaqtincha foydalanishga berishi"},
            {"q":"Kreditning zarurligiga qanday omillar sabab bo'ladi?","opts":["Faqat ishlab chiqarish sikllarining mos kelmasligi", "Ishlab chiqarish sikllarining mos kelmasligi, jamg'arish imkoniyati mavjudligi, vaqtincha bo'sh m...", "Faqat davlat byudjet taqchilligi", "Faqat xalqaro savdo zarurligi"],"ans":1,"exp":"To'g'ri javob: A) Ishlab chiqarish sikllarining mos kelmasligi, jamg'arish imkoniyati mavjudligi, vaqtincha bo'sh mablag'lar paydo bo'lishi"},
        ]
    },
}

# ── DATABASE ──────────────────────────────────────────────
def init_db():
    c = sqlite3.connect(DB_PATH)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, username TEXT,
            full_name TEXT, language TEXT DEFAULT 'uz', joined_at TEXT);
        CREATE TABLE IF NOT EXISTS results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, topic_key TEXT,
            score INTEGER, total INTEGER, pct INTEGER, finished_at TEXT);
        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, topic_key TEXT,
            thumb INTEGER,   -- 1=up, 0=down, NULL=skip
            stars INTEGER,   -- 1-5, NULL=skip
            comment TEXT,
            created_at TEXT);
        CREATE TABLE IF NOT EXISTS custom_q(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat TEXT, topic_key TEXT, question TEXT,
            opt_a TEXT, opt_b TEXT, opt_c TEXT, opt_d TEXT,
            correct INTEGER, explanation TEXT);
    """)
    c.commit(); c.close()

def db_upsert(uid, uname, fname):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO users(user_id,username,full_name,language,joined_at)
        VALUES(?,?,?,'uz',?) ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username, full_name=excluded.full_name""",
        (uid, uname or "", fname, datetime.now().isoformat()))
    c.commit(); c.close()

def db_lang(uid, lang=None):
    c = sqlite3.connect(DB_PATH)
    if lang:
        c.execute("UPDATE users SET language=? WHERE user_id=?", (lang, uid))
        c.commit(); c.close()
    else:
        r = c.execute("SELECT language FROM users WHERE user_id=?", (uid,)).fetchone()
        c.close(); return r[0] if r else "uz"

def db_save_result(uid, topic_key, score, total):
    pct = round(score / total * 100)
    c   = sqlite3.connect(DB_PATH)
    c.execute("INSERT INTO results(user_id,topic_key,score,total,pct,finished_at) VALUES(?,?,?,?,?,?)",
        (uid, topic_key, score, total, pct, datetime.now().isoformat()))
    c.commit(); c.close(); return pct

def db_leaderboard(key="all"):
    c = sqlite3.connect(DB_PATH)
    if key == "all":
        rows = c.execute("""SELECT u.full_name,MAX(r.pct),r.score,r.total
            FROM results r JOIN users u ON u.user_id=r.user_id
            GROUP BY r.user_id ORDER BY MAX(r.pct) DESC LIMIT 10""").fetchall()
    else:
        rows = c.execute("""SELECT u.full_name,MAX(r.pct),r.score,r.total
            FROM results r JOIN users u ON u.user_id=r.user_id WHERE r.topic_key=?
            GROUP BY r.user_id ORDER BY MAX(r.pct) DESC LIMIT 10""", (key,)).fetchall()
    c.close(); return rows

def db_stats():
    c   = sqlite3.connect(DB_PATH)
    u   = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    t   = c.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    avg = c.execute("SELECT AVG(pct) FROM results").fetchone()[0] or 0
    c.close(); return u, t, round(avg)

def db_all_uids():
    c = sqlite3.connect(DB_PATH)
    r = c.execute("SELECT user_id FROM users").fetchall()
    c.close(); return [x[0] for x in r]

def db_add_q(cat, tkey, q, opts, ans, exp):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO custom_q(cat,topic_key,question,opt_a,opt_b,opt_c,opt_d,correct,explanation)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (cat, tkey, q, opts[0], opts[1], opts[2], opts[3], ans, exp))
    c.commit(); c.close()

def db_custom_q(key):
    c = sqlite3.connect(DB_PATH)
    if key == "all":
        rows = c.execute("SELECT question,opt_a,opt_b,opt_c,opt_d,correct,explanation FROM custom_q").fetchall()
    elif key.endswith("_all"):
        cat  = key.replace("_all","")
        rows = c.execute("SELECT question,opt_a,opt_b,opt_c,opt_d,correct,explanation FROM custom_q WHERE cat=?", (cat,)).fetchall()
    else:
        rows = c.execute("SELECT question,opt_a,opt_b,opt_c,opt_d,correct,explanation FROM custom_q WHERE topic_key=?", (key,)).fetchall()
    c.close()
    return [{"q":r[0],"opts":list(r[1:5]),"ans":r[5],"exp":r[6]} for r in rows]

# ── SERTIFIKAT ────────────────────────────────────────────
def make_cert(name, score, total, pct, topic, lang):
    if not PIL_OK: return None
    try:
        W, H = 900, 580
        img  = Image.new("RGB", (W, H), "#0D1B2A")
        d    = ImageDraw.Draw(img)
        for i in range(3):
            d.rectangle([8+i*5,8+i*5,W-8-i*5,H-8-i*5], outline="#C9A84C", width=1)
        d.rectangle([0,55,W,150], fill="#1B2A40")
        d.text((W//2,95),  "SERTIFIKAT" if lang=="uz" else "СЕРТИФИКАТ", fill="#C9A84C", anchor="mm")
        d.text((W//2,135), "Iqtisodiyot bo'yicha test muvaffaqiyatli topshirildi" if lang=="uz" else "Тест успешно пройден", fill="#AAAAAA", anchor="mm")
        d.text((W//2,220), name,  fill="#FFFFFF", anchor="mm")
        d.line([(140,250),(W-140,250)], fill="#C9A84C", width=1)
        d.text((W//2,290), topic, fill="#88BBEE", anchor="mm")
        gt = TX[lang]["grade_5"] if pct>=85 else TX[lang]["grade_4"] if pct>=70 else TX[lang]["grade_3"] if pct>=55 else TX[lang]["grade_2"]
        d.text((W//2,350), f"{score}/{total}  ({pct}%)", fill="#66EE88", anchor="mm")
        d.text((W//2,390), gt, fill="#FFDD44", anchor="mm")
        d.text((W//2,460), datetime.now().strftime("%d.%m.%Y"), fill="#888888", anchor="mm")
        d.text((W//2,500), "Super Quiz Bot", fill="#445566", anchor="mm")
        buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0); return buf
    except Exception as e:
        log.warning(f"cert: {e}"); return None

# ── HELPERS ───────────────────────────────────────────────
def get_qs(key):
    if key == "all":
        qs = [q for tp in TOPICS.values() for q in tp["questions"]]
    elif key.endswith("_all"):
        cat = key.replace("_all","")
        qs  = [q for k,tp in TOPICS.items() if tp["cat"]==cat for q in tp["questions"]]
    else:
        qs  = TOPICS[key]["questions"].copy()
    qs += db_custom_q(key)
    random.shuffle(qs); return qs

def tname(key, uid):
    lang = user_lang.get(uid, "uz")
    if key == "all": return txt(uid, "all_mix")
    if key.endswith("_all"):
        cat = key.replace("_all","")
        return f"{CATEGORIES[cat]['emoji']} {CATEGORIES[cat][lang]}"
    return TOPICS[key][lang]

def grade_t(uid, pct):
    l = user_lang.get(uid,"uz")
    return TX[l]["grade_5"] if pct>=85 else TX[l]["grade_4"] if pct>=70 else TX[l]["grade_3"] if pct>=55 else TX[l]["grade_2"]

def eg(pct): return "🏆" if pct>=85 else "✅" if pct>=70 else "📝" if pct>=55 else "❌"

# ── REPLY KEYBOARD ────────────────────────────────────────
def main_kb(uid):
    """
    ┌─────────────────────────────────┐
    │         📝 Testlar              │
    ├───────────────┬─────────────────┤
    │ 📊 Mikro      │ 📈 Makro        │
    ├───────────────┴─────────────────┤
    │      🏦 Pul va Bank             │
    ├───────────────┬─────────────────┤
    │  🏆 Reyting   │ 📊 Statistika   │
    ├───────────────┴─────────────────┤
    │          ℹ️ Yordam              │
    └─────────────────────────────────┘
    """
    lang = user_lang.get(uid, "uz")
    return ReplyKeyboardMarkup([
        [KeyboardButton(TX[lang]["btn_tests"]),
         KeyboardButton(TX[lang]["btn_pdf"])],
        [KeyboardButton(TX[lang]["btn_top"]),
         KeyboardButton(TX[lang]["btn_stats"])],
        [KeyboardButton(TX[lang]["btn_feedback"]),
         KeyboardButton(TX[lang]["btn_help"])],
    ], resize_keyboard=True)

# ── TIMER ─────────────────────────────────────────────────
def make_timer_bar(sec_left, total=30):
    """Progress bar yasash"""
    filled = round((sec_left / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return bar

def timer_kb(uid):
    lang = user_lang.get(uid, "uz")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(TX[lang]["btn_pause"], callback_data="quiz_pause"),
        InlineKeyboardButton(TX[lang]["btn_stop"],  callback_data="quiz_stop"),
    ]])

def resume_kb(uid):
    lang = user_lang.get(uid, "uz")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(TX[lang]["btn_resume"], callback_data="quiz_resume"),
        InlineKeyboardButton(TX[lang]["btn_stop"],   callback_data="quiz_stop"),
    ]])

async def timer_job(context):
    d = context.job.data; uid = d["uid"]; pid = d["pid"]
    if uid not in user_state: return
    st = user_state[uid]
    if pid not in st["poll_map"]: return
    del st["poll_map"][pid]; st["index"] += 1
    st["skipped"] = st.get("skipped", 0) + 1
    await context.bot.send_message(st["cid"], txt(uid, "time_up"))
    await send_q(context, uid, st["cid"])

# ── SEND QUESTION ─────────────────────────────────────────
async def send_q(context, uid, cid):
    st = user_state.get(uid)
    if not st: return
    idx = st["index"]; qs = st["qs"]
    if idx >= len(qs):
        import time as _t
        s       = st["score"]; tot = len(qs)
        skipped = st.get("skipped", 0)
        wrong   = tot - s - skipped
        elapsed = int(_t.time() - st.get("start_time", _t.time()))
        mins, secs = divmod(elapsed, 60)
        pct     = db_save_result(uid, st["key"], s, tot)
        rank, participants = db_rank(uid, st["key"], pct)
        lang    = user_lang.get(uid, "uz")
        topic   = tname(st["key"], uid)

        if lang == "uz":
            time_str  = f"{mins} daqiqa {secs} soniya" if mins else f"{secs} soniya"
            rank_line = (f"\n{participants} tadan {rank}-o'rin. Siz ushbu testda ishtirok etgan "
                         f"{round((participants-rank)/participants*100) if participants>1 else 0}% "
                         f"odamlardan yuqoriroq ball to'pladingiz.") if participants > 1 else ""
            result_text = (
                f"🏁 \"{topic}\" testi yakunlandi!\n\n"
                f"Siz {tot} ta savolga javob berdingiz:\n"
                f"✅ To'g'ri — **{s}**\n"
                f"❌ Xato — **{wrong}**\n"
                f"⏳ Tashlab ketilgan — **{skipped}**\n"
                f"🕐 {time_str}"
                f"{rank_line}"
            )
        else:
            time_str  = f"{mins} мин {secs} сек" if mins else f"{secs} сек"
            rank_line = (f"\n{participants} из {rank}-е место. Вы набрали больше баллов, чем "
                         f"{round((participants-rank)/participants*100) if participants>1 else 0}% "
                         f"участников.") if participants > 1 else ""
            result_text = (
                f"🏁 Тест \"{topic}\" завершён!\n\n"
                f"Вы ответили на {tot} вопросов:\n"
                f"✅ Правильно — **{s}**\n"
                f"❌ Неправильно — **{wrong}**\n"
                f"⏳ Пропущено — **{skipped}**\n"
                f"🕐 {time_str}"
                f"{rank_line}"
            )

        await context.bot.send_message(cid, result_text,
            parse_mode="Markdown", reply_markup=main_kb(uid))

        c   = sqlite3.connect(DB_PATH)
        row = c.execute("SELECT full_name FROM users WHERE user_id=?", (uid,)).fetchone()
        c.close()
        cert = make_cert(row[0] if row else "User", s, tot, pct, tname(st["key"],uid), lang)
        if cert:
            await context.bot.send_photo(cid, photo=cert,
                caption=f"🎓 {row[0] if row else 'User'} — {s}/{tot} ({pct}%)")
        saved_key = st["key"]
        del user_state[uid]
        await start_feedback(uid, saved_key, cid, context)
        return
    q   = qs[idx]

    # Eski joblarni tozalash
    for job in context.job_queue.get_jobs_by_name(f"t_{uid}"):
        job.schedule_removal()

    # Telegram limitlari: savol max 255, variant max 100, izoh max 200
    q_text   = f"[{idx+1}/{len(qs)}] {q['q']}"[:255]
    opts     = [o[:100] for o in q["opts"]]
    exp_text = (q.get("exp") or "")[:200]

    try:
        msg = await context.bot.send_poll(
            cid,
            question          = q_text,
            options           = opts,
            type              = "quiz",
            correct_option_id = q["ans"],
            explanation       = exp_text,
            open_period       = TIMER_SEC,
            is_anonymous      = False,
            reply_markup      = ReplyKeyboardRemove())
    except Exception as e:
        log.warning(f"send_poll xato uid={uid}: {e}")
        # Xatoli savolni o'tkazib yuborish
        st["index"]   += 1
        st["skipped"]  = st.get("skipped", 0) + 1
        await send_q(context, uid, cid)
        return

    st["poll_map"][msg.poll.id] = q["ans"]
    st["poll_msg_id"]  = msg.message_id
    st["paused"]       = False

    context.job_queue.run_once(timer_job, TIMER_SEC + 2,
        name=f"t_{uid}", data={"uid": uid, "pid": msg.poll.id})

# ── HANDLERS ──────────────────────────────────────────────
async def cmd_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    db_upsert(uid, u.effective_user.username, u.effective_user.full_name)
    lang = db_lang(uid); user_lang[uid] = lang
    kb = [[InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
           InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]]
    await u.message.reply_text(TX[lang]["choose_lang"],
                               reply_markup=InlineKeyboardMarkup(kb))

async def cb_lang(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    uid = q.from_user.id; lang = q.data.split("_")[1]
    user_lang[uid] = lang; db_lang(uid, lang)
    await q.edit_message_text(txt(uid,"welcome",name=q.from_user.first_name))
    await ctx.bot.send_message(q.message.chat_id, txt(uid,"main_menu"),
                               reply_markup=main_kb(uid))

async def show_topic_inline(uid, cat_key, cid, ctx):
    """Kategoriya tanlanganda inline mavzular chiqaradi"""
    lang = user_lang.get(uid,"uz")
    cat  = CATEGORIES[cat_key]
    if not cat["active"]:
        await ctx.bot.send_message(cid, txt(uid,"coming_soon"),
                                   reply_markup=main_kb(uid)); return
    kb = []
    for tk, tp in TOPICS.items():
        if tp["cat"] == cat_key:
            kb.append([InlineKeyboardButton(f"📝 {tp[lang]}", callback_data=f"t_{tk}")])
    kb.append([InlineKeyboardButton(txt(uid,"all_mix"), callback_data=f"t_{cat_key}_all")])
    kb.append([InlineKeyboardButton(txt(uid,"back_cat"), callback_data="back_main")])
    await ctx.bot.send_message(cid,
        txt(uid,"topic_menu", cat=f"{cat['emoji']} {cat[lang]}"),
        reply_markup=InlineKeyboardMarkup(kb))

async def handle_reply_btn(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = u.effective_user.id
    text = u.message.text
    lang = user_lang.get(uid,"uz")
    cid  = u.message.chat_id

    # Feedback izoh bosqichida bo'lsa — birinchi tekshir
    if uid in feedback_state and feedback_state[uid].get("step") == "comment":
        await handle_feedback_comment(uid, text, cid, ctx); return

    # Testlar — asosiy kategoriyalar menyusi
    if text == TX[lang]["btn_tests"]:
        kb = []
        for cat_key, cat in CATEGORIES.items():
            label = f"{cat['emoji']} {cat[lang]}"
            if not cat["active"]:
                label += " (tez kunda)" if lang=="uz" else " (скоро)"
            kb.append([InlineKeyboardButton(label, callback_data=f"cat_{cat_key}")])
        # Avval reply keyboard'ni qayta ko'rsatish uchun bo'sh xabar
        await ctx.bot.send_message(cid, txt(uid,"main_menu"),
                                   reply_markup=main_kb(uid))
        await ctx.bot.send_message(cid, "👇 Fan tanlang:",
                                   reply_markup=InlineKeyboardMarkup(kb)); return

    # Reyting
    if text == TX[lang]["btn_top"]:
        await show_top_menu(uid, cid, ctx); return

    # Statistika
    if text == TX[lang]["btn_stats"]:
        us, ts, avg = db_stats()
        await ctx.bot.send_message(cid, txt(uid,"stats",u=us,t=ts,a=avg),
                                   reply_markup=main_kb(uid)); return

    # PDF dan test
    if text == TX[lang]["btn_pdf"]:
        await ctx.bot.send_message(cid,
            "📄 PDF faylni yuboring — AI avtomatik test tuzadi!\n\n"
            "• Darslik, ma'ruza, konspekt — istalgan PDF\n"
            "• 10 ta savol avtomatik tuziladi",
            reply_markup=main_kb(uid)); return

    # Feedback (foydalanuvchi uchun — o'z fikrlarini ko'rish)
    if text == TX[lang]["btn_feedback"]:
        c = __import__("sqlite3").connect("quiz.db")
        rows = c.execute("""SELECT f.stars, f.thumb, f.comment, f.created_at
            FROM feedback f WHERE f.user_id=?
            ORDER BY f.created_at DESC LIMIT 5""", (uid,)).fetchall()
        c.close()
        if not rows:
            await ctx.bot.send_message(cid,
                "💬 Siz hali feedback qoldirmagansiz.\n\nTestni yakunlagandan so'ng feedback so'raladi!",
                reply_markup=main_kb(uid)); return
        lines = ["💬 Sizning so'nggi feedbacklaringiz:"]
        for stars, thumb, comment, created in rows:
            t_icon = "👍" if thumb == 1 else "👎" if thumb == 0 else "—"
            s_icon = "⭐" * (stars or 0)
            lines.append(f"{t_icon} {s_icon} — {comment or '(izohsiz)'}")
        await ctx.bot.send_message(cid, "\n".join(lines), reply_markup=main_kb(uid)); return

    # Yordam
    if text == TX[lang]["btn_help"]:
        await ctx.bot.send_message(cid, txt(uid,"help"),
                                   reply_markup=main_kb(uid)); return

async def cb_cat(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    uid = q.from_user.id; cat_key = q.data.split("_",1)[1]
    await show_topic_inline(uid, cat_key, q.message.chat_id, ctx)

async def cb_back_main(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    uid = q.from_user.id; lang = user_lang.get(uid,"uz")
    kb = []
    for cat_key, cat in CATEGORIES.items():
        label = f"{cat['emoji']} {cat[lang]}"
        if not cat["active"]:
            label += " (tez kunda)" if lang=="uz" else " (скоро)"
        kb.append([InlineKeyboardButton(label, callback_data=f"cat_{cat_key}")])
    await q.edit_message_text(txt(uid,"main_menu"),
                              reply_markup=InlineKeyboardMarkup(kb))

async def cb_topic(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    uid = q.from_user.id; key = q.data[2:]
    qs  = get_qs(key)
    import time as _t
    user_state[uid] = {"qs":qs,"index":0,"score":0,"skipped":0,
                       "poll_map":{},"key":key,"cid":q.message.chat_id,
                       "start_time": _t.time()}
    await q.edit_message_text(
        txt(uid,"quiz_start",topic=tname(key,uid),n=len(qs),timer=TIMER_SEC))
    await send_q(ctx, uid, q.message.chat_id)

async def poll_answer(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    a = u.poll_answer; uid = a.user.id
    if uid not in user_state: return
    # Bo'sh javob (open_period tugagach Telegram yuboradigan signal) — e'tibor berma
    if not a.option_ids: return
    st = user_state[uid]; pid = a.poll_id
    if pid not in st["poll_map"]: return
    # Timer jobni bekor qil
    for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
        job.schedule_removal()
    # Javobni tekshirish
    if a.option_ids[0] == st["poll_map"][pid]:
        st["score"] += 1
    st["index"] += 1
    del st["poll_map"][pid]
    # Keyingi savol
    await send_q(ctx, uid, st["cid"])

async def show_top_menu(uid, cid, ctx):
    lang = user_lang.get(uid,"uz")
    kb = []
    for cat_key, cat in CATEGORIES.items():
        if cat["active"]:
            kb.append([InlineKeyboardButton(f"{cat['emoji']} {cat[lang]}",
                                            callback_data=f"top_{cat_key}_all")])
            for tk, tp in TOPICS.items():
                if tp["cat"] == cat_key:
                    kb.append([InlineKeyboardButton(f"  └ {tp[lang]}", callback_data=f"top_{tk}")])
    await ctx.bot.send_message(cid, "🏆 Mavzu tanlang:",
                               reply_markup=InlineKeyboardMarkup(kb))

async def cb_top(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    uid = q.from_user.id; key = q.data[4:]
    rows = db_leaderboard(key)
    if not rows: await q.edit_message_text(txt(uid,"top_empty")); return
    md    = ["🥇","🥈","🥉"]+["🏅"]*7
    lines = [f"🏆 {tname(key,uid)}"]
    for i,(nm,pct,sc,tot) in enumerate(rows):
        lines.append(f"{md[i]} {nm} — {pct}%  ({sc}/{tot})")
    await q.edit_message_text("\n".join(lines))

async def cmd_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    us, ts, avg = db_stats()
    await u.message.reply_text(txt(uid,"stats",u=us,t=ts,a=avg),
                               reply_markup=main_kb(uid))

async def cmd_admin(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid,"not_admin")); return
    us, ts, avg = db_stats()
    await u.message.reply_text(
        f"⚙️ Admin panel\n\nFoydalanuvchilar: {us}\nTestlar: {ts}\nO'rtacha: {avg}%\n\n"
        f"/broadcast Matn — Barcha userlarga xabar\n/addq — Savol qo'shish")

async def cmd_broadcast(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid,"not_admin")); return
    msg = " ".join(ctx.args)
    if not msg:
        await u.message.reply_text("Xabar kiriting: /broadcast Salom!"); return
    sent = 0
    for i in db_all_uids():
        try: await ctx.bot.send_message(i, f"📢 {msg}"); sent += 1
        except: pass
    await u.message.reply_text(txt(uid,"bcast_ok",n=sent))

async def cmd_addq(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid,"not_admin")); return
    raw = u.message.text.replace("/addq","").strip()
    if not raw:
        await u.message.reply_text(txt(uid,"addq_help")); return
    try:
        lines = {ln.split(":",1)[0].strip(): ln.split(":",1)[1].strip()
                 for ln in raw.splitlines() if ":" in ln}
        cat  = lines.get("CAT","mikro")
        tkey = f"{cat}_{lines.get('TOPIC','1')}"
        db_add_q(cat, tkey, lines["Q"],
                 [lines["A"],lines["B"],lines["C"],lines["D"]],
                 int(lines["ANS"]), lines.get("EXP",""))
        await u.message.reply_text(txt(uid,"addq_ok"))
    except Exception as e:
        log.warning(f"addq: {e}")
        await u.message.reply_text(txt(uid,"addq_err"))

async def cmd_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    await u.message.reply_text(txt(uid,"help"), reply_markup=main_kb(uid))

async def cmd_top(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    await show_top_menu(uid, u.message.chat_id, ctx)

# ── PDF → AI TEST ─────────────────────────────────────────
def extract_pdf_text(file_bytes: bytes) -> str:
    """PDF dan matn ajratib olish"""
    if not PYPDF_OK:
        return ""
    try:
        reader = PdfReader(BytesIO(file_bytes))
        pages  = [p.extract_text() or "" for p in reader.pages]
        text   = "\n".join(pages).strip()
        return text[:12000]   # max 12k belgi
    except Exception as e:
        log.warning(f"pdf extract: {e}"); return ""

async def ai_generate_questions(text: str, lang: str, n: int = 10) -> list:
    """Google Gemini API orqali savol yaratish"""
    if not GEMINI_OK or not GEMINI_KEY:
        return []

    prompt_uz = f"""Quyidagi matndan {n} ta test savoli tuz (o'zbek tilida).
Javobni FAQAT sof JSON formatida ber — hech qanday ``` yoki izoh yozma.
Faqat [ ] ichidagi JSON massivni yoz:
[
  {{
    "q": "Savol matni",
    "opts": ["A variant", "B variant", "C variant", "D variant"],
    "ans": 0,
    "exp": "To'g'ri javob izohi"
  }}
]
ans = to'g'ri variant indeksi (0=A, 1=B, 2=C, 3=D)

MATN:
{text}"""

    prompt_ru = f"""Составь {n} тестовых вопросов на русском языке по следующему тексту.
Ответ дай ТОЛЬКО в виде чистого JSON — без ``` и без лишнего текста.
Только JSON массив [ ]:
[
  {{
    "q": "Текст вопроса",
    "opts": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
    "ans": 0,
    "exp": "Пояснение правильного ответа"
  }}
]
ans = индекс правильного варианта (0=A, 1=B, 2=C, 3=D)

ТЕКСТ:
{text}"""

    prompt = prompt_uz if lang == "uz" else prompt_ru

    def _gemini_call(p):
        try:
            genai.configure(api_key=GEMINI_KEY)
            model    = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(p)
            raw      = response.text.strip()
            log.info(f"gemini raw (first 200): {raw[:200]}")
            return raw
        except Exception as e:
            log.error(f"gemini _sync xato: {e}")
            raise

    try:
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            raw = await loop.run_in_executor(pool, _gemini_call, prompt)

        # JSON tozalash
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"): part = part[4:].strip()
                if part.startswith("["): raw = part; break
        start = raw.find("[")
        end   = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end+1]

        questions = json.loads(raw)
        valid = []
        for q in questions:
            if all(k in q for k in ("q","opts","ans","exp")) and len(q["opts"]) == 4:
                valid.append(q)
        log.info(f"gemini: {len(valid)} ta savol yaratildi")
        return valid[:n]
    except Exception as e:
        log.error(f"ai_generate XATO: {type(e).__name__}: {e}")
        return []

async def handle_pdf(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = u.effective_user.id
    lang = user_lang.get(uid, "uz")
    cid  = u.message.chat_id
    doc  = u.message.document

    if not doc or not doc.file_name.lower().endswith(".pdf"):
        return

    await ctx.bot.send_message(cid, txt(uid, "pdf_recv"))

    if not GEMINI_OK or not GEMINI_KEY:
        await ctx.bot.send_message(cid, txt(uid, "pdf_no_ai"),
                                   reply_markup=main_kb(uid)); return
    try:
        file      = await doc.get_file()
        file_data = await file.download_as_bytearray()
        pdf_text  = extract_pdf_text(bytes(file_data))
        if not pdf_text:
            await ctx.bot.send_message(cid, txt(uid, "pdf_no_text"),
                                       reply_markup=main_kb(uid)); return

        questions = await ai_generate_questions(pdf_text, lang)

        if not questions:
            await ctx.bot.send_message(cid, txt(uid, "pdf_fail"),
                                       reply_markup=main_kb(uid)); return

        fname = doc.file_name[:30]
        key   = f"pdf_{uid}_{int(datetime.now().timestamp())}"
        import time as _t2
        user_state[uid] = {
            "qs"      : questions,
            "index"   : 0,
            "score"   : 0,
            "skipped" : 0,
            "poll_map": {},
            "key"     : key,
            "cid"     : cid,
            "is_pdf"  : True,
            "pdf_name": fname,
            "start_time": _t2.time(),
        }
        await ctx.bot.send_message(cid,
            txt(uid, "pdf_done", n=len(questions)))
        await send_q(ctx, uid, cid)

    except Exception as e:
        log.warning(f"handle_pdf: {e}")
        await ctx.bot.send_message(cid, txt(uid, "pdf_fail"),
                                   reply_markup=main_kb(uid))

# ── FEEDBACK TIZIMI ────────────────────────────────────────
def db_save_feedback(uid, topic_key, thumb, stars, comment):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO feedback(user_id,topic_key,thumb,stars,comment,created_at)
        VALUES(?,?,?,?,?,?)""",
        (uid, topic_key, thumb, stars, comment, datetime.now().isoformat()))
    c.commit(); c.close()

def db_feedback_report():
    c = sqlite3.connect(DB_PATH)
    total  = c.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    thumbs = c.execute("SELECT COUNT(*) FROM feedback WHERE thumb=1").fetchone()[0]
    thumbd = c.execute("SELECT COUNT(*) FROM feedback WHERE thumb=0").fetchone()[0]
    avg_s  = c.execute("SELECT AVG(stars) FROM feedback WHERE stars IS NOT NULL").fetchone()[0] or 0
    recent = c.execute("""
        SELECT u.full_name, f.stars, f.thumb, f.comment, f.topic_key, f.created_at
        FROM feedback f LEFT JOIN users u ON u.user_id=f.user_id
        ORDER BY f.created_at DESC LIMIT 10""").fetchall()
    c.close()
    return total, thumbs, thumbd, round(avg_s, 1), recent

async def start_feedback(uid, topic_key, cid, ctx):
    """Test tugagach feedback so'rash"""
    feedback_state[uid] = {"step": "thumb", "topic": topic_key, "thumb": None, "stars": None}
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("👍 Ha", callback_data="fb_thumb_1"),
        InlineKeyboardButton("👎 Yo'q", callback_data="fb_thumb_0"),
        InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="fb_skip"),
    ]])
    await ctx.bot.send_message(cid, txt(uid, "fb_thumb_q"), reply_markup=kb)

async def cb_feedback(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = u.callback_query; await q.answer()
    uid = q.from_user.id
    cid = q.message.chat_id
    data = q.data

    if data == "fb_skip":
        feedback_state.pop(uid, None)
        await q.edit_message_text(txt(uid, "fb_skip"))
        await ctx.bot.send_message(cid, "📚", reply_markup=main_kb(uid)); return

    st = feedback_state.get(uid)
    if not st: return

    if data.startswith("fb_thumb_"):
        st["thumb"] = int(data[-1])
        st["step"]  = "star"
        stars_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("⭐", callback_data="fb_star_1"),
            InlineKeyboardButton("⭐⭐", callback_data="fb_star_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data="fb_star_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data="fb_star_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="fb_star_5"),
        ]])
        await q.edit_message_text(txt(uid, "fb_star_q"), reply_markup=stars_kb); return

    if data.startswith("fb_star_"):
        st["stars"] = int(data[-1])
        st["step"]  = "comment"
        await q.edit_message_text(txt(uid, "fb_comment_q")); return

async def handle_feedback_comment(uid, text, cid, ctx):
    """Foydalanuvchi izoh yozganda"""
    st = feedback_state.get(uid)
    if not st or st.get("step") != "comment": return False
    comment = "" if text == "/skip" else text
    db_save_feedback(uid, st["topic"], st.get("thumb"), st.get("stars"), comment)
    feedback_state.pop(uid, None)
    await ctx.bot.send_message(cid, txt(uid, "fb_done"), reply_markup=main_kb(uid))
    return True

async def cmd_feedback(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid, "not_admin")); return
    total, thumbs_up, thumbs_dn, avg_stars, recent = db_feedback_report()
    lines = [
        f"📊 Feedback hisoboti",
        f"Jami: {total} ta",
        f"👍 Foydali: {thumbs_up} | 👎 Foydali emas: {thumbs_dn}",
        f"⭐ O'rtacha baho: {avg_stars}/5",
        f"",
        f"🕐 So'nggi fikrlar:",
    ]
    for nm, stars, thumb, comment, topic, created in recent:
        t_icon = "👍" if thumb == 1 else "👎" if thumb == 0 else "—"
        s_icon = "⭐" * (stars or 0)
        lines.append(f"{t_icon} {s_icon} {nm or '?'}: {comment or '(izohsiz)'}")
    await u.message.reply_text("\n".join(lines))

# ── PAUSE / RESUME / STOP ─────────────────────────────────
async def cb_quiz_ctrl(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = u.callback_query; await q.answer()
    uid  = q.from_user.id
    cid  = q.message.chat_id
    data = q.data
    st   = user_state.get(uid)

    if data == "quiz_stop":
        if not st: return
        for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
            job.schedule_removal()
        del user_state[uid]
        await ctx.bot.send_message(cid, txt(uid, "stop_confirm"),
                                   reply_markup=main_kb(uid))

    elif data == "quiz_pause_disabled":  # eski kod — ishlatilmaydi
        if not st or st.get("paused"): return
        pass  # open_period bilan pause mumkin emas

    if data == "quiz_pause":
        if not st or st.get("paused"): return
        # Joblarni to'xtatish
        for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
            job.schedule_removal()
        # Qolgan vaqtni hisoblash
        elapsed  = int(datetime.now().timestamp()) - st.get("timer_start", 0)
        sec_left = max(0, TIMER_SEC - elapsed)
        st["paused"]       = True
        st["paused_sec"]   = sec_left
        # Timer xabarni yangilash
        await q.edit_message_text(
            txt(uid, "paused_msg", sec=sec_left),
            parse_mode   = "HTML",
            reply_markup = resume_kb(uid)
        )

    elif data == "quiz_resume":
        if not st or not st.get("paused"): return
        sec_left = st.get("paused_sec", TIMER_SEC)
        now      = int(datetime.now().timestamp())
        st["timer_start"] = now - (TIMER_SEC - sec_left)
        st["paused"]      = False
        # Joblarni qayta ishga tushirish
        ctx.job_queue.run_once(timer_job, sec_left,
            name=f"t_{uid}",
            data={"uid": uid, "pid": list(st["poll_map"].keys())[-1] if st["poll_map"] else ""})
        # Timer xabarni yangilash
        bar = make_timer_bar(sec_left)
        idx = st["index"]; n = len(st["qs"])
        await q.edit_message_text(
            txt(uid, "timer_msg", i=idx+1, n=n, bar=bar, sec=sec_left),
            reply_markup = timer_kb(uid)
        )

    elif data == "quiz_stop":
        if not st: return
        # Barcha joblarni to'xtatish
        for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
            job.schedule_removal()
        # Timer xabarni o'chirish
        try:
            await ctx.bot.delete_message(cid, st.get("timer_msg_id"))
        except Exception:
            pass
        del user_state[uid]
        await ctx.bot.send_message(cid, txt(uid, "stop_confirm"),
                                   reply_markup=main_kb(uid))

# ── MAIN ──────────────────────────────────────────────────
async def post_init(app):
    """Bot ishga tushganda command menyusini o'rnatish"""
    from telegram import BotCommand, BotCommandScopeDefault
    uz_commands = [
        BotCommand("start",     "🏠 Bosh menyu"),
        BotCommand("tests",     "📝 Testlar bo'limi"),
        BotCommand("top",       "🏆 Reyting"),
        BotCommand("stats",     "📊 Statistika"),
        BotCommand("stop",      "🚫 Testni to'xtatish"),
        BotCommand("help",      "ℹ️ Yordam"),
    ]
    await app.bot.set_my_commands(uz_commands, scope=BotCommandScopeDefault())

async def cmd_tests(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Testlar bo'limiga to'g'ridan o'tish"""
    uid = u.effective_user.id
    lang = user_lang.get(uid, "uz")
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    kb = []
    for cat_key, cat in CATEGORIES.items():
        status = "" if cat["active"] else " ⏳"
        kb.append([InlineKeyboardButton(
            f"{cat['emoji']} {cat[lang]}{status}",
            callback_data=f"cat_{cat_key}"
        )])
    await u.message.reply_text(txt(uid, "main_menu"), reply_markup=InlineKeyboardMarkup(kb))

async def cmd_stop_quiz(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/stop — aktiv testni to'xtatish"""
    uid = u.effective_user.id
    if uid in user_state:
        for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
            job.schedule_removal()
        del user_state[uid]
        await u.message.reply_text(txt(uid, "stop_confirm"), reply_markup=main_kb(uid))
    else:
        lang = user_lang.get(uid, "uz")
        msg = "Hozir aktiv test yo'q." if lang == "uz" else "Нет активного теста."
        await u.message.reply_text(msg, reply_markup=main_kb(uid))

def main():
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("tests",     cmd_tests))
    app.add_handler(CommandHandler("top",       cmd_top))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("stop",      cmd_stop_quiz))
    app.add_handler(CommandHandler("admin",     cmd_admin))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("addq",      cmd_addq))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("feedback",  cmd_feedback))
    app.add_handler(CallbackQueryHandler(cb_lang,      pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(cb_cat,       pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(cb_topic,     pattern="^t_"))
    app.add_handler(CallbackQueryHandler(cb_back_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(cb_top,       pattern="^top_"))
    app.add_handler(CallbackQueryHandler(cb_feedback,  pattern="^fb_"))
    app.add_handler(CallbackQueryHandler(cb_quiz_ctrl, pattern="^quiz_"))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_btn))
    app.add_handler(PollAnswerHandler(poll_answer))
    log.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
