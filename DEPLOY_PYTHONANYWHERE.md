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

`.env.example` faylidan foydalanib, PythonAnywhere Files sahifasida
`~/demo_day/.env` faylini yarating. `SECRET_KEY` uchun konsolda yangi kalit yarating:

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
qiymatni vergul bilan ajrating. Telegram va email ishlatilsa, tegishli
o'zgaruvchilarni ham `.env` ga kiriting.

Xonadon bronini email kodi bilan tasdiqlash uchun `EMAIL_HOST_USER` va
`EMAIL_HOST_PASSWORD` ni (Gmail uchun ilova parolini) albatta sozlang.
Email yuborilmasa, bron tasdiqlanmaydi va xonadon yana bo‘sh holatga qaytadi.

### Google va GitHub orqali kirish

Google yoki GitHub tugmalari faqat tegishli Client ID va Secret `.env` faylida
bo'lganda faollashadi. Google Cloud Console'da OAuth 2.0 Client ID (Web
application) yarating va **Authorized redirect URI** ga quyidagini kiriting:

```text
https://yourusername.pythonanywhere.com/accounts/google/login/callback/
```

GitHub'da **OAuth App** yarating va **Authorization callback URL** sifatida
quyidagini kiriting:

```text
https://yourusername.pythonanywhere.com/accounts/github/login/callback/
```

`yourusername.pythonanywhere.com` o'rniga haqiqiy PythonAnywhere domeningizni
yozing. Custom domen ishlatilsa, OAuth sozlamalaridagi callback manzillarida ham
o'sha domenni ishlating. Google Client ID/Secret va GitHub Client ID/Secret
qiymatlarini PythonAnywhere'dagi `~/demo_day/.env` fayliga kiriting:

```dotenv
GOOGLE_CLIENT_ID=<Google Client ID>
GOOGLE_CLIENT_SECRET=<Google Client Secret>
GITHUB_CLIENT_ID=<GitHub Client ID>
GITHUB_CLIENT_SECRET=<GitHub Client Secret>
```

Ishlatmaydigan provayder uchun qiymatlarni bo'sh qoldirish mumkin. Bu
ma'lumotlarni chatga yoki GitHub'ga yubormang. Saqlagandan so'ng Bash console'da
loyiha virtual muhitini faollashtirib, sozlamalar o'qilganini tekshiring:

```bash
cd ~/demo_day
workon xonsaroy-venv
python manage.py shell -c "from django.conf import settings; print('Google:', settings.GOOGLE_OAUTH_ENABLED, 'GitHub:', settings.GITHUB_OAUTH_ENABLED)"
```

Kerakli provayder uchun `True` chiqishi kerak. So'ng **Web → Reload** ni bosing.
Bu kalitlarsiz ham email va parol orqali ro'yxatdan o'tish ishlayveradi; faqat
Google/GitHub tugmalari o'chirilgan bo'ladi.

Telegram bot va uning saytdagi tugmalari uchun `.env` ga quyidagilarni ham
qo'shing. Tokenni BotFather beradi; tokenni chatga yoki GitHub'ga yubormang.

```dotenv
TELEGRAM_BOT_TOKEN=<BotFather bergan token>
TELEGRAM_ADMIN_CHAT_ID=
SITE_URL=https://xonsaroy.uz
```

`SITE_URL` ni saytingizning haqiqiy HTTPS manziliga moslang. Botdagi sayt va
profil tugmalari shu manzilga yo'naltiriladi. `TELEGRAM_ADMIN_CHAT_ID` ni botni
ishga tushirgach `/profile` dan oling va shu yerga yozing. Bu ID bot orqali va
saytdan kelgan arizalarni admin'ga yuboradi.

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

## 5. Telegram botni ishga tushirish

Telegram bot bepul PythonAnywhere hisobida ham webhook orqali ishlashi mumkin;
Always-on task kerak emas. Telegram xabarlari Django web ilovasining HTTPS
endpoint'iga yuboriladi.

1. BotFather'da bot yarating yoki mavjud bot tokenini oling. Tokenni
   `~/demo_day/.env` ichidagi `TELEGRAM_BOT_TOKEN` ga yozing. Tokenni buyruq
   satriga yozmang va skrinshotda ko'rsatmang.
2. `SITE_URL` ni PythonAnywhere saytingizning haqiqiy HTTPS manziliga moslang.
   `TELEGRAM_WEBHOOK_SECRET` uchun maxfiy kalit yarating:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

   Chiqqan qiymatni `.env` dagi `TELEGRAM_WEBHOOK_SECRET` ga yozing; uni
   hech kimga yubormang. Secret faqat lotin harflari, raqamlar, `_` va `-`
   belgilaridan iborat bo'lishi kerak.
3. **Consoles → Bash** oynasida migratsiya va sozlamalarni bajaring:

```bash
cd ~/demo_day
python manage.py migrate
python manage.py check
python manage.py runbot --set-webhook
python manage.py runbot --check
```

4. PythonAnywhere **Web** sahifasida **Reload** bosing. Telegram'da botga
   `/start` yuborib, javob kelishini tekshiring. Keyin `/profile` orqali
   Telegram ID ni olib, xabarnoma olish uchun `.env` dagi
   `TELEGRAM_ADMIN_CHAT_ID` ga yozing va web ilovani qayta yuklang.
5. Saytdan test ariza yuborib ko'ring. Xatolar bo'lsa PythonAnywhere'dagi
   **Web → Error log** ni tekshiring. Botni polling rejimida qo'lda ishga
   tushirmang; webhook faol bo'lganda `runbot` alohida ishlatilmaydi.

Kod yangilanganda Bash console'da `git pull`, zarur bo'lsa `python manage.py migrate`
buyruqlarini bajaring, so'ng webhook holatini tekshirib **Web → Reload** qiling.
Webhook manzili o'zgarsa `python manage.py runbot --set-webhook` ni qayta bajaring.
