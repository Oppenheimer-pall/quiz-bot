#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║   SUPER QUIZ BOT v2.0                                    ║
║   Ko'p tillilik, Mavzu, Timer, Reyting, Sertifikat,      ║
║   Admin panel, Statistika, Broadcast                     ║
╚══════════════════════════════════════════════════════════╝
"""

import logging, random, sqlite3, os
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PollAnswerHandler, ContextTypes
)

# ── CONFIG ────────────────────────────────────────────────
TOKEN     = os.getenv("BOT_TOKEN", "8657957504:AAEqdqcK9Ljix2-DYiYoXFgWiuWJzIkq9c8")
_adm      = os.getenv("ADMIN_IDS", "0")
ADMIN_IDS = [int(x) for x in _adm.split(",") if x.strip().isdigit()]
DB_PATH   = "quiz.db"
TIMER_SEC = 30

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ── KO'P TILLIK MATNLAR ───────────────────────────────────
TX = {
    "uz": {
        "welcome"    : "Salom, {name}! Iqtisodiyot bo'yicha Super Quiz Botga xush kelibsiz!",
        "choose_lang": "Tilni tanlang:",
        "main_menu"  : "Mavzu tanlang:",
        "quiz_start" : "Mavzu: {topic}\nSavollar: {n} ta | Har savolga {timer} soniya\n\nBoshlanmoqda...",
        "q_label"    : "{i}/{n} savol",
        "time_up"    : "Vaqt tugadi! Keyingi savol...",
        "result"     : "{emoji} Test yakunlandi!\n\nNatija: {s}/{total} ({p}%)\nBaho: {grade}\n\n/start — Qayta boshlash",
        "grade_5"    : "A'lo ⭐⭐⭐",
        "grade_4"    : "Yaxshi",
        "grade_3"    : "Qoniqarli",
        "grade_2"    : "Qayta o'qing",
        "top_title"  : "TOP-10 Reyting — {topic}",
        "top_empty"  : "Hali natijalar yo'q.",
        "stats"      : "Statistika:\nFoydalanuvchilar: {u}\nTestlar: {t}\nO'rtacha ball: {a}%",
        "not_admin"  : "Siz admin emassiz.",
        "bcast_ok"   : "{n} ta foydalanuvchiga yuborildi.",
        "addq_help"  : "Savol qo'shish formati:\n\n/addq\nTOPIC:1\nQ:Savol matni\nA:Variant A\nB:Variant B\nC:Variant C\nD:Variant D\nANS:0\nEXP:Izoh\n\nANS: 0=A, 1=B, 2=C, 3=D\nTOPIC: 1-4",
        "addq_ok"    : "Savol muvaffaqiyatli qo'shildi!",
        "addq_err"   : "Format xato. /addq ni ko'ring.",
        "all_topics" : "Barcha mavzular (aralash)",
        "help"       : "/start — Bosh menyu\n/top — Reyting\n/stats — Statistika\n/admin — Admin panel",
    },
    "ru": {
        "welcome"    : "Привет, {name}! Добро пожаловать в Super Quiz Bot по экономике!",
        "choose_lang": "Выберите язык:",
        "main_menu"  : "Выберите тему:",
        "quiz_start" : "Тема: {topic}\nВопросов: {n} | На каждый {timer} секунд\n\nНачинаем...",
        "q_label"    : "Вопрос {i}/{n}",
        "time_up"    : "Время вышло! Следующий вопрос...",
        "result"     : "{emoji} Тест завершён!\n\nРезультат: {s}/{total} ({p}%)\nОценка: {grade}\n\n/start — Начать заново",
        "grade_5"    : "Отлично",
        "grade_4"    : "Хорошо",
        "grade_3"    : "Удовлетворительно",
        "grade_2"    : "Повторите материал",
        "top_title"  : "ТОП-10 Рейтинг — {topic}",
        "top_empty"  : "Результатов пока нет.",
        "stats"      : "Статистика:\nПользователей: {u}\nТестов: {t}\nСредний балл: {a}%",
        "not_admin"  : "Вы не являетесь администратором.",
        "bcast_ok"   : "Отправлено {n} пользователям.",
        "addq_help"  : "Формат добавления вопроса:\n\n/addq\nTOPIC:1\nQ:Текст вопроса\nA:Вариант A\nB:Вариант B\nC:Вариант C\nD:Вариант D\nANS:0\nEXP:Пояснение",
        "addq_ok"    : "Вопрос успешно добавлен!",
        "addq_err"   : "Неверный формат. Смотрите /addq.",
        "all_topics" : "Все темы (вперемешку)",
        "help"       : "/start — Главное меню\n/top — Рейтинг\n/stats — Статистика\n/admin — Панель",
    }
}

user_lang  = {}
user_state = {}

def txt(uid, key, **kw):
    lang = user_lang.get(uid, "uz")
    s    = TX[lang].get(key, key)
    return s.format(**kw) if kw else s

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
        CREATE TABLE IF NOT EXISTS custom_q(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_key TEXT, question TEXT,
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
        c.commit()
    else:
        r = c.execute("SELECT language FROM users WHERE user_id=?", (uid,)).fetchone()
        c.close()
        return r[0] if r else "uz"
    c.close()

def db_save_result(uid, topic_key, score, total):
    pct = round(score / total * 100)
    c   = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO results(user_id,topic_key,score,total,pct,finished_at)
        VALUES(?,?,?,?,?,?)""",
        (uid, topic_key, score, total, pct, datetime.now().isoformat()))
    c.commit(); c.close()
    return pct

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
    c.close()
    return rows

