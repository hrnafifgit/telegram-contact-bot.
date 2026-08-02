# 🤖 بوت تليجرام للتواصل والاستقبال (Telegram Proxy / Contact Bot)

بوت استقبال رسائل احترافي يعمل كوسيط بين المستخدمين وحسابك الشخصي على تليجرام، مصمم بلغة **Python** باستخدام مكتبة **`python-telegram-bot`** الحديثة (v20+ Async) وقاعدة بيانات **SQLite**.

---

## 🌟 المميزات

1. **استقبال الرسائل من أي مستخدم**: يستقبل البوت رسائل المستخدمين في أي وقت.
2. **إشعار تفصيلي للمدير**: يستخرج البوت ويرسل الإشعار بالشكل التالي:
   ```text
   📩 رسالة جديدة

   👤 الاسم: أحمد علي
   🔗 Username: @ahmed_ali
   🆔 ID: 123456789
   🕒 الوقت: 2026-08-02 21:49:00

   💬 الرسالة:
   مرحباً، أود الاستفسار عن الخدمات المتاحة.
   ```
3. **نظام الرد المباشر والسرّي**: يمكنك الرد على المستخدم فوراً عبر خاصية **الرد (Reply)** في تليجرام على رسالة الإشعار نفسها. يصل الرد للمستخدم من البوت دون كشف حسابك الشخصي.
4. **تخزين الآثار والتفاعلات**: حفظ بيانات المستخدمين والرسائل والربط بينها في قاعدة بيانات SQLite.
5. **دعم الوسائط**: دعم الرسائل النصية، الصور، الفيديوهات، الملفات والرسائل الصوتية.

---

## 📁 هيكل المشروع

```text
bot/
├── .env.example            # نموذج ملف متغيرات البيئة
├── requirements.txt        # المكتبات المطلوبة
├── config.py               # إدارة وقراءة الإعدادات
├── database.py             # التعامل مع قاعدة البيانات SQLite غير المتزامنة
├── handlers/
│   ├── __init__.py
│   ├── start.py            # معالج أمر البدء /start
│   ├── user_messages.py    # استقبال وتنسيق رسائل المستخدمين
│   └── admin_replies.py    # معالج ردود المدير على الرسائل
├── main.py                 # نقطة تشغيل البوت الرئيسية
└── README.md               # دليل الاستخدام والتشغيل
```

---

## 🛠️ دليل الإعداد والتشغيل الخطوة بخطوة

### 1️⃣ إنشاء البوت من BotFather
1. افتح تطبيق Telegram وابحث عن البوت الرسمي: **[@BotFather](https://t.me/BotFather)**.
2. أرسل الأمر `/newbot`.
3. أدخل اسماً للبوت (مثل: `My Contact Bot`).
4. أدخل اسم مستخدم (Username) ينتهي بـ `bot` (مثل: `MyContactBridge_bot`).
5. سيعطيك BotFather رمز التوكن الخاص بالبوت (**API Token**)، احفظه في مكان آمن.

---

### 2️⃣ الحصول على Telegram ID الخاص بالمدير
لتحصل على الرقم التعريفي لحسابك الشخصي:
1. ابحث عن البوت: **[@userinfobot](https://t.me/userinfobot)** أو **[@rawdata_bot](https://t.me/rawdata_bot)**.
2. أرسل `/start` وسيقوم البوت بإظهار رقم الـ `Id` الخاص بك (مثال: `987654321`).

---

### 3️⃣ التهيئة والتشغيل المحلي (Local Running)

#### أ. تثبيت Python وتأكيد النسخة (Python 3.10+)
تأكد من وجود Python مثبت على جهازك عبر تنفيذ الأمر:
```bash
python --version
```

#### ب. إنشاء ملف `.env`
قم بإنشاء ملف باسم `.env` في المجلد الرئيسي للمشروع، وضع فيه التوكن و ID الخاص بك:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
ADMIN_ID=987654321
DB_PATH=bot_database.db
```

#### ج. تثبيت المكتبات المطلوبة
افتح موجه الأوامر (Terminal / Command Prompt) في مجلد المشروع ونفذ:
```bash
pip install -r requirements.txt
```

#### د. تشغيل البوت
```bash
python main.py
```
ستظهر لك رسالة في التيرمينال تؤكد عمل البوت:
`🤖 البوت يعمل الآن ويستقبل الرسائل بنجاح!`

---

## ☁️ رفع البوت على سيرفر ليعمل 24/7

لتشغيل البوت بشكل دائم بدون انقطاع على خادم Linux (مثل VPS من DigitalOcean, Hetzner, AWS, إلخ)، يمكنك استخدام إحدى الطريقتين التاليين:

### الطريقة الأولى: باستخدام خدمة النظام `systemd` (موصى بها لسيرفرات Linux)

1. **انقل ملفات المشروع إلى السيرفر** (مثلاً في المسار `/opt/telegram-bot`).
2. **قم بتثبيت البيئة الافتراضية والمكتبات على السيرفر**:
   ```bash
   cd /opt/telegram-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **أنشئ ملف خدمة `systemd`**:
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
4. **ضع المحتوى التالي داخل الملف**:
   ```ini
   [Unit]
   Description=Telegram Proxy Contact Bot Service
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/telegram-bot
   ExecStart=/opt/telegram-bot/venv/bin/python main.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
5. **تفعيل وتشغيل الخدمة**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```
6. **التحقق من حالة البوت وقراءة السجلات**:
   ```bash
   sudo systemctl status telegram-bot
   sudo journalctl -u telegram-bot -f
   ```

---

### الطريقة الثانية: باستخدام Docker

أنشئ ملف `Dockerfile` في مجلد المشروع بالمحتوى التالي:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

ثم قم ببناء وتشغيل حاوية Docker:
```bash
docker build -t telegram-contact-bot .
docker run -d --name my_bot --restart always telegram-contact-bot
```

---

## 🧪 اختبار البوت

1. قم بفتح البوت من حساب شخصي آخر (ليس حساب المدير).
2. أرسل الأمر `/start` ثم أرسل رسالة نصية أو صورة.
3. ستصلك رسالة إشعار فورية على حساب المدير المعتمد بالشكل المطلوب.
4. اضغط **Reply** في تليجرام على رسالة الإشعار واكتب ردك، وسيتم تسليمه للمستخدم مباشرةً وبشكل مجهول.
