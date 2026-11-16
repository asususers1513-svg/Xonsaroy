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

Bot saytning WSGI jarayonida ishlamaydi va Web sahifasini reload qilish uni
ishga tushirmaydi. U PythonAnywhere'da alohida **Always-on task** bo'lib
ishlashi kerak. Bu imkoniyat hisob tarifiga bog'liq.

1. BotFather'da bot yarating yoki mavjud bot tokenini oling. Tokenni
   `~/demo_day/.env` ichidagi `TELEGRAM_BOT_TOKEN` ga yozing. Tokenni buyruq
   satriga yozmang va skrinshotda ko'rsatmang.
2. `SITE_URL` ni saytingizning haqiqiy HTTPS manziliga moslang. Hozircha
   `TELEGRAM_ADMIN_CHAT_ID` ni bo'sh qoldiring; admin ID ni bot ishlagach olasiz.
3. **Consoles → Bash** ochib, sozlamalarni tekshiring. Username va virtual muhit
   nomini o'zingiznikiga moslang:

```bash
/home/yourusername/.virtualenvs/xonsaroy-venv/bin/python /home/yourusername/demo_day/manage.py check
/home/yourusername/.virtualenvs/xonsaroy-venv/bin/python /home/yourusername/demo_day/manage.py runbot --check
```

4. `runbot --check` bot username'ini ko'rsatib, token va webhook holatini
   tekshiradi; u botni doimiy ishga tushirmaydi. Token noto'g'ri bo'lsa yoki
   webhook sozlangan bo'lsa, terminaldagi xabarni tuzating. Ushbu loyiha polling
   ishlatgani uchun webhook o'chirilgan bo'lishi kerak.
5. PythonAnywhere **Tasks → Always-on tasks** ro'yxatida **Add a new task**
   tugmasini bosib, ushbu buyruqni kiriting (username va yo'llarni moslang):

```bash
/home/yourusername/.virtualenvs/xonsaroy-venv/bin/python /home/yourusername/demo_day/manage.py runbot
```

   Faqat bitta Always-on task yarating: bir bot tokeni bilan parallel polling
   qiladigan ikki jarayon Telegram'da to'qnashuv keltirib chiqaradi.
6. Task holati **Running** bo'lgach, Telegram'da botga `/start`, keyin
   `/profile` yuboring. Bot ko'rsatgan **Telegram ID** ni nusxalab,
   `~/demo_day/.env` dagi `TELEGRAM_ADMIN_CHAT_ID` ga yozing, so'ng Always-on
   task'ni **Restart** qiling. Admin bildirishnomalari kelishi uchun admin
   avval botga `/start` yuborgan bo'lishi shart.
7. Botga `/projects` va `/profile` yuborib, saytdan test arizasi jo'nating.
   Ariza admin akkauntiga Telegram xabari bo'lib kelishi kerak. Muammo bo'lsa
   PythonAnywhere'dagi task logini va **Web → Error log** ni ko'ring.

Kod yangilanganda Bash console'da `git pull` qiling, yuqoridagi `runbot --check`
tekshiruvini takrorlang va Always-on task'ni **Restart** qiling. Web sahifasini
alohida **Web → Reload** tugmasi bilan qayta yuklash kerak.
