# PythonAnywhere'ga joylash

Quyidagi amallar loyihani PythonAnywhere'da ishga tushirish uchun. Bu repo tuzilmasida
`manage.py` va `root/settings.py` loyiha ildizida joylashgan.

## 1. Kod va virtual muhit

PythonAnywhere'da **Bash console** ochib, repozitoriyangiz manzilini ishlating:

```bash
git clone <REPOSITORY_URL> demo_day
cd ~/demo_day
mkvirtualenv --python=/usr/bin/python3.13 xonsaroy-venv
pip install -r requirements.txt
```

Web ilovasini yaratishda virtual muhit bilan bir xil Python versiyasini tanlang.
Agar hisobingizda Python 3.13 mavjud bo'lmasa, PythonAnywhere taklif qiladigan va
`requirements.txt` talablariga mos versiyani tanlang.

## 2. Maxfiy sozlamalar

`~/demo_day/.env` faylini PythonAnywhere Files sahifasida yarating (`.env.example`
namunasidan foydalaning). `SECRET_KEY` uchun konsolda yangi kalit yarating:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Chiqqan kalitni `.env` ichiga yozing; uni GitHub'ga yubormang. Quyidagi qiymatlarni
haqiqiy domen va integratsiyalaringizga moslang:

```dotenv
DEBUG=False
SECRET_KEY=<generated-secret>
ALLOWED_HOSTS=yourusername.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com
DJANGO_ADMIN_PATH=<private-random-path>
```

Admin sahifasining maxsus manzilini terminalda yarating:

```bash
python -c "import secrets; print('panel-' + secrets.token_urlsafe(24))"
```

Chiqqan qiymatni `.env` faylidagi `DJANGO_ADMIN_PATH` ga yozing (`https://` yoki
boshlang'ich `/` qo'shmang). Production'da standart `/admin/` bosh sahifaga
yo'naltiriladi; boshqaruv paneli faqat siz belgilagan maxsus manzilda ochiladi.
Maxsus manzil login/parol va Django staff ruxsatlarini almashtirmaydi.

Custom domen ulangan bo'lsa, uni `ALLOWED_HOSTS` ro'yxatiga host nomi sifatida,
`CSRF_TRUSTED_ORIGINS` ro'yxatiga esa `https://` bilan qo'shing. Bir nechta
qiymatni vergul bilan ajrating. Telegram, email va Google/GitHub login ishlatilsa,
tegishli o'zgaruvchilarni ham `.env` ga kiriting.

## 3. Django Web app va WSGI

PythonAnywhere **Web** sahifasida **Manual configuration** bilan web app yarating
va virtual muhit sifatida `xonsaroy-venv` ni ko'rsating.
Web sahifadagi WSGI faylini ochib, Django bo'limiga quyidagini kiriting.
`yourusername` ni o'z PythonAnywhere username'ingizga almashtiring:

```python
import os
import sys

project_path = '/home/yourusername/demo_day'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

`root/settings.py` loyiha ichidagi `.env` faylini o'zi yuklaydi. PythonAnywhere
saytingiz uchun HTTPS yoqilganini tekshiring; production sozlamalarida session va
CSRF cookie'lari faqat HTTPS orqali yuboriladi.

## 4. Mavjud ma'lumotlar, migratsiyalar va statik fayllar

`db.sqlite3` va `media/` Git'ga kiritilmaydi. Saytdagi mavjud ma'lumot va
rasmlarni saqlash kerak bo'lsa, ularni repozitoriydan alohida ravishda
PythonAnywhere'ga yuklang:

- `db.sqlite3` faylini `~/demo_day/db.sqlite3` ga yuklang. Serverda avvaldan
  ishlayotgan baza bo'lsa, uni almashtirishdan oldin backup oling.
- `media/` ichidagi fayllarni `~/demo_day/media/` ga nusxalang.

Bash console'da:

```bash
cd ~/demo_day
workon xonsaroy-venv
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

**Web → Static files** bo'limida quyidagi mapping'larni qo'shing, username'ni
almashtiring va web app'ni reload qiling:

| URL | Path |
|---|---|
| `/static/` | `/home/yourusername/demo_day/staticfiles` |
| `/media/` | `/home/yourusername/demo_day/media` |

`media/` mapping'ini faqat media fayllar ishlatilsa qo'shing. Kod yoki static
fayllar o'zgarganda `collectstatic` ni qayta ishlating.

## 5. Telegram bot (ixtiyoriy)

Bot veb-saytning WSGI ichida avtomatik ishlamaydi. PythonAnywhere'ning **Tasks**
sahifasida Always-on task mavjud bo'lgan tarifda quyidagi komandani alohida
vazifa sifatida qo'shing:

```bash
/home/yourusername/.virtualenvs/xonsaroy-venv/bin/python /home/yourusername/demo_day/manage.py runbot
```

`.env` da `TELEGRAM_BOT_TOKEN` va kerak bo'lsa `TELEGRAM_ADMIN_CHAT_ID` to'ldirilgan
bo'lishi kerak. Always-on task pullik tarifda mavjud; bepul tarifda bot'ni doimiy
ishlatish kafolatlanmaydi.

## 6. Tekshirish

Web app'ni reload qiling va PythonAnywhere'dagi **Error log** ni tekshiring. Sayt
ochilmasa, odatda `SECRET_KEY`/`ALLOWED_HOSTS`, virtual muhit yo'li yoki WSGI
`project_path` ni to'g'rilash kerak bo'ladi.