def db_stats():
    c = sqlite3.connect(DB_PATH)
    u    = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    t    = c.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    avg  = c.execute("SELECT AVG(pct) FROM results").fetchone()[0] or 0
    c.close()
    return u, t, round(avg)

def db_all_uids():
    c = sqlite3.connect(DB_PATH)
    rows = c.execute("SELECT user_id FROM users").fetchall()
    c.close()
    return [r[0] for r in rows]

def db_add_q(topic_key, question, opts, correct, exp):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO custom_q(topic_key,question,opt_a,opt_b,opt_c,opt_d,correct,explanation)
        VALUES(?,?,?,?,?,?,?,?)""",
        (topic_key, question, opts[0], opts[1], opts[2], opts[3], correct, exp))
    c.commit(); c.close()

def db_custom_q(topic_key):
    c = sqlite3.connect(DB_PATH)
    if topic_key == "all":
        rows = c.execute("SELECT question,opt_a,opt_b,opt_c,opt_d,correct,explanation FROM custom_q").fetchall()
    else:
        rows = c.execute("SELECT question,opt_a,opt_b,opt_c,opt_d,correct,explanation FROM custom_q WHERE topic_key=?", (topic_key,)).fetchall()
    c.close()
    return [{"q": r[0], "opts": list(r[1:5]), "ans": r[5], "exp": r[6]} for r in rows]

# ── SAVOLLAR ──────────────────────────────────────────────
TOPICS = {
    "1": {
        "uz": "Ishlab chiqarish omillari bozori",
        "ru": "Рынок факторов производства",
        "questions": [
            {"q":"Raqobatlashgan mehnat bozorida firmalar ishchi yollashni qachongacha davom ettiradi?","opts":["Ish haqi maksimal bo'lguncha","MRPL = ish haqi bo'lguncha","Ishchilar soni kamayguncha","Mehnatga taklif tugaguncha"],"ans":1,"exp":"Firma MRPL ish haqiga teng bo'lguncha ishchi yollaydi."},
            {"q":"Mehnatga talab kim tomonidan shakllantiriladi?","opts":["Uy xo'jaliklari","Firmalar","Banklar","Davlat"],"ans":1,"exp":"Mehnatga talab firmalar tomonidan shakllantiriladi."},
            {"q":"Mehnat bozori nimani ifodalaydi?","opts":["Tovarlar almashinuvi","Ishchi kuchi xizmatlari bozori","Kapital bozori","Valyuta bozori"],"ans":1,"exp":"Mehnat bozori ishchi kuchi xizmatlari sotiladi va sotib olinadigan bozor."},
            {"q":"Mehnatga taklif qaysi subyekt tomonidan shakllantiriladi?","opts":["Firmalar","Davlat","Uy xo'jaliklari","Banklar"],"ans":2,"exp":"Mehnatga taklifni uy xo'jaliklari (ishchilar) shakllantiradi."},
            {"q":"Raqobatlashgan mehnat bozorida ish haqi nimaning natijasida belgilanadi?","opts":["Davlat qarori","Ish beruvchi xohishi","Talab va taklif muvozanati","Inflyatsiya"],"ans":2,"exp":"Raqobatlashgan bozorda ish haqi talab va taklif muvozanati orqali belgilanadi."},
            {"q":"MRPL nimani bildiradi?","opts":["Mehnatning o'rtacha mahsuloti","Mehnatning chekli daromadliligi","Ish haqi","Umumiy daromad"],"ans":1,"exp":"MRPL — Marginal Revenue Product of Labour — mehnatning chekli daromadliligi."},
            {"q":"Raqobatlashgan mehnat bozorida MRPL qanday aniqlanadi?","opts":["MPL + P","MPL x P","MPL / P","MPL - P"],"ans":1,"exp":"MRPL = MPL x P (chekli mahsulot x narx)."},
            {"q":"Firma foydasini maksimal qilish sharti qaysi tenglik bilan ifodalanadi?","opts":["MPL = W","MRPL = W","AP = W","MP = W"],"ans":1,"exp":"Optimal ishchi soni: MRPL = W."},
            {"q":"Mehnat bozorida monopsoniya nimani anglatadi?","opts":["Bitta ish beruvchi","Ko'p ish beruvchi","Ko'p ishchi","Davlat bozori"],"ans":0,"exp":"Monopsoniya — bozorda yagona ish beruvchi mavjud bo'lgan holat."},
            {"q":"Monopsoniyada ish haqi qanday bo'ladi?","opts":["Nolga teng","Muvozanatga teng","Muvozanatdan past","Muvozanatdan yuqori"],"ans":2,"exp":"Monopsoniyada ish haqi muvozanat darajasidan past belgilanadi."},
            {"q":"Kapital bozorida foiz stavkasi nimani muvozanatlashtiradi?","opts":["Kapitalga talab va taklifni","Ish haqi","Narxlar darajasi","Inflyatsiya"],"ans":0,"exp":"Foiz stavkasi kapital bozorida talab va taklifni muvozanatlashtiradigan narx."},
            {"q":"Asosiy kapitalga qaysi resurs kiradi?","opts":["Xom ashyo","Yoqilg'i","Mashina-uskunalar","Ish haqi"],"ans":2,"exp":"Asosiy kapital — mashina-uskunalar, binolar, uzoq muddat xizmat qiladi."},
            {"q":"Aylanma kapitalning asosiy xususiyati nima?","opts":["Uzoq muddat xizmat qiladi","Bir siklda to'liq sarflanadi","Amortizatsiyalanadi","Qayta tiklanmaydi"],"ans":1,"exp":"Aylanma kapital bir ishlab chiqarish siklida to'liq sarflanadi."},
            {"q":"MRPL = MPL x P formulasi qaysi sharoitda amal qiladi?","opts":["Monopol mehnat bozorida","Monopsoniyada","Raqobatlashgan mahsulot bozorida","Davlat tartibga solgan bozorda"],"ans":2,"exp":"MRPL = MPL x P faqat raqobatlashgan mahsulot bozorida amal qiladi."},
            {"q":"Agar MPL = 4, narxi P = 25 bo'lsa, MRPL nechaga teng?","opts":["21","25","100","4"],"ans":2,"exp":"MRPL = MPL x P = 4 x 25 = 100."},
            {"q":"Minimal ish haqi monopsoniya sharoitida qanday natija berishi mumkin?","opts":["Bandlik kamayadi","Bandlik oshadi","Ta'sir qilmaydi","Ishsizlik ortadi"],"ans":1,"exp":"Monopsoniyada minimal ish haqi to'g'ri belgilansa, bandlik oshishi mumkin."},
            {"q":"Foiz stavkasi 10%, amortizatsiya 5%. Kapitalning foydalanuvchi xarajati?","opts":["5%","10%","15%","20%"],"ans":2,"exp":"Foydalanuvchi xarajati = foiz stavkasi + amortizatsiya = 10% + 5% = 15%."},
            {"q":"Mehnat taklifi oshsa, ish haqi qanday o'zgaradi?","opts":["Oshadi","Pasayadi","O'zgarmaydi","Nol bo'ladi"],"ans":1,"exp":"Taklif oshsa muvozanat narxi (ish haqi) pasayadi."},
            {"q":"Mehnat bozorida muvozanat nimani bildiradi?","opts":["Ish haqi nol","Ishchilar ko'p","Talab va taklif teng","Bandlik maksimal"],"ans":2,"exp":"Muvozanat — mehnatga talab va taklif teng bo'lgan holat."},
            {"q":"Ishlab chiqarish omillari bozori tahlilining asosiy maqsadi nima?","opts":["Narxlarni pasaytirish","Soliqni oshirish","Resurslardan optimal foydalanishni aniqlash","Foydani nolga tenglashtirish"],"ans":2,"exp":"Resurslardan samarali va optimal foydalanishni o'rgatadi."},
            {"q":"Iqtisodiy renta tushunchasi qaysi omillarga tatbiq etiladi?","opts":["Faqat yerga","Faqat mehnatga","Barcha cheklangan resurslarga","Faqat kapitalga"],"ans":2,"exp":"Iqtisodiy renta barcha taklifi cheklangan resurslarga tatbiq etiladi."},
            {"q":"Yuqori malakali ishchi ish haqining bir qismi nima sababdan renta hisoblanadi?","opts":["Mehnat ortiqcha","Malaka noyob","Talab past","Davlat belgilaydi"],"ans":1,"exp":"Noyob malaka taklifini cheklab qo'yadi — bu rentaning asosiy sababi."},
            {"q":"Iqtisodiy renta tushunchasi qaysi nazariyaga asoslanadi?","opts":["Klassik iqtisodiyot","Keyneschilik","Monetarizm","Institutsionalizm"],"ans":0,"exp":"Renta nazariyasi klassik iqtisodiyot (D. Rikardo) doirasida ishlab chiqilgan."},
            {"q":"Monopsoniyada bandlik darajasi raqobatnikiga nisbatan:","opts":["Yuqori","Past","Teng","Maksimal"],"ans":1,"exp":"Monopsonist ME = MRP qoidasida kamroq ishchi yollaydi — bandlik past."},
            {"q":"Mehnat bozorida iqtisodiy renta qachon yuzaga keladi?","opts":["Mehnat taklifi cheklanganda","Ishsizlikda","Inflyatsiyada","Davlat aralashganda"],"ans":0,"exp":"Iqtisodiy renta taklif cheklangan omillarda yuzaga keladi."},
        ]
    },
    "2": {
        "uz": "Umumiy muvozanat va samaradorlik",
        "ru": "Общее равновесие и эффективность",
        "questions": [
            {"q":"Umumiy muvozanat nimani anglatadi?","opts":["Faqat bitta bozorda narx muvozanatini","Barcha bozorlar bir vaqtning o'zida muvozanatga kelgan holatni","Davlat tomonidan belgilangan narxlar tizimini","Faqat ishlab chiqarish samaradorligini"],"ans":1,"exp":"Umumiy muvozanat — barcha bozorlar bir vaqtning o'zida muvozanatga kelgan holat."},
            {"q":"Pareto samarali holat qachon yuzaga keladi?","opts":["Kimningdir foydasi oshsa","Resurslar teng taqsimlanganda","Hech kimni yomonlashtirmasdan birovni yaxshilab bo'lmaganda","Davlat aralashuvi bo'lganda"],"ans":2,"exp":"Pareto samaradorligi: hech kimni yomonlashtirmasdan birovning holatini yaxshilab bo'lmaydi."},
            {"q":"Edgeworth qutisi nimani ko'rsatadi?","opts":["Ishlab chiqarish xarajatlarini","Barcha mumkin bo'lgan taqsimotlarni","Faqat muvozanat narxini","Soliq ta'sirini"],"ans":1,"exp":"Edgeworth qutisi ikkita iste'molchi o'rtasidagi barcha mumkin bo'lgan taqsimotlarni ko'rsatadi."},
            {"q":"Shartnoma egri chizig'i nimani ifodalaydi?","opts":["Davlat aralashuvi yo'llarini","Barcha adolatli taqsimotlarni","Barcha Pareto samarali taqsimotlarni","Narxlar nisbatini"],"ans":2,"exp":"Shartnoma (contract) egri chizig'i — barcha Pareto samarali taqsimotlar to'plami."},
            {"q":"Iste'molda samaradorlik sharti qaysi tenglik bilan ifodalanadi?","opts":["MRT = MRS","MRSa = MRSb","MC = MR","P = AC"],"ans":1,"exp":"Iste'molda samaradorlik: ikkala iste'molchining MRS lari teng bo'lishi kerak."},
            {"q":"Ishlab chiqarishda samaradorlik sharti:","opts":["MRS = MRT","MRTS1 = MRTS2","MC = P","AC = MC"],"ans":1,"exp":"Ishlab chiqarish samaradorligi sharti: barcha firmalar uchun MRTS lar teng bo'lishi kerak."},
            {"q":"Mahsulot (output) samaradorligi nimani talab qiladi?","opts":["MRS = MRT","MRS = MRTS","MC = AC","TR = TC"],"ans":0,"exp":"Mahsulot samaradorligi sharti: MRS = MRT."},
            {"q":"Raqobatli muvozanat nimani ta'minlaydi?","opts":["Faqat adolatlilikni","Faqat samaradorlikni","Samaradorlikni, lekin adolatlilikni emas","Teng daromadni"],"ans":2,"exp":"Raqobatli muvozanat samaradorlikni ta'minlaydi, lekin adolatli taqsimotni kafolatlamaydi."},
            {"q":"UPF nimani ko'rsatadi?","opts":["Ishlab chiqarish imkoniyatlarini","Iste'molchilar foydalilik kombinatsiyalarini","Narxlar harakatini","Soliq tushumlarini"],"ans":1,"exp":"UPF (Utility Possibility Frontier) — iste'molchilar foydalilik kombinatsiyalarini ko'rsatadi."},
            {"q":"PPF ichidagi nuqtalar nimani bildiradi?","opts":["Imkonsiz holat","Samarali ishlab chiqarish","Resurslardan to'liq foydalanilmagan holat","Muvozanat"],"ans":2,"exp":"PPF ichidagi nuqtalar resurslardan to'liq foydalanilmagan (samarasiz) holatni bildiradi."},
            {"q":"Pareto mezonining asosiy cheklovi nimada?","opts":["Samaradorlikni o'lchay olmaydi","Tenglikni hisobga olmaydi","Bozorni inkor qiladi","Texnologiyani hisobga olmaydi"],"ans":1,"exp":"Pareto mezoni samaradorlikni o'lchaydi, lekin taqsimot tengligini hisobga olmaydi."},
            {"q":"Birinchi farovonlik teoremasi mazmuniga mos nima?","opts":["Har qanday raqobatli muvozanat Pareto samarali","Har qanday Pareto samarali holat raqobatli","Davlat har doim samarali","Tenglik avtomatik yuzaga keladi"],"ans":0,"exp":"1-farovonlik teoremasi: har qanday raqobatli muvozanat Pareto samarali bo'ladi."},
            {"q":"Ikkinchi farovonlik teoremasi nimani ta'kidlaydi?","opts":["Davlat samaradorlikni buzadi","Har qanday Pareto samarali holatni raqobatli muvozanatga aylantirish mumkin","Raqobat tenglik beradi","Narxlar ahamiyatsiz"],"ans":1,"exp":"2-farovonlik teoremasi: istalgan Pareto samarali holatga qayta taqsimlash orqali erishish mumkin."},
            {"q":"Adolatlilik nimaga asoslanadi?","opts":["Iqtisodiy qonunlarga","Texnologiyaga","Ijtimoiy va normativ baholarga","Bozor signallariga"],"ans":2,"exp":"Adolatlilik — normativ tushuncha bo'lib, ijtimoiy qadriyatlar va normativ baholarga asoslanadi."},
            {"q":"Qisman muvozanat tahlilining asosiy farazi qaysi?","opts":["Barcha bozorlar o'zgaradi","Davlat aralashuvi mavjud","Boshqa bozorlar o'zgarmas deb olinadi","Narxlar qat'iy belgilanadi"],"ans":2,"exp":"Qisman muvozanat tahlilida boshqa bozorlar o'zgarmas (ceteris paribus) deb olinadi."},
        ]
    },
    "3": {
        "uz": "Monopoliya va monopsoniya",
        "ru": "Монополия и монопсония",
        "questions": [
            {"q":"Agar talab elastikligi Ed = -4 bo'lsa, Lerner indeksi L nechaga teng?","opts":["0.25","4","-0.25","0"],"ans":0,"exp":"L = 1/|Ed| = 1/4 = 0.25"},
            {"q":"Talab: Q = 200 - 2P. MC = 20. Optimal ishlab chiqarish hajmi?","opts":["40","60","80","100"],"ans":2,"exp":"P = 100 - Q/2, MR = 100 - Q. MR=MC: 100-Q=20, Q=80."},
            {"q":"3 ta firma ulushlari: 50%, 30%, 20%. HHI?","opts":["3800","2500","10000","5000"],"ans":0,"exp":"HHI = 50^2 + 30^2 + 20^2 = 2500+900+400 = 3800."},
            {"q":"Agar monopolist MR < MC bo'lsa u nima qiladi?","opts":["Ishlab chiqarishni oshiradi","O'zgartirmaydi","Narxni oshiradi","Ishlab chiqarishni kamaytiradi"],"ans":3,"exp":"MR < MC bo'lsa, qo'shimcha ishlab chiqarish zararli — hajm kamaytiriladi."},
            {"q":"Monopsoniyada optimal shart:","opts":["MRP = ME","W = MRP","MR = MC","W = ME"],"ans":0,"exp":"Monopsoniyada optimal: MRP = ME."},
            {"q":"Agar P = 120 va MC = 60 bo'lsa, Lerner indeksi?","opts":["0","1","0.5","2"],"ans":2,"exp":"L = (P - MC)/P = (120 - 60)/120 = 0.5"},
            {"q":"HHI = 10000 nimani bildiradi?","opts":["Mukammal raqobat","Past konsentratsiya","Sof monopoliya","Oligopoliya"],"ans":2,"exp":"HHI = 10000 — faqat bitta firma mavjud, ya'ni sof monopoliya."},
            {"q":"Monopolist talabning qaysi qismida ishlaydi?","opts":["Noelastik","Birlik elastik","Elastik","Vertikal"],"ans":2,"exp":"Monopolist faqat elastik qismda ishlaydi, chunki noelastik qismda MR < 0."},
            {"q":"Sof monopoliyada narx:","opts":["MC ga teng","ATC dan kichik","MC dan yuqori","MR ga teng"],"ans":2,"exp":"Monopoliyada P > MC — narx chekli xarajatdan yuqori belgilanadi."},
            {"q":"MR = MC sharti nimani beradi?","opts":["Maksimal TR","Minimal AC","Maksimal foyda","Nol foyda"],"ans":2,"exp":"MR = MC — foyda maksimallashtirilishi sharti."},
            {"q":"Lerner indeksi 0 bo'lsa:","opts":["Sof monopoliya","Mukammal raqobat","Oligopoliya","Monopsoniya"],"ans":1,"exp":"L = 0 bo'lsa P = MC — mukammal raqobat bozori."},
            {"q":"Deadweight loss (DWL) sababi?","opts":["P = MC","Q optimal","Ishlab chiqarish ko'p","P > MC"],"ans":3,"exp":"Monopoliyada P > MC bo'lgani uchun ishlab chiqarish optimaldan kam — DWL yuzaga keladi."},
            {"q":"Monopolistning talab elastikligi |Ed| = 3 bo'lsa, narx MC dan necha foiz yuqori?","opts":["25%","33%","50%","75%"],"ans":1,"exp":"L = 1/|Ed| = 1/3 = 33%."},
            {"q":"Monopsoniyada mehnat taklifi W = 10 + L bo'lsa, ME nimaga teng?","opts":["10 + L","10 + 2L","20 + L","L"],"ans":1,"exp":"TC = W*L = (10+L)*L. ME = d(TC)/dL = 10 + 2L."},
            {"q":"Monopsoniyada bandlik darajasi raqobatnikiga nisbatan:","opts":["Yuqori","Past","Teng","Maksimal"],"ans":1,"exp":"Monopsonist ME = MRP qoidasida kamroq ishchi yollaydi — bandlik past."},
        ]
    },
    "4": {
        "uz": "Monopoliyada narxlar strategiyasi",
        "ru": "Ценовая стратегия монополии",
        "questions": [
            {"q":"1-darajali diskriminatsiyada ishlab chiqarish hajmi qaysi nuqtada aniqlanadi?","opts":["MR = MC","P = MC","MR = 0","ATC minimum"],"ans":1,"exp":"1-daraja diskriminatsiyada har bir birlik WTP ga sotiladi, optimal Q: P = MC."},
            {"q":"Mukammal narxlar diskriminatsiyasida iste'molchi ortiqchaligi:","opts":["Maksimal bo'ladi","Nolga teng bo'ladi","Yarimga kamayadi","MC ga teng bo'ladi"],"ans":1,"exp":"Mukammal diskriminatsiyada monopolist barcha iste'molchi ortiqchasini oladi — u nolga teng bo'ladi."},
            {"q":"Talab: P = 200 - Q, MC = 20. Mukammal diskriminatsiyada foyda?","opts":["8100","16200","9000","18000"],"ans":1,"exp":"Q* = 180 (P=MC=20). Foyda = 1/2 * 180 * 180 = 16200."},
            {"q":"2-darajali diskriminatsiya nimaga asoslanadi?","opts":["Daromadga","Hududga","Hajmga","Yoshga"],"ans":2,"exp":"2-daraja diskriminatsiya sotib olinadigan miqdor (hajm) ga qarab turli narxlar belgilashga asoslanadi."},
            {"q":"3-darajali diskriminatsiyada optimal shart:","opts":["P1 = P2","MR1 = MR2 = MC","MC1 = MC2","TR max"],"ans":1,"exp":"3-daraja diskriminatsiyada optimal: barcha segmentlarda MR MC ga teng bo'lishi kerak."},
            {"q":"Qaysi segmentda narx yuqori belgilanadi?","opts":["Elastik","Noelastik","MC past","Q katta"],"ans":1,"exp":"Talab noelastik bo'lgan segmentda narx yuqori belgilanadi."},
            {"q":"Agar |Ed1| = 2 va |Ed2| = 4 bo'lsa, qaysi segmentda narx yuqori?","opts":["1-segment","2-segment","Teng","Aniqlab bo'lmaydi"],"ans":0,"exp":"L = 1/|Ed|. 1-segment: L=0.5 katta → narx yuqori."},
            {"q":"1-darajali diskriminatsiyada DWL:","opts":["Mavjud","Nol","Maksimal","Yarim monopol"],"ans":1,"exp":"Mukammal diskriminatsiyada Q = Qraqobat bo'ladi — DWL yo'q."},
            {"q":"3-darajali diskriminatsiya umumiy foydani:","opts":["Kamaytiradi","Oshiradi","Nolga tushiradi","MC ga teng"],"ans":1,"exp":"Segmentlash va farqlangan narx belgilash yagona narxga nisbatan foydani oshiradi."},
            {"q":"2-qismli tarifda optimal T:","opts":["Minimal","Nol","Iste'molchi ortiqchaligiga teng","MC"],"ans":2,"exp":"Optimal kirish to'lovi T = CS (iste'molchi ortiqchaligi) ga teng belgilanadi."},
            {"q":"Ikki qismli tarifda agar P = MC bo'lsa:","opts":["Foyda nol","Foyda faqat T dan","TR nol","Zarar"],"ans":1,"exp":"P = MC bo'lsa savdo foydasi nol, lekin kirish to'lovi T dan foyda olinadi."},
            {"q":"Agar qayta sotish erkin bo'lsa:","opts":["Diskriminatsiya mumkin","Narxlar tenglashadi","P oshadi","MC o'zgaradi"],"ans":1,"exp":"Qayta sotish erkin bo'lsa narxlar tenglashadi — diskriminatsiya buziladi."},
            {"q":"3-darajali diskriminatsiyada umumiy Q:","opts":["Monopol Q dan kichik","Monopol Q dan katta","Monopol Q ga teng","Nol"],"ans":1,"exp":"Diskriminatsiya bilan umumiy Q yagona monopol Q dan ko'proq bo'ladi."},
            {"q":"Mukammal narxlar diskriminatsiyasining asosiy sharti:","opts":["Ko'p firma bo'lishi","Qayta sotish mumkin bo'lishi","Har xaridor WTP ni bilish","Elastiklik bir xil bo'lishi"],"ans":2,"exp":"Mukammal diskriminatsiya uchun monopolist har bir xaridorning WTP ni bilishi zarur."},
            {"q":"Ikki qismli tarif optimal tanlovi:","opts":["Faqat P","Faqat T","P va T birgalikda optimallashtiriladi","MC"],"ans":2,"exp":"Optimal 2 qismli tarifda P va T bir vaqtda optimallashtiriladi."},
        ]
    }
}

# ── SERTIFIKAT ────────────────────────────────────────────
def make_cert(full_name, score, total, pct, topic, lang):
    if not PIL_OK:
        return None
    try:
        W, H = 900, 580
        img = Image.new("RGB", (W, H), "#0D1B2A")
        d   = ImageDraw.Draw(img)
        for i in range(3):
            d.rectangle([8+i*5, 8+i*5, W-8-i*5, H-8-i*5], outline="#C9A84C", width=1)
        d.rectangle([0, 55, W, 150], fill="#1B2A40")
        title = "SERTIFIKAT" if lang == "uz" else "СЕРТИФИКАТ"
        sub   = "Iqtisodiyot bo'yicha test muvaffaqiyatli topshirildi" if lang == "uz" else "Тест по экономике успешно пройден"
        d.text((W//2, 95),  title, fill="#C9A84C", anchor="mm")
        d.text((W//2, 135), sub,   fill="#AAAAAA",  anchor="mm")
        d.text((W//2, 220), full_name, fill="#FFFFFF", anchor="mm")
        d.line([(140, 250), (W-140, 250)], fill="#C9A84C", width=1)
        d.text((W//2, 290), topic, fill="#88BBEE", anchor="mm")
        grade = (TX[lang]["grade_5"] if pct>=85 else TX[lang]["grade_4"] if pct>=70
                 else TX[lang]["grade_3"] if pct>=55 else TX[lang]["grade_2"])
        d.text((W//2, 350), f"{score}/{total}  ({pct}%)", fill="#66EE88", anchor="mm")
        d.text((W//2, 390), grade, fill="#FFDD44", anchor="mm")
        d.text((W//2, 460), datetime.now().strftime("%d.%m.%Y"), fill="#888888", anchor="mm")
        d.text((W//2, 500), "Super Quiz Bot", fill="#445566", anchor="mm")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        log.warning(f"cert error: {e}")
        return None

# ── HELPERS ───────────────────────────────────────────────
def get_qs(key):
    qs = []
    if key == "all":
        for tp in TOPICS.values():
            qs.extend(tp["questions"])
    else:
        qs = TOPICS[key]["questions"].copy()
    qs += db_custom_q(key)
    random.shuffle(qs)
    return qs

def tname(key, uid):
    lang = user_lang.get(uid, "uz")
    if key == "all":
        return TX[lang]["all_topics"]
    return TOPICS[key][lang]

def grade(uid, pct):
    if pct >= 85: return TX[user_lang.get(uid,"uz")]["grade_5"]
    if pct >= 70: return TX[user_lang.get(uid,"uz")]["grade_4"]
    if pct >= 55: return TX[user_lang.get(uid,"uz")]["grade_3"]
    return TX[user_lang.get(uid,"uz")]["grade_2"]

def emoji(pct):
    return "🏆" if pct>=85 else "✅" if pct>=70 else "📝" if pct>=55 else "❌"

# ── TIMER ─────────────────────────────────────────────────
async def timer_job(context):
    d   = context.job.data
    uid = d["uid"]
    pid = d["pid"]
    if uid not in user_state:
        return
    st = user_state[uid]
    if pid not in st["poll_map"]:
        return
    del st["poll_map"][pid]
    st["index"] += 1
    await context.bot.send_message(st["cid"], txt(uid, "time_up"))
    await send_q(context, uid, st["cid"])

# ── SEND QUESTION ─────────────────────────────────────────
async def send_q(context, uid, cid):
    st  = user_state.get(uid)
    if not st:
        return
    idx = st["index"]
    qs  = st["qs"]
    if idx >= len(qs):
        s   = st["score"]
        tot = len(qs)
        pct = db_save_result(uid, st["key"], s, tot)
        lang = user_lang.get(uid, "uz")
        await context.bot.send_message(
            cid,
            txt(uid, "result", s=s, total=tot, p=pct,
                emoji=emoji(pct), grade=grade(uid, pct))
        )
        c    = sqlite3.connect(DB_PATH)
        row  = c.execute("SELECT full_name FROM users WHERE user_id=?", (uid,)).fetchone()
        c.close()
        name = row[0] if row else "User"
        cert = make_cert(name, s, tot, pct, tname(st["key"], uid), lang)
        if cert:
            await context.bot.send_photo(cid, photo=cert,
                caption=f"{name} — {s}/{tot} ({pct}%)")
        del user_state[uid]
        return
    q   = qs[idx]
    msg = await context.bot.send_poll(
        cid,
        question=f"{txt(uid,'q_label',i=idx+1,n=len(qs))}\n\n{q['q']}",
        options=q["opts"],
        type="quiz",
        correct_option_id=q["ans"],
        explanation=q["exp"],
        is_anonymous=False,
    )
    st["poll_map"][msg.poll.id] = q["ans"]
    context.job_queue.run_once(
        timer_job, TIMER_SEC,
        name=f"t_{uid}",
        data={"uid": uid, "pid": msg.poll.id}
    )

# ── HANDLERS ──────────────────────────────────────────────
async def cmd_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    db_upsert(uid, u.effective_user.username, u.effective_user.full_name)
    lang = db_lang(uid)
    user_lang[uid] = lang
    kb = [[InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang_uz"),
           InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]]
    await u.message.reply_text(TX[lang]["choose_lang"],
                               reply_markup=InlineKeyboardMarkup(kb))

async def cb_lang(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = u.callback_query; await q.answer()
    uid  = q.from_user.id
    lang = q.data.split("_")[1]
    user_lang[uid] = lang
    db_lang(uid, lang)
    await q.edit_message_text(txt(uid, "welcome", name=q.from_user.first_name))
    await show_menu(uid, q.message.chat_id, ctx)

async def show_menu(uid, cid, ctx):
    lang = user_lang.get(uid, "uz")
    kb = [[InlineKeyboardButton(f"1️⃣ {TOPICS['1'][lang]}", callback_data="t_1")],
          [InlineKeyboardButton(f"2️⃣ {TOPICS['2'][lang]}", callback_data="t_2")],
          [InlineKeyboardButton(f"3️⃣ {TOPICS['3'][lang]}", callback_data="t_3")],
          [InlineKeyboardButton(f"4️⃣ {TOPICS['4'][lang]}", callback_data="t_4")],
          [InlineKeyboardButton(TX[lang]["all_topics"],      callback_data="t_all")],
          [InlineKeyboardButton("🏆 TOP",    callback_data="top_all"),
           InlineKeyboardButton("📊 Stats",  callback_data="stats")]]
    await ctx.bot.send_message(cid, txt(uid, "main_menu"),
                               reply_markup=InlineKeyboardMarkup(kb))

async def cb_topic(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = u.callback_query; await q.answer()
    uid = q.from_user.id
    key = q.data.split("_")[1]
    qs  = get_qs(key)
    user_state[uid] = {"qs": qs, "index": 0, "score": 0,
                       "poll_map": {}, "key": key, "cid": q.message.chat_id}
    lang = user_lang.get(uid, "uz")
    await q.edit_message_text(
        txt(uid, "quiz_start", topic=tname(key, uid), n=len(qs), timer=TIMER_SEC))
    await send_q(ctx, uid, q.message.chat_id)

async def poll_answer(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    a   = u.poll_answer
    uid = a.user.id
    if uid not in user_state:
        return
    st  = user_state[uid]
    pid = a.poll_id
    if pid not in st["poll_map"]:
        return
    for job in ctx.job_queue.get_jobs_by_name(f"t_{uid}"):
        job.schedule_removal()
    if (a.option_ids[0] if a.option_ids else -1) == st["poll_map"][pid]:
        st["score"] += 1
    st["index"] += 1
    del st["poll_map"][pid]
    await send_q(ctx, uid, st["cid"])

async def cmd_top(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = u.effective_user.id
    lang = user_lang.get(uid, "uz")
    kb = [[InlineKeyboardButton(f"{TOPICS[k][lang]}", callback_data=f"top_{k}")] for k in TOPICS]
    kb.append([InlineKeyboardButton(TX[lang]["all_topics"], callback_data="top_all")])
    await u.message.reply_text("🏆 Mavzu:", reply_markup=InlineKeyboardMarkup(kb))

async def cb_top(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = u.callback_query; await q.answer()
    uid  = q.from_user.id
    key  = q.data.split("_")[1]
    rows = db_leaderboard(key)
    if not rows:
        await q.edit_message_text(txt(uid, "top_empty"))
        return
    md   = ["🥇","🥈","🥉"]+["🏅"]*7
    lines = [f"🏆 {tname(key, uid)}"]
    for i, (nm, pct, sc, tot) in enumerate(rows):
        lines.append(f"{md[i]} {nm} — {pct}%  ({sc}/{tot})")
    await q.edit_message_text("\n".join(lines))

async def cmd_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    us, ts, avg = db_stats()
    await u.message.reply_text(txt(uid, "stats", u=us, t=ts, a=avg))

async def cb_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = u.callback_query; await q.answer()
    uid = q.from_user.id
    us, ts, avg = db_stats()
    await q.edit_message_text(txt(uid, "stats", u=us, t=ts, a=avg))

async def cmd_admin(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid, "not_admin")); return
    us, ts, avg = db_stats()
    await u.message.reply_text(
        f"Admin panel\n\nFoydalanuvchilar: {us}\nTestlar: {ts}\nO'rtacha: {avg}%\n\n"
        f"/broadcast Matn — Xabar yuborish\n"
        f"/addq — Savol qo'shish"
    )

async def cmd_broadcast(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid, "not_admin")); return
    msg = " ".join(ctx.args)
    if not msg:
        await u.message.reply_text("Xabar kiriting: /broadcast Salom!"); return
    uids = db_all_uids()
    sent = 0
    for i in uids:
        try:
            await ctx.bot.send_message(i, f"📢 {msg}"); sent += 1
        except Exception:
            pass
    await u.message.reply_text(txt(uid, "bcast_ok", n=sent))

async def cmd_addq(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS:
        await u.message.reply_text(txt(uid, "not_admin")); return
    raw = u.message.text.replace("/addq", "").strip()
    if not raw:
        await u.message.reply_text(txt(uid, "addq_help")); return
    try:
        lines = {ln.split(":",1)[0].strip(): ln.split(":",1)[1].strip()
                 for ln in raw.splitlines() if ":" in ln}
        db_add_q(lines.get("TOPIC","1"), lines["Q"],
                 [lines["A"],lines["B"],lines["C"],lines["D"]],
                 int(lines["ANS"]), lines.get("EXP",""))
        await u.message.reply_text(txt(uid, "addq_ok"))
    except Exception as e:
        log.warning(f"addq: {e}")
        await u.message.reply_text(txt(uid, "addq_err"))

async def cmd_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    await u.message.reply_text(txt(uid, "help"))

# ── MAIN ──────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("top",       cmd_top))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("admin",     cmd_admin))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("addq",      cmd_addq))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CallbackQueryHandler(cb_lang,  pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(cb_topic, pattern="^t_"))
    app.add_handler(CallbackQueryHandler(cb_top,   pattern="^top_"))
    app.add_handler(CallbackQueryHandler(cb_stats, pattern="^stats$"))
    app.add_handler(PollAnswerHandler(poll_answer))
    log.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
