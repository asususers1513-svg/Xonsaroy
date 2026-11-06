import os
import sys
import time
import json
import logging
import requests
import html
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from app.models import Home, Apartment, SalesOffice, Material, Client, User, BotUser, Lead

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# I18N / TRANSLATIONS
# ---------------------------------------------------------------------------
TEXTS = {
    'uz': {
        'welcome': (
            "Assalomu alaykum, <b>{name}</b>! 🌟\n\n"
            "<b>Xon Saroy</b> kompaniyasining rasmiy axborot va konsultatsiya botiga xush kelibsiz!\n\n"
            "Bu yerda siz:\n"
            "• 🏢 <b>Xon Saroy</b> va uning afzalliklari haqida bilib olasiz\n"
            "• 🏗 Zamonaviy <b>turar-joy majmualarimizni</b> ko‘rishingiz mumkin\n"
            "• 🔑 Bo‘sh <b>xonadonlar, rejalari va narxlarini</b> ko‘rishingiz mumkin\n"
            "• 🧮 0% <b>muddatli to‘lov va oylik to‘lovni</b> bir zumda hisoblashingiz mumkin\n"
            "• 📍 Eng yaqin <b>sotuv ofislarimiz</b> manzillari va lokatsiyasini olasiz\n"
            "• 📞 1 daqiqada <b>bepul konsultatsiya</b> uchun ariza qoldirishingiz mumkin\n\n"
            "Kerakli bo‘limni tanlang 👇"
        ),
        'menu_about': '🏢 Xon Saroy nima?',
        'menu_projects': '🏗 Loyihalarimiz',
        'menu_apartments': '🔑 Xonadonlar va Narxlar',
        'menu_calc': '🧮 To‘lov kalkulyatori',
        'menu_offices': '📍 Sotuv ofislari',
        'menu_materials': '🧱 Sifat va Materiallar',
        'menu_reviews': '⭐ Mamnun mijozlar',
        'menu_consult': '📞 Konsultatsiya olish',
        'menu_profile': '👤 Mening profilim',
        'menu_website': '🌐 Veb-saytga o‘tish',
        'menu_lang': '🌐 Tilni o‘zgartirish',
        'menu_admin': '📊 Admin panel',
        'btn_back': '⬅️ Asosiy menyu',
        'btn_share_contact': '📱 Telefon raqamimni yuborish',
        'about_text': (
            "🏢 <b>XON SAROY NIMA?</b>\n\n"
            "<b>Xon Saroy</b> — O‘zbekiston ko‘chmas mulk bozorida mustahkam o‘ringa ega bo‘lgan, "
            "zamonaviy va nufuzli developerlik kompaniyasidir.\n\n"
            "Biz shunchaki ko‘p qavatli binolar qurmaymiz, balki insonlar xavfsiz, xotirjam va "
            "farovon yashaydigan <b>yangi hayot tarzini</b> yaratamiz.\n\n"
            "💎 <b>BIZNING USTUNLIKLARIMIZ:</b>\n\n"
            "🔹 <b>9 ballik seysmik chidamlilik:</b> Barcha majmualar eng yuqori mustahkamlik talablariga javob beruvchi monolit-karkas texnologiyasi asosida qad rostlaydi.\n\n"
            "🔹 <b>Mukammal infratuzilma:</b> Yerosti avtoturargohlari, 24/7 qo‘riqlash va videokuzatuv xizmati, ekologik toza yashil hovlilar, bolalar va sport maydonchalari.\n\n"
            "🔹 <b>Sifatli va ekologik materiallar:</b> Issiqlik va shovqin izolyatsiyasi yuqori pishiq g‘ishtlar, tejamkor panoramik oynalar va ovozsiz tezyurar liftlar.\n\n"
            "🔹 <b>0% foizsiz muddatli to‘lov:</b> Boshlang‘ich to‘lov 15-20% dan boshlab, 36 oygacha qulay to‘lov jadvallari.\n\n"
            "🔹 <b>Qonuniy kafolat:</b> Har bir xonadon to‘liq qonuniy kadastr hujjatlari bilan o‘z vaqtida topshiriladi."
        ),
        'consult_prompt': (
            "📞 <b>BEPUL KONSULTATSIYA OLISH</b>\n\n"
            "Iltimos, telefon raqamingizni qoldiring. <b>Xon Saroy</b> mutaxassisi tez orada siz bilan bog‘lanib, "
            "barcha savollaringizga batafsil javob beradi va eng yaxshi takliflarni taqdim etadi.\n\n"
            "Quyidagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing yoki raqamingizni yozib yuboring (masalan: +998901234567):"
        ),
        'lead_success': (
            "✅ <b>Rahmat, {name}!</b>\n\n"
            "Arizangiz muvaffaqiyatli qabul qilindi. Tez orada <b>Xon Saroy</b> sotuv bo‘limi mutaxassisi "
            "<b>{phone}</b> raqamingizga qo‘ng‘iroq qiladi."
        ),
        'profile_text': (
            "👤 <b>SIZNING PROFILINGIZ:</b>\n\n"
            "🆔 <b>Telegram ID:</b> <code>{tg_id}</code>\n"
            "👤 <b>Ism:</b> {name}\n"
            "💬 <b>Username:</b> {username}\n"
            "🌐 <b>Tanlangan til:</b> {lang_name}\n\n"
            "{site_status}\n\n"
            "💡 <i>Eslatma: Telegram ID raqamingizni veb-saytdagi shaxsiy profilingizda kiritib, "
            "hisoblaringizni o‘zaro bog‘lashingiz mumkin.</i>"
        ),
        'calc_intro': (
            "🧮 <b>MUDDATLI TO‘LOV KALKULYATORI</b>\n\n"
            "Xon Saroy majmualarida 0% foizsiz muddatli to‘lov asosida xonadon xarid qilishingiz mumkin!\n\n"
            "Kerakli narx toifasini tanlang yoki o‘z summasini yozib yuboring 👇"
        ),
        'calc_down_prompt': (
            "💰 <b>Xonadon qiymati:</b> {price} so‘m\n\n"
            "Endi <b>boshlang‘ich to‘lov</b> foizini tanlang 👇"
        ),
        'calc_period_prompt': (
            "💰 <b>Xonadon qiymati:</b> {price} so‘m\n"
            "💳 <b>Boshlang‘ich to‘lov ({pct}%):</b> {down_sum} so‘m\n\n"
            "Endi <b>to‘lov muddatini</b> tanlang 👇"
        ),
        'calc_result': (
            "🧮 <b>MUDDATLI TO‘LOV HISOB-KITOBI:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Xonadon qiymati:</b> {price} so‘m\n"
            "💳 <b>Boshlang‘ich to‘lov ({pct}%):</b> {down_sum} so‘m\n"
            "📉 <b>Qolgan summa:</b> {rem_sum} so‘m\n"
            "📅 <b>To‘lov muddati:</b> {period} oy\n"
            "💵 <b>Oylik to‘lov:</b> <b>{monthly} so‘m/oy</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>* 0% foizsiz qulay muddatli to‘lov shartlari asosida hisoblandi.</i>\n\n"
            "Ushbu shartlar bo‘yicha mutaxassis bilan bog‘lanmoqchimisiz?"
        )
    },
    'ru': {
        'welcome': (
            "Здравствуйте, <b>{name}</b>! 🌟\n\n"
            "Добро пожаловать в официальный бот девелоперской компании <b>Xon Saroy</b>!\n\n"
            "Здесь вы можете:\n"
            "• 🏢 Узнать больше о компании <b>Xon Saroy</b> и наших преимуществах\n"
            "• 🏗 Ознакомиться с нашими современными <b>жилыми комплексами</b>\n"
            "• 🔑 Посмотреть свободные <b>квартиры, планировки и актуальные цены</b>\n"
            "• 🧮 Рассчитать <b>рассрочку 0% и ежемесячный платеж</b> за пару кликов\n"
            "• 📍 Найти ближайшие <b>офисы продаж</b> и получить геолокацию\n"
            "• 📞 Оставить заявку на <b>бесплатную консультацию</b> за 1 минуту\n\n"
            "Выберите интересующий раздел 👇"
        ),
        'menu_about': '🏢 О компании Xon Saroy',
        'menu_projects': '🏗 Наши проекты',
        'menu_apartments': '🔑 Квартиры и цены',
        'menu_calc': '🧮 Калькулятор рассрочки',
        'menu_offices': '📍 Офисы продаж',
        'menu_materials': '🧱 Качество и материалы',
        'menu_reviews': '⭐ Отзывы клиентов',
        'menu_consult': '📞 Получить консультацию',
        'menu_profile': '👤 Мой профиль',
        'menu_website': '🌐 Перейти на сайт',
        'menu_lang': '🌐 Сменить язык',
        'menu_admin': '📊 Админ панель',
        'btn_back': '⬅️ Главное меню',
        'btn_share_contact': '📱 Отправить номер телефона',
        'about_text': (
            "🏢 <b>О КОМПАНИИ XON SAROY</b>\n\n"
            "<b>Xon Saroy</b> — один из ведущих и надежных девелоперов на рынке недвижимости Узбекистана.\n\n"
            "Мы не просто строим дома — мы создаем <b>новое качество жизни</b>, где каждая семья чувствует комфорт, уют и безопасность.\n\n"
            "💎 <b>НАШИ ПРЕИМУЩЕСТВА:</b>\n\n"
            "🔹 <b>Сейсмостойкость до 9 баллов:</b> Все комплексы строятся на основе монолитно-каркасной технологии наивысшей прочности.\n\n"
            "🔹 <b>Современная инфраструктура:</b> Подземные паркинги, круглосуточная охрана 24/7, зеленые эко-дворы, детские и спортивные площадки.\n\n"
            "🔹 <b>Премиальные материалы:</b> Жженый кирпич с высокой тепло- и шумоизоляцией, панорамные окна и бесшумные скоростные лифты.\n\n"
            "🔹 <b>Выгодная рассрочка 0%:</b> Первоначальный взнос от 15-20%, срок до 36 месяцев без переплат.\n\n"
            "🔹 <b>Юридическая чистота:</b> Все объекты сдаются с полным пакетом кадастровых документов точно в срок."
        ),
        'consult_prompt': (
            "📞 <b>БЕСПЛАТНАЯ КОНСУЛЬТАЦИЯ</b>\n\n"
            "Пожалуйста, оставьте ваш номер телефона. Специалист <b>Xon Saroy</b> свяжется с вами в течение 10 минут, "
            "ответит на все вопросы и подберет лучший вариант по специальной цене.\n\n"
            "Нажмите кнопку <b>«📱 Отправить номер телефона»</b> ниже или введите номер вручную (+998901234567):"
        ),
        'lead_success': (
            "✅ <b>Спасибо, {name}!</b>\n\n"
            "Ваша заявка успешно принята. В ближайшее время менеджер отдела продаж <b>Xon Saroy</b> "
            "свяжется с вами по номеру <b>{phone}</b>."
        ),
        'profile_text': (
            "👤 <b>ВАШ ПРОФИЛЬ:</b>\n\n"
            "🆔 <b>Telegram ID:</b> <code>{tg_id}</code>\n"
            "👤 <b>Имя:</b> {name}\n"
            "💬 <b>Username:</b> {username}\n"
            "🌐 <b>Выбранный язык:</b> {lang_name}\n\n"
            "{site_status}\n\n"
            "💡 <i>Вы можете указать этот Telegram ID в профиле на сайте для привязки аккаунта.</i>"
        ),
        'calc_intro': (
            "🧮 <b>КАЛЬКУЛЯТОР БЕСПРОЦЕНТНОЙ РАССРОЧКИ</b>\n\n"
            "В жилых комплексах Xon Saroy доступна беспроцентная рассрочка 0%!\n\n"
            "Выберите бюджет квартиры или введите сумму вручную 👇"
        ),
        'calc_down_prompt': (
            "💰 <b>Стоимость квартиры:</b> {price} сум\n\n"
            "Выберите размер <b>первоначального взноса</b> 👇"
        ),
        'calc_period_prompt': (
            "💰 <b>Стоимость квартиры:</b> {price} сум\n"
            "💳 <b>Первоначальный взнос ({pct}%):</b> {down_sum} сум\n\n"
            "Выберите <b>срок рассрочки</b> 👇"
        ),
        'calc_result': (
            "🧮 <b>РАСЧЕТ РАССРОЧКИ:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Стоимость квартиры:</b> {price} сум\n"
            "💳 <b>Первоначальный взнос ({pct}%):</b> {down_sum} сум\n"
            "📉 <b>Остаток к выплате:</b> {rem_sum} сум\n"
            "📅 <b>Срок рассрочки:</b> {period} мес.\n"
            "💵 <b>Ежемесячный платеж:</b> <b>{monthly} сум/мес.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>* Рассчитано по условиям беспроцентной рассрочки 0%.</i>\n\n"
            "Хотите забронировать эти условия у специалиста?"
        )
    },
    'en': {
        'welcome': (
            "Hello, <b>{name}</b>! 🌟\n\n"
            "Welcome to the official bot of <b>Xon Saroy</b> development company!\n\n"
            "Here you can:\n"
            "• 🏢 Learn about <b>Xon Saroy</b> and our key advantages\n"
            "• 🏗 Explore our modern <b>residential complexes</b>\n"
            "• 🔑 View available <b>apartments, floor plans, and prices</b>\n"
            "• 🧮 Calculate <b>0% installment payments</b> in seconds\n"
            "• 📍 Find the nearest <b>sales offices</b> with GPS coordinates\n"
            "• 📞 Request a <b>free consultation</b> in 1 minute\n\n"
            "Choose a section below 👇"
        ),
        'menu_about': '🏢 About Xon Saroy',
        'menu_projects': '🏗 Our Projects',
        'menu_apartments': '🔑 Apartments & Prices',
        'menu_calc': '🧮 Payment Calculator',
        'menu_offices': '📍 Sales Offices',
        'menu_materials': '🧱 Quality & Materials',
        'menu_reviews': '⭐ Customer Reviews',
        'menu_consult': '📞 Get Consultation',
        'menu_profile': '👤 My Profile',
        'menu_website': '🌐 Visit Website',
        'menu_lang': '🌐 Change Language',
        'menu_admin': '📊 Admin Panel',
        'btn_back': '⬅️ Main Menu',
        'btn_share_contact': '📱 Share Phone Number',
        'about_text': (
            "🏢 <b>ABOUT XON SAROY</b>\n\n"
            "<b>Xon Saroy</b> is a premier real estate development company in Uzbekistan.\n\n"
            "We build more than just buildings — we create a <b>modern living environment</b> "
            "where families enjoy security, comfort, and happiness.\n\n"
            "💎 <b>OUR ADVANTAGES:</b>\n\n"
            "🔹 <b>9-Magnitude Seismic Safety:</b> All complexes are built using high-strength monolithic-frame technology.\n\n"
            "🔹 <b>Complete Infrastructure:</b> Underground parking, 24/7 security, green eco-courtyards, children playgrounds, and sports areas.\n\n"
            "🔹 <b>High-Grade Materials:</b> Thermal & acoustic insulated brickwork, panoramic energy-efficient windows, and high-speed silent elevators.\n\n"
            "🔹 <b>0% Interest-Free Installments:</b> Starting from 15-20% down payment, up to 36 months payment plans.\n\n"
            "🔹 <b>Legal Transparency:</b> All homes come with complete cadastral documents delivered on time."
        ),
        'consult_prompt': (
            "📞 <b>FREE CONSULTATION</b>\n\n"
            "Please provide your contact phone number. A <b>Xon Saroy</b> specialist will contact you shortly "
            "to answer all your questions and provide the best available offers.\n\n"
            "Tap <b>«📱 Share Phone Number»</b> below or type your phone (+998901234567):"
        ),
        'lead_success': (
            "✅ <b>Thank you, {name}!</b>\n\n"
            "Your request has been successfully received. A <b>Xon Saroy</b> sales specialist will call you at "
            "<b>{phone}</b> very soon."
        ),
        'profile_text': (
            "👤 <b>YOUR PROFILE:</b>\n\n"
            "🆔 <b>Telegram ID:</b> <code>{tg_id}</code>\n"
            "👤 <b>Name:</b> {name}\n"
            "💬 <b>Username:</b> {username}\n"
            "🌐 <b>Language:</b> {lang_name}\n\n"
            "{site_status}\n\n"
            "💡 <i>Tip: You can paste your Telegram ID into your website profile settings to sync your accounts.</i>"
        ),
        'calc_intro': (
            "🧮 <b>0% INSTALLMENT CALCULATOR</b>\n\n"
            "Get an apartment in Xon Saroy with 0% interest-free installments!\n\n"
            "Select an apartment price range or type a custom amount 👇"
        ),
        'calc_down_prompt': (
            "💰 <b>Apartment Price:</b> {price} UZS\n\n"
            "Select <b>down payment percentage</b> 👇"
        ),
        'calc_period_prompt': (
            "💰 <b>Apartment Price:</b> {price} UZS\n"
            "💳 <b>Down Payment ({pct}%):</b> {down_sum} UZS\n\n"
            "Select <b>installment duration</b> 👇"
        ),
        'calc_result': (
            "🧮 <b>INSTALLMENT BREAKDOWN:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Apartment Price:</b> {price} UZS\n"
            "💳 <b>Down Payment ({pct}%):</b> {down_sum} UZS\n"
            "📉 <b>Remaining Amount:</b> {rem_sum} UZS\n"
            "📅 <b>Duration:</b> {period} months\n"
            "💵 <b>Monthly Payment:</b> <b>{monthly} UZS/mo</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>* Calculated under 0% interest-free terms.</i>\n\n"
            "Would you like to book this plan with a specialist?"
        )
    }
}


def fmt_sum(val):
    try:
        return f"{int(round(float(val))):,}".replace(',', ' ')
    except Exception:
        return str(val)


# ---------------------------------------------------------------------------
# TELEGRAM BOT CLASS
# ---------------------------------------------------------------------------
class TelegramBot:
    def __init__(self, token, admin_chat_id=None):
        self.token = token.strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.admin_chat_id = str(admin_chat_id or '').strip()
        self.user_states = {}  # {chat_id: {'state': ..., 'data': ...}}

    def call_api(self, method, data=None, files=None):
        try:
            url = f"{self.api_url}/{method}"
            resp = requests.post(url, data=data, files=files, timeout=35)
            return resp.json()
        except Exception:
            logger.error("Telegram API so‘rovi bajarilmadi (%s).", method)
            return {'ok': False, 'description': 'Telegram API request failed.'}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode='HTML'):
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        return self.call_api('sendMessage', data)

    def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode='HTML'):
        data = {
            'chat_id': chat_id,
            'caption': caption or '',
            'parse_mode': parse_mode
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)

        if isinstance(photo, str) and (photo.startswith('http://') or photo.startswith('https://')):
            data['photo'] = photo
            resp = self.call_api('sendPhoto', data)
            if resp.get('ok'):
                return resp
            # If photo failed, fallback to send_message
            return self.send_message(chat_id, caption or '', reply_markup=reply_markup)

        elif isinstance(photo, str) and os.path.exists(photo):
            try:
                with open(photo, 'rb') as f:
                    resp = self.call_api('sendPhoto', data, files={'photo': f})
                    if resp.get('ok'):
                        return resp
            except Exception as e:
                logger.error(f"Error reading photo {photo}: {e}")
            return self.send_message(chat_id, caption or '', reply_markup=reply_markup)

        else:
            return self.send_message(chat_id, caption or '', reply_markup=reply_markup)

    def send_location(self, chat_id, latitude, longitude, reply_markup=None):
        data = {
            'chat_id': chat_id,
            'latitude': float(latitude),
            'longitude': float(longitude)
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        return self.call_api('sendLocation', data)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        data = {'callback_query_id': callback_query_id}
        if text:
            data['text'] = text
        if show_alert:
            data['show_alert'] = True
        return self.call_api('answerCallbackQuery', data)

    # -----------------------------------------------------------------------
    # USER & LANGUAGE HELPERS
    # -----------------------------------------------------------------------
    def get_or_create_user(self, from_user):
        tg_id = str(from_user.get('id', ''))
        first_name = from_user.get('first_name', '') or ''
        last_name = from_user.get('last_name', '') or ''
        username = from_user.get('username', None)

        bot_user, created = BotUser.objects.get_or_create(
            telegram_id=tg_id,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'language': 'uz'
            }
        )
        # Update details if changed
        updated = False
        if bot_user.first_name != first_name:
            bot_user.first_name = first_name
            updated = True
        if bot_user.last_name != last_name:
            bot_user.last_name = last_name
            updated = True
        if bot_user.username != username:
            bot_user.username = username
            updated = True
        if updated:
            bot_user.save()

        return bot_user

    def get_lang(self, chat_id):
        try:
            bu = BotUser.objects.filter(telegram_id=str(chat_id)).first()
            if bu and bu.language in TEXTS:
                return bu.language
        except Exception:
            pass
        return 'uz'

    def set_lang(self, chat_id, lang):
        if lang in TEXTS:
            BotUser.objects.filter(telegram_id=str(chat_id)).update(language=lang)

    def t(self, chat_id, key, **kwargs):
        lang = self.get_lang(chat_id)
        tmpl = TEXTS.get(lang, TEXTS['uz']).get(key, TEXTS['uz'].get(key, ''))
        return tmpl.format(**kwargs) if kwargs else tmpl

    # -----------------------------------------------------------------------
    # KEYBOARDS
    # -----------------------------------------------------------------------
    def get_main_keyboard(self, chat_id):
        t = lambda k: self.t(chat_id, k)
        kb = [
            [{'text': t('menu_about')}, {'text': t('menu_projects')}],
            [{'text': t('menu_apartments')}, {'text': t('menu_calc')}],
            [{'text': t('menu_offices')}, {'text': t('menu_materials')}],
            [{'text': t('menu_reviews')}, {'text': t('menu_consult')}],
            [{'text': t('menu_profile')}, {'text': t('menu_website')}],
            [{'text': t('menu_lang')}]
        ]
        if str(chat_id) == self.admin_chat_id:
            kb.append([{'text': t('menu_admin')}])

        return {'keyboard': kb, 'resize_keyboard': True, 'persistent': True}

    def get_contact_keyboard(self, chat_id):
        t = lambda k: self.t(chat_id, k)
        return {
            'keyboard': [
                [{'text': t('btn_share_contact'), 'request_contact': True}],
                [{'text': t('btn_back')}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }

    # -----------------------------------------------------------------------
    # HANDLERS: START & LANGUAGE
    # -----------------------------------------------------------------------
    def handle_start(self, chat_id, from_user):
        bu = self.get_or_create_user(from_user)
        name = html.escape(from_user.get('first_name', 'Mijoz'))
        text = self.t(chat_id, 'welcome', name=name)
        self.send_message(chat_id, text, reply_markup=self.get_main_keyboard(chat_id))

    def handle_lang_prompt(self, chat_id):
        text = (
            "🌐 <b>Tilni tanlang / Выберите язык / Select language:</b>\n\n"
            "🇺🇿 <b>O‘zbekcha</b> — O‘zbek tili\n"
            "🇷🇺 <b>Русский</b> — Русский язык\n"
            "🇬🇧 <b>English</b> — English language"
        )
        kb = {
            'inline_keyboard': [
                [{'text': '🇺🇿 O‘zbekcha', 'callback_data': 'set_lang_uz'}],
                [{'text': '🇷🇺 Русский', 'callback_data': 'set_lang_ru'}],
                [{'text': '🇬🇧 English', 'callback_data': 'set_lang_en'}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=kb)

    # -----------------------------------------------------------------------
    # HANDLERS: ABOUT
    # -----------------------------------------------------------------------
    def handle_about(self, chat_id):
        text = self.t(chat_id, 'about_text')
        lang = self.get_lang(chat_id)
        btn_projects = '🏗 Loyihalarni ko‘rish' if lang == 'uz' else ('🏗 Смотреть проекты' if lang == 'ru' else '🏗 View Projects')
        btn_calc = '🧮 Kalkulyator' if lang == 'uz' else ('🧮 Калькулятор' if lang == 'ru' else '🧮 Calculator')
        btn_consult = '📞 Konsultatsiya olish' if lang == 'uz' else ('📞 Консультация' if lang == 'ru' else '📞 Consultation')

        inline_kb = {
            'inline_keyboard': [
                [{'text': btn_projects, 'callback_data': 'filter_proj_all'},
                 {'text': btn_calc, 'callback_data': 'calc_start'}],
                [{'text': btn_consult, 'callback_data': 'req_consult'}]
            ]
        }
        banner_url = "https://xonsaroy.uz/assets/96551977e212f9efb81e221cd96e26f43153c263-B76rgFTQ.png"
        self.send_photo(chat_id, banner_url, caption=text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: PROJECTS
    # -----------------------------------------------------------------------
    def handle_projects(self, chat_id, status_filter=None):
        homes = Home.objects.select_related('category').order_by('id')
        if status_filter:
            homes = homes.filter(status=status_filter)

        lang = self.get_lang(chat_id)
        titles = {
            'uz': {
                'in_progress': '🟡 Qurilayotgan loyihalar',
                'completed': '🟢 Yakunlangan loyihalar',
                'soon': '🟣 Tez kunda kutilayotgan loyihalar',
                None: '🏗 Barcha loyihalarimiz'
            },
            'ru': {
                'in_progress': '🟡 Строящиеся комплексы',
                'completed': '🟢 Завершенные комплексы',
                'soon': '🟣 Скоро в продаже',
                None: '🏗 Все наши проекты'
            },
            'en': {
                'in_progress': '🟡 Projects in Progress',
                'completed': '🟢 Completed Projects',
                'soon': '🟣 Coming Soon',
                None: '🏗 All Projects'
            }
        }
        title = titles.get(lang, titles['uz']).get(status_filter, '🏗 Loyihalarimiz')
        count = homes.count()

        if count == 0:
            msg = "Loyihalar topilmadi." if lang == 'uz' else ("Проекты не найдены." if lang == 'ru' else "No projects found.")
            self.send_message(chat_id, f"<b>{title}</b>: {msg}")
            return

        hint = (
            f"<b>{title} ({count} ta):</b>\n\n"
            f"Batafsil ma’lumot va bo‘sh xonadonlarni ko‘rish uchun loyihani tanlang 👇"
            if lang == 'uz' else
            f"<b>{title} ({count}):</b>\n\n"
            f"Выберите проект для подробной информации и просмотра планировок 👇"
            if lang == 'ru' else
            f"<b>{title} ({count}):</b>\n\n"
            f"Select a project to view details and floor plans 👇"
        )

        filter_row = [
            {'text': '🟡 Jarayonda' if lang == 'uz' else ('🟡 В процессе' if lang == 'ru' else '🟡 Active'), 'callback_data': 'filter_proj_in_progress'},
            {'text': '🟢 Tayyor' if lang == 'uz' else ('🟢 Готовые' if lang == 'ru' else '🟢 Ready'), 'callback_data': 'filter_proj_completed'},
            {'text': '🟣 Tez kunda' if lang == 'uz' else ('🟣 Скоро' if lang == 'ru' else '🟣 Soon'), 'callback_data': 'filter_proj_soon'}
        ]
        all_row = [{'text': '📑 Barcha loyihalar' if lang == 'uz' else ('📑 Все проекты' if lang == 'ru' else '📑 All Projects'), 'callback_data': 'filter_proj_all'}]

        project_buttons = []
        for h in homes:
            icon = '🟢' if h.status == 'completed' else ('🟡' if h.status == 'in_progress' else '🟣')
            project_buttons.append([{'text': f"{icon} {h.name}", 'callback_data': f"proj_{h.id}"}])

        inline_kb = {'inline_keyboard': [filter_row, all_row] + project_buttons}
        self.send_message(chat_id, hint, reply_markup=inline_kb)

    def handle_project_detail(self, chat_id, project_id):
        try:
            home = Home.objects.get(id=project_id)
        except Home.DoesNotExist:
            self.send_message(chat_id, "Loyiha topilmadi.")
            return

        lang = self.get_lang(chat_id)
        status_names = {
            'completed': ('🟢 Yakunlangan (Tayyor)', '🟢 Завершен (Сдан)', '🟢 Completed (Ready)'),
            'in_progress': ('🟡 Qurilish jarayonida', '🟡 В процессе строительства', '🟡 Under Construction'),
            'soon': ('🟣 Tez kunda savdoda', '🟣 Скоро в продаже', '🟣 Coming Soon')
        }
        idx = 0 if lang == 'uz' else (1 if lang == 'ru' else 2)
        st_text = status_names.get(home.status, (home.status, home.status, home.status))[idx]

        category_name = home.category.name if home.category else ("Turar-joy majmuasi" if lang == 'uz' else "Жилой комплекс")
        apts = home.apartments.filter(is_active=True)
        apt_count = apts.count()

        text = (
            f"🏢 <b>«{home.name}»</b>\n\n"
            f"📌 <b>Toifasi:</b> {category_name}\n"
            f"📊 <b>Holati:</b> {st_text}\n"
            f"🔑 <b>Mavjud xonadonlar:</b> {apt_count} ta reja\n\n"
            f"{home.description or 'Zamonaviy arxitektura, qulay infratuzilma va yerosti avtoturargoh.'}\n"
        )
        if lang == 'ru':
            text = (
                f"🏢 <b>«{home.name}»</b>\n\n"
                f"📌 <b>Категория:</b> {category_name}\n"
                f"📊 <b>Статус:</b> {st_text}\n"
                f"🔑 <b>Доступно планировок:</b> {apt_count}\n\n"
                f"{home.description or 'Современная архитектура, развитая инфраструктура и подземный паркинг.'}\n"
            )

        btn_apts = f"🔑 Xonadonlarni ko‘rish ({apt_count} ta)" if lang == 'uz' else (f"🔑 Планировки ({apt_count})" if lang == 'ru' else f"🔑 View Apartments ({apt_count})")
        btn_lead = "📞 Ushbu loyiha uchun maslahat" if lang == 'uz' else ("📞 Консультация по проекту" if lang == 'ru' else "📞 Consult for Project")
        btn_back = "⬅️ Loyihalar ro‘yxati" if lang == 'uz' else ("⬅️ Список проектов" if lang == 'ru' else "⬅️ Projects List")

        inline_buttons = []
        if apt_count > 0:
            inline_buttons.append([{'text': btn_apts, 'callback_data': f"apts_proj_{home.id}"}])
        inline_buttons.append([{'text': btn_lead, 'callback_data': f"lead_proj_{home.id}"}])
        inline_buttons.append([{'text': btn_back, 'callback_data': 'filter_proj_all'}])

        inline_kb = {'inline_keyboard': inline_buttons}

        img = None
        if home.hero_image and os.path.exists(home.hero_image.path):
            img = home.hero_image.path
        elif home.image and os.path.exists(home.image.path):
            img = home.image.path
        elif home.image_url:
            img = home.image_url

        if img:
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: APARTMENTS
    # -----------------------------------------------------------------------
    def handle_apartments(self, chat_id, rooms=None, project_id=None):
        apts = Apartment.objects.filter(is_active=True).select_related('project')
        if rooms:
            apts = apts.filter(rooms=rooms)
        if project_id:
            apts = apts.filter(project_id=project_id)

        count = apts.count()
        lang = self.get_lang(chat_id)

        if count == 0:
            msg = "Ushbu parametrlar bo‘yicha hozircha xonadonlar topilmadi." if lang == 'uz' else ("Квартир по данным параметрам пока не найдено." if lang == 'ru' else "No apartments found for this filter.")
            self.send_message(chat_id, msg)
            return

        header = (
            f"🔑 <b>Orzuyingizdagi xonadonni tanlang ({count} ta):</b>\n\n"
            f"Rejasi va rasmini ko‘rish uchun kerakli xonadonni bosing 👇"
            if lang == 'uz' else
            f"🔑 <b>Квартиры и цены ({count}):</b>\n\n"
            f"Нажмите на квартиру, чтобы посмотреть планировку и расчёт рассрочки 👇"
            if lang == 'ru' else
            f"🔑 <b>Apartments and Prices ({count}):</b>\n\n"
            f"Click an apartment to view floor plan and payment calculation 👇"
        )

        filter_row = [{'text': 'Barchasi', 'callback_data': 'apts_rm_all'}]

        apt_buttons = []
        for a in apts[:10]:
            p_name = a.project.name if a.project else "Xon Saroy"
            price_str = fmt_sum(a.price)
            btn_title = f"{p_name}: {a.rooms}-xona, {a.area} m² — {price_str} so‘m"
            apt_buttons.append([{'text': btn_title, 'callback_data': f"apt_detail_{a.id}"}])

        inline_kb = {'inline_keyboard': [filter_row] + apt_buttons}
        self.send_message(chat_id, header, reply_markup=inline_kb)

    def handle_apartment_detail(self, chat_id, apt_id):
        try:
            apt = Apartment.objects.select_related('project').get(id=apt_id)
        except Apartment.DoesNotExist:
            self.send_message(chat_id, "Xonadon topilmadi.")
            return

        lang = self.get_lang(chat_id)
        proj_name = apt.project.name if apt.project else "Xon Saroy"
        total_price = fmt_sum(apt.price)
        m2_price = fmt_sum(round(float(apt.price) / float(apt.area))) if apt.area else '0'

        text = (
            f"🔑 <b>XONADON PASPORTI:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Majmua:</b> {proj_name}\n"
            f"🚪 <b>Xonalar soni:</b> {apt.rooms} xonali\n"
            f"🏢 <b>Qavat:</b> {apt.floor}-qavat\n"
            f"📐 <b>Umumiy maydon:</b> {apt.area} m²\n"
            f"💰 <b>1 m² narxi:</b> ~{m2_price} so‘m\n"
            f"🏷 <b>Umumiy narx:</b> <b>{total_price} so‘m</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>* 0% foizsiz muddatli to‘lov imkoniyati mavjud.</i>"
        )
        if lang == 'ru':
            text = (
                f"🔑 <b>КАРТОЧКА КВАРТИРЫ:</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🏢 <b>Комплекс:</b> {proj_name}\n"
                f"🚪 <b>Количество комнат:</b> {apt.rooms}-комнатная\n"
                f"🏢 <b>Этаж:</b> {apt.floor}-этаж\n"
                f"📐 <b>Площадь:</b> {apt.area} м²\n"
                f"💰 <b>Цена за 1 м²:</b> ~{m2_price} сум\n"
                f"🏷 <b>Общая стоимость:</b> <b>{total_price} сум</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>* Доступна беспроцентная рассрочка 0%.</i>"
            )

        btn_calc = '🧮 Ushbu xonadon to‘lovini hisoblash' if lang == 'uz' else '🧮 Рассчитать рассрочку для квартиры'
        btn_book = '📞 Ushbu xonadonni band qilish' if lang == 'uz' else '📞 Забронировать эту квартиру'
        btn_back = '⬅️ Xonadonlar ro‘yxati' if lang == 'uz' else '⬅️ Список квартир'

        inline_kb = {
            'inline_keyboard': [
                [{'text': btn_calc, 'callback_data': f"calc_apt_{apt.id}"}],
                [{'text': btn_book, 'callback_data': f"book_apt_{apt.id}"}],
                [{'text': btn_back, 'callback_data': 'apts_rm_all'}]
            ]
        }

        # Check plan image
        img = None
        if apt.image and os.path.exists(apt.image.path):
            img = apt.image.path
        elif apt.image_url:
            img = apt.image_url

        if img:
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: CALCULATOR (MUDDATLI TO'LOV / INSTALLMENTS)
    # -----------------------------------------------------------------------
    def handle_calc_start(self, chat_id, default_price=None):
        text = self.t(chat_id, 'calc_intro')
        inline_kb = {
            'inline_keyboard': [
                [{'text': '350 000 000 so‘m', 'callback_data': 'calc_pr_350000000'},
                 {'text': '500 000 000 so‘m', 'callback_data': 'calc_pr_500000000'}],
                [{'text': '700 000 000 so‘m', 'callback_data': 'calc_pr_700000000'},
                 {'text': '1 000 000 000 so‘m', 'callback_data': 'calc_pr_1000000000'}],
                [{'text': '✏️ O‘z summangizni yozish', 'callback_data': 'calc_pr_custom'}]
            ]
        }
        if default_price:
            self.handle_calc_select_down(chat_id, float(default_price))
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_calc_select_down(self, chat_id, price):
        self.user_states[chat_id] = {'state': 'calc_step_down', 'price': float(price)}
        text = self.t(chat_id, 'calc_down_prompt', price=fmt_sum(price))

        inline_kb = {
            'inline_keyboard': [
                [{'text': '15%', 'callback_data': 'calc_down_15'},
                 {'text': '20%', 'callback_data': 'calc_down_20'}],
                [{'text': '30%', 'callback_data': 'calc_down_30'},
                 {'text': '50%', 'callback_data': 'calc_down_50'}],
                [{'text': '🔄 Boshqa summa tanlash', 'callback_data': 'calc_start'}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_calc_select_period(self, chat_id, pct):
        state = self.user_states.get(chat_id, {})
        price = state.get('price', 500000000.0)
        down_sum = price * (float(pct) / 100.0)
        self.user_states[chat_id] = {'state': 'calc_step_period', 'price': price, 'pct': pct, 'down_sum': down_sum}

        text = self.t(chat_id, 'calc_period_prompt', price=fmt_sum(price), pct=pct, down_sum=fmt_sum(down_sum))
        inline_kb = {
            'inline_keyboard': [
                [{'text': '12 oy (1 yil)', 'callback_data': 'calc_per_12'},
                 {'text': '24 oy (2 yil)', 'callback_data': 'calc_per_24'}],
                [{'text': '36 oy (3 yil)', 'callback_data': 'calc_per_36'},
                 {'text': '48 oy (4 yil)', 'callback_data': 'calc_per_48'}],
                [{'text': '⬅️ Boshlang‘ich to‘lovni o‘zgartirish', 'callback_data': f"calc_pr_{int(price)}"}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_calc_compute(self, chat_id, period):
        state = self.user_states.get(chat_id, {})
        price = state.get('price', 500000000.0)
        pct = state.get('pct', 20)
        down_sum = state.get('down_sum', price * 0.2)
        rem_sum = price - down_sum
        monthly = rem_sum / float(period)

        text = self.t(
            chat_id, 'calc_result',
            price=fmt_sum(price),
            pct=pct,
            down_sum=fmt_sum(down_sum),
            rem_sum=fmt_sum(rem_sum),
            period=period,
            monthly=fmt_sum(monthly)
        )

        note_data = f"Kalkulyator hisobi: Narx={fmt_sum(price)} so'm, Boshlang'ich={pct}% ({fmt_sum(down_sum)} so'm), Muddat={period} oy, Oylik={fmt_sum(monthly)} so'm/oy"
        self.user_states[chat_id] = {'state': 'awaiting_contact', 'note': note_data}

        lang = self.get_lang(chat_id)
        btn_consult = '📞 Ushbu shartlarda ariza qoldirish' if lang == 'uz' else '📞 Оставить заявку на этих условиях'
        btn_restart = '🔄 Qaytadan hisoblash' if lang == 'uz' else '🔄 Рассчитать заново'

        inline_kb = {
            'inline_keyboard': [
                [{'text': btn_consult, 'callback_data': 'req_consult'}],
                [{'text': btn_restart, 'callback_data': 'calc_start'}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: OFFICES & LOCATIONS
    # -----------------------------------------------------------------------
    def handle_offices(self, chat_id):
        offices = SalesOffice.objects.all().order_by('sort_order', 'id')
        lang = self.get_lang(chat_id)

        if not offices.exists():
            msg = "Sotuv ofislari ma’lumotlari tez orada joylashtiriladi." if lang == 'uz' else "Информация об офисах продаж скоро появится."
            self.send_message(chat_id, msg)
            return

        text = (
            "📍 <b>XON SAROY SOTUV OFISLARI:</b>\n\n"
            "Sizni qulay va shinam savdo ofislarimizda kutib qolamiz!\n"
            "🕒 <b>Ish vaqti:</b> Har kuni 09:00 dan 19:00 gacha dam olish kunlarisiz.\n\n"
            if lang == 'uz' else
            "📍 <b>ОФИСЫ ПРОДАЖ XON SAROY:</b>\n\n"
            "Будем рады видеть вас в наших комфортабельных офисах продаж!\n"
            "🕒 <b>График работы:</b> Ежедневно с 09:00 до 19:00 без выходных.\n\n"
        )

        inline_buttons = []
        for idx, o in enumerate(offices, 1):
            text += f"🏢 <b>{idx}. {o.name}</b>\n📍 {o.address}\n\n"
            if o.latitude and o.longitude:
                btn_name = f"📍 {o.name} lokatsiyasi" if lang == 'uz' else f"📍 Локация: {o.name}"
                inline_buttons.append([{'text': btn_name, 'callback_data': f"office_loc_{o.id}"}])

        btn_consult = '📞 Ofisga qo‘ng‘iroq buyurtma qilish' if lang == 'uz' else '📞 Заказать звонок из офиса'
        inline_buttons.append([{'text': btn_consult, 'callback_data': 'req_consult'}])

        inline_kb = {'inline_keyboard': inline_buttons}
        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_office_location(self, chat_id, office_id):
        try:
            o = SalesOffice.objects.get(id=office_id)
            if o.latitude and o.longitude:
                self.send_location(chat_id, o.latitude, o.longitude)
                lat, lng = float(o.latitude), float(o.longitude)
                gmaps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
                yandex_url = f"https://yandex.com/maps/?pt={lng},{lat}&z=16"
                kb = {
                    'inline_keyboard': [
                        [{'text': '🗺 Google Maps', 'url': gmaps_url},
                         {'text': '🚕 Yandex Maps / Go', 'url': yandex_url}]
                    ]
                }
                self.send_message(chat_id, f"📍 <b>{o.name}</b>\nManzil: {o.address}", reply_markup=kb)
            else:
                self.send_message(chat_id, f"📍 <b>{o.name}</b>\nManzil: {o.address}\n\n(Lokatsiya koordinatalari mavjud emas)")
        except SalesOffice.DoesNotExist:
            self.send_message(chat_id, "Sotuv ofisi topilmadi.")

    # -----------------------------------------------------------------------
    # HANDLERS: MATERIALS & QUALITY
    # -----------------------------------------------------------------------
    def handle_materials(self, chat_id):
        materials = Material.objects.all().order_by('sort_order', 'id')
        lang = self.get_lang(chat_id)

        text = (
            "🧱 <b>XON SAROY SIFAT STANDARTLARI VA MATERIALLAR:</b>\n\n"
            "Kompaniyamiz qurilishda jahon standartlariga mos, sertifikatlangan va laboratoriya nazoratidan o‘tgan xomashyolardan foydalanadi:\n\n"
            "🏗 <b>Monolit karkas:</b> 9 ballik zilzilaga bardoshli poydevor va ustunlar.\n"
            "🧱 <b>Pishiq g‘isht va gazoblok:</b> Ekologik toza, qishda issiq, yozda salqin saqlovchi energiya tejamkor devorlar.\n"
            "🪟 <b>Panoramik romlar:</b> Shovqin va changdan ishonchli himoyalovchi sifatli oynalar.\n"
            "🛗 <b>Tezyurar liftlar:</b> Shovqinsiz, xavfsiz va yuqori yuk ko‘tarish quvvatiga ega liftlar.\n\n"
            if lang == 'uz' else
            "🧱 <b>СТАНДАРТЫ КАЧЕСТВА И МАТЕРИАЛЫ XON SAROY:</b>\n\n"
            "Все наши объекты строятся исключительно из сертифицированных и проверенных материалов:\n\n"
            "🏗 <b>Монолитный каркас:</b> Сейсмостойкость до 9 баллов.\n"
            "🧱 <b>Жженый кирпич и газоблок:</b> Энергоэффективные стены — тепло зимой и прохладно летом.\n"
            "🪟 <b>Панорамные окна:</b> Высокая шумо- и теплоизоляция.\n"
            "🛗 <b>Бесшумные скоростные лифты:</b> Максимальная безопасность и надежность.\n\n"
        )

        for idx, m in enumerate(materials, 1):
            text += f"• <b>{m.title}</b>\n"

        btn_consult = '📞 Sifat bo‘yicha maslahat olish' if lang == 'uz' else '📞 Консультация по качеству'
        inline_kb = {'inline_keyboard': [[{'text': btn_consult, 'callback_data': 'req_consult'}]]}

        first_mat = materials.first()
        if first_mat and first_mat.image_url:
            self.send_photo(chat_id, first_mat.image_url, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: REVIEWS
    # -----------------------------------------------------------------------
    def handle_reviews(self, chat_id):
        clients = Client.objects.all().order_by('sort_order', 'id')
        lang = self.get_lang(chat_id)

        text = (
            "⭐ <b>BIZGA ISHONCH BILDIRGAN MIJOZLARIMIZ:</b>\n\n"
            "Minglab oilalar Xon Saroy majmualarida o‘z orzularidagi xonadonlarga ega bo‘lishdi. "
            "Biz har bir mijozning ishonchini yuksak qadrlaymiz!\n\n"
            if lang == 'uz' else
            "⭐ <b>ОТЗЫВЫ НАШИХ ДОВОЛЬНЫХ КЛИЕНТОВ:</b>\n\n"
            "Тысячи семей уже выбрали жилые комплексы Xon Saroy и счастливо живут в своих квартирах!\n\n"
        )

        for c in clients:
            text += f"✨ <b>{c.name}</b> — Xon Saroy rezidenti\n"

        btn_consult = '📞 Xonadon xarid qilish' if lang == 'uz' else '📞 Подобрать квартиру'
        inline_kb = {'inline_keyboard': [[{'text': btn_consult, 'callback_data': 'req_consult'}]]}

        first_c = clients.first()
        if first_c and first_c.image_url:
            self.send_photo(chat_id, first_c.image_url, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: USER PROFILE
    # -----------------------------------------------------------------------
    def handle_profile(self, chat_id, from_user):
        bu = self.get_or_create_user(from_user)
        lang = self.get_lang(chat_id)
        name = html.escape(from_user.get('first_name', 'Foydalanuvchi'))
        username = f"@{from_user.get('username')}" if from_user.get('username') else ("Mavjud emas" if lang == 'uz' else "Не указан")

        lang_names = {'uz': 'O‘zbekcha', 'ru': 'Русский', 'en': 'English'}
        lang_name = lang_names.get(lang, 'O‘zbekcha')

        # Check if matched with website user
        web_user = User.objects.filter(telegram_id=str(chat_id)).first()
        if web_user:
            site_status = (
                f"🔗 <b>Veb-sayt hisobi:</b> Bog‘langan ✅\n"
                f"👤 <b>Foydalanuvchi nomi:</b> <code>{web_user.username}</code>\n"
                f"📧 <b>Pochta:</b> {web_user.email or 'Kiritilmagan'}"
            )
        else:
            site_status = (
                "🔗 <b>Veb-sayt hisobi:</b> Hali bog‘lanmagan ⚠️\n"
                "<i>Saytimiz profil sozlamalarida Telegram ID'ingizni kiritib, hisobingizni bog‘lashingiz mumkin.</i>"
                if lang == 'uz' else
                "🔗 <b>Аккаунт на сайте:</b> Еще не привязан ⚠️\n"
                "<i>Укажите ваш Telegram ID в профиле на сайте для привязки.</i>"
            )

        text = self.t(
            chat_id, 'profile_text',
            tg_id=chat_id,
            name=name,
            username=username,
            lang_name=lang_name,
            site_status=site_status
        )

        site_url = f"{settings.SITE_URL}/profile/"
        kb = {
            'inline_keyboard': [
                [{'text': '🌐 Saytdagi profilni ochish' if lang == 'uz' else '🌐 Профиль на сайте', 'url': site_url}],
                [{'text': '🌐 Tilni o‘zgartirish' if lang == 'uz' else '🌐 Сменить язык', 'callback_data': 'show_lang_modal'}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=kb)

    # -----------------------------------------------------------------------
    # HANDLERS: CONSULTATION & LEADS
    # -----------------------------------------------------------------------
    def request_consultation_prompt(self, chat_id, note=""):
        prev = self.user_states.get(chat_id, {})
        existing_note = prev.get('note', '') or note
        self.user_states[chat_id] = {'state': 'awaiting_contact', 'note': existing_note}
        text = self.t(chat_id, 'consult_prompt')
        self.send_message(chat_id, text, reply_markup=self.get_contact_keyboard(chat_id))

    def process_lead(self, chat_id, from_user, phone, custom_note=""):
        name = from_user.get('first_name', '') + (' ' + from_user.get('last_name', '') if from_user.get('last_name') else '')
        name = name.strip() or 'Mijoz'
        username = from_user.get('username')
        username_str = f"@{username}" if username else "Mavjud emas"

        # Update BotUser phone
        BotUser.objects.filter(telegram_id=str(chat_id)).update(phone=phone)

        # Retrieve any pending note or project from state
        state = self.user_states.get(chat_id, {})
        full_note = custom_note or state.get('note', '')

        # Save to database
        lead = Lead.objects.create(
            name=name,
            phone=phone,
            telegram_id=str(chat_id),
            telegram_username=username,
            source=Lead.Source.TELEGRAM,
            note=full_note
        )

        # Notify Admin on Telegram
        if self.admin_chat_id:
            admin_msg = (
                "🚨 <b>YANGI ARIZA (Telegram Bot)!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Mijoz:</b> {html.escape(name)}\n"
                f"📞 <b>Telefon:</b> <code>{html.escape(phone)}</code>\n"
                f"💬 <b>Telegram:</b> {username_str} (ID: <code>{chat_id}</code>)\n"
            )
            if full_note:
                admin_msg += f"📝 <b>Izoh:</b> {html.escape(full_note)}\n"
            admin_msg += (
                f"⏱ <b>Vaqt:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👉 <a href='tg://user?id={chat_id}'>Mijoz bilan Telegramda yozishish</a>"
            )
            self.send_message(self.admin_chat_id, admin_msg)

        # Confirm to User
        confirm_text = self.t(chat_id, 'lead_success', name=html.escape(name), phone=html.escape(phone))
        if chat_id in self.user_states:
            del self.user_states[chat_id]

        self.send_message(chat_id, confirm_text, reply_markup=self.get_main_keyboard(chat_id))

    # -----------------------------------------------------------------------
    # HANDLERS: ADMIN COMMANDS
    # -----------------------------------------------------------------------
    def handle_admin_panel(self, chat_id):
        if str(chat_id) != self.admin_chat_id:
            self.send_message(chat_id, "Siz admin emassiz.")
            return

        bot_users_count = BotUser.objects.count()
        leads_count = Lead.objects.count()
        new_leads_count = Lead.objects.filter(status=Lead.Status.NEW).count()
        homes_count = Home.objects.count()
        apts_count = Apartment.objects.count()

        text = (
            "📊 <b>XON SAROY ADMIN BOSHQARUV PANELI:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Bot foydalanuvchilari:</b> {bot_users_count} ta\n"
            f"📬 <b>Jami arizalar (Leads):</b> {leads_count} ta\n"
            f"🆕 <b>Yangi ko‘rilmagan arizalar:</b> {new_leads_count} ta\n"
            f"🏗 <b>Loyihalar soni:</b> {homes_count} ta\n"
            f"🔑 <b>Faol xonadonlar:</b> {apts_count} ta\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Quyidagi buyruqlardan foydalanishingiz mumkin:\n"
            "• So‘nggi arizalarni ko‘rish\n"
            "• Barcha foydalanuvchilarga xabar yuborish (<code>/broadcast [matn]</code>)"
        )
        kb = {
            'inline_keyboard': [
                [{'text': '📬 So‘nggi 5 ta ariza', 'callback_data': 'admin_recent_leads'}],
                [{'text': '📢 Xabar yuborish (Broadcast)', 'callback_data': 'admin_broadcast_prompt'}]
            ]
        }
        self.send_message(chat_id, text, reply_markup=kb)

    def handle_admin_recent_leads(self, chat_id):
        if str(chat_id) != self.admin_chat_id:
            return

        leads = Lead.objects.all().order_by('-created_at')[:5]
        if not leads.exists():
            self.send_message(chat_id, "Hozircha arizalar mavjud emas.")
            return

        text = "📬 <b>SO‘NGGI 5 TA ARIZA:</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for idx, l in enumerate(leads, 1):
            st_icon = '🆕' if l.status == 'new' else ('🟡' if l.status == 'in_contact' else '✅')
            text += (
                f"{idx}. {st_icon} <b>{l.name}</b> — <code>{l.phone}</code>\n"
                f"   Manba: {l.get_source_display()} | Vaqt: {l.created_at.strftime('%d.%m %H:%M')}\n"
            )
            if l.note:
                text += f"   Izoh: {l.note[:60]}...\n"
            text += "\n"

        self.send_message(chat_id, text)

    # -----------------------------------------------------------------------
    # POLLING LOOP
    # -----------------------------------------------------------------------
    def run_polling(self):
        logger.info("Telegram Bot ishga tushirildi! Polling boshlandi...")
        offset = 0

        while True:
            try:
                resp = requests.get(
                    f"{self.api_url}/getUpdates",
                    params={'offset': offset, 'timeout': 25},
                    timeout=35
                )
                resp.raise_for_status()
                data = resp.json()
                if not data.get('ok'):
                    if data.get('error_code') in (401, 409):
                        raise CommandError(
                            f"Telegram getUpdates xatosi: {data.get('description', 'token yoki polling muammosi')}"
                        )
                    logger.error("Telegram getUpdates xatosi: %s", data.get('description', 'noma’lum xato'))
                    time.sleep(2)
                    continue

                for update in data.get('result', []):
                    offset = update['update_id'] + 1

                    # 1. MESSAGE UPDATE
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        text = msg.get('text', '').strip()
                        user = msg.get('from', {})

                        # Record/update user activity
                        self.get_or_create_user(user)

                        # Contact sharing
                        if 'contact' in msg:
                            contact = msg['contact']
                            phone = contact.get('phone_number')
                            self.process_lead(chat_id, user, phone, "Kontakt tugmasi orqali yuborildi")
                            continue

                        # Text command routing
                        if text == '/start':
                            self.handle_start(chat_id, user)

                        elif text in ('/lang', '🌐 Tilni o‘zgartirish', '🌐 Сменить язык', '🌐 Change Language', '🌐 Til / Язык / Lang'):
                            self.handle_lang_prompt(chat_id)

                        elif text in ('🏢 Xon Saroy nima?', '🏢 О компании Xon Saroy', '🏢 About Xon Saroy', '/about'):
                            self.handle_about(chat_id)

                        elif text in ('🏗 Loyihalarimiz', '🏗 Наши проекты', '🏗 Our Projects', '/projects'):
                            self.handle_projects(chat_id)

                        elif text in ('🔑 Xonadonlar va Narxlar', '🔑 Квартиры и цены', '🔑 Apartments & Prices', '/apartments'):
                            self.handle_apartments(chat_id)

                        elif text in ('🧮 To‘lov kalkulyatori', '🧮 Калькулятор рассрочки', '🧮 Payment Calculator', '/calc'):
                            self.handle_calc_start(chat_id)

                        elif text in ('📍 Sotuv ofislari', '📍 Офисы продаж', '📍 Sales Offices', '/offices'):
                            self.handle_offices(chat_id)

                        elif text in ('🧱 Sifat va Materiallar', '🧱 Качество и материалы', '🧱 Quality & Materials', '/materials'):
                            self.handle_materials(chat_id)

                        elif text in ('⭐ Mamnun mijozlar', '⭐ Отзывы клиентов', '⭐ Customer Reviews', '/reviews'):
                            self.handle_reviews(chat_id)

                        elif text in ('📞 Konsultatsiya olish', '📞 Получить консультацию', '📞 Get Consultation', '/consult', '/contact'):
                            self.request_consultation_prompt(chat_id)

                        elif text in ('👤 Mening profilim', '👤 Мой профиль', '👤 My Profile', '/profile'):
                            self.handle_profile(chat_id, user)

                        elif text in ('🌐 Veb-saytga o‘tish', '🌐 Перейти на сайт', '🌐 Visit Website', '/website'):
                            site_url = f"{settings.SITE_URL}/"
                            kb = {'inline_keyboard': [[{'text': '🌐 Xon Saroy veb-saytini ochish', 'url': site_url}]]}
                            self.send_message(chat_id, "Xon Saroy rasmiy veb-saytiga tashrif buyuring:", reply_markup=kb)

                        elif text in ('📊 Admin panel', '/admin'):
                            self.handle_admin_panel(chat_id)

                        elif text.startswith('/broadcast') and str(chat_id) == self.admin_chat_id:
                            broadcast_msg = text.replace('/broadcast', '').strip()
                            if broadcast_msg:
                                users = BotUser.objects.values_list('telegram_id', flat=True)
                                sent_cnt = 0
                                for uid in users:
                                    try:
                                        self.send_message(uid, f"📢 <b>XON SAROY YANGILIK:</b>\n\n{broadcast_msg}")
                                        sent_cnt += 1
                                    except Exception:
                                        pass
                                self.send_message(chat_id, f"✅ Xabar {sent_cnt} ta foydalanuvchiga muvaffaqiyatli yetkazildi.")
                            else:
                                self.send_message(chat_id, "Foydalanish: <code>/broadcast [xabar matni]</code>")

                        elif text in ('⬅️ Asosiy menyu', '⬅️ Главное меню', '⬅️ Main Menu'):
                            if chat_id in self.user_states:
                                del self.user_states[chat_id]
                            self.send_message(chat_id, "Asosiy menyudasiz 👇", reply_markup=self.get_main_keyboard(chat_id))

                        elif self.user_states.get(chat_id, {}).get('state') == 'calc_custom_amount':
                            digits = ''.join(c for c in text if c.isdigit())
                            if digits and int(digits) > 10000000:
                                val = float(digits)
                                self.handle_calc_select_down(chat_id, val)
                            else:
                                self.send_message(chat_id, "Iltimos, to‘g‘ri summa kiriting (masalan: 500000000):")

                        elif self.user_states.get(chat_id, {}).get('state') == 'awaiting_contact':
                            self.process_lead(chat_id, user, text, self.user_states.get(chat_id, {}).get('note', 'Qo‘lda kiritilgan telefon/xabar'))

                        elif self.user_states.get(chat_id, {}).get('state') == 'admin_broadcast_input' and str(chat_id) == self.admin_chat_id:
                            users = BotUser.objects.values_list('telegram_id', flat=True)
                            sent_cnt = 0
                            for uid in users:
                                try:
                                    self.send_message(uid, f"📢 <b>XON SAROY:</b>\n\n{text}")
                                    sent_cnt += 1
                                except Exception:
                                    pass
                            del self.user_states[chat_id]
                            self.send_message(chat_id, f"✅ Xabar {sent_cnt} ta foydalanuvchiga yuborildi.")

                        else:
                            self.send_message(
                                chat_id,
                                "Iltimos, quyidagi menyu tugmalaridan birini tanlang yoki /start buyrug‘ini bosing 👇",
                                reply_markup=self.get_main_keyboard(chat_id)
                            )

                    # 2. CALLBACK QUERY (INLINE BUTTONS)
                    elif 'callback_query' in update:
                        cb = update['callback_query']
                        cb_id = cb['id']
                        chat_id = cb['message']['chat']['id']
                        data_val = cb.get('data', '')
                        user = cb.get('from', {})

                        self.answer_callback_query(cb_id)
                        self.get_or_create_user(user)

                        # Language selection
                        if data_val.startswith('set_lang_'):
                            lang_code = data_val.replace('set_lang_', '')
                            self.set_lang(chat_id, lang_code)
                            lang_titles = {'uz': 'O‘zbek tili tanlandi 🇺🇿', 'ru': 'Выбран русский язык 🇷🇺', 'en': 'English language selected 🇬🇧'}
                            self.send_message(chat_id, lang_titles.get(lang_code, 'OK'), reply_markup=self.get_main_keyboard(chat_id))

                        elif data_val == 'show_lang_modal':
                            self.handle_lang_prompt(chat_id)

                        # Projects
                        elif data_val == 'filter_proj_all':
                            self.handle_projects(chat_id)
                        elif data_val == 'filter_proj_in_progress':
                            self.handle_projects(chat_id, status_filter='in_progress')
                        elif data_val == 'filter_proj_completed':
                            self.handle_projects(chat_id, status_filter='completed')
                        elif data_val == 'filter_proj_soon':
                            self.handle_projects(chat_id, status_filter='soon')
                        elif data_val.startswith('proj_'):
                            pid = int(data_val.replace('proj_', ''))
                            self.handle_project_detail(chat_id, pid)
                        elif data_val.startswith('apts_proj_'):
                            pid = int(data_val.replace('apts_proj_', ''))
                            self.handle_apartments(chat_id, project_id=pid)
                        elif data_val.startswith('lead_proj_'):
                            pid = int(data_val.replace('lead_proj_', ''))
                            h = Home.objects.filter(id=pid).first()
                            note = f"Qiziqqan loyihasi: {h.name}" if h else "Loyiha bo'yicha maslahat"
                            self.request_consultation_prompt(chat_id, note=note)

                        # Apartments
                        elif data_val == 'apts_rm_all':
                            self.handle_apartments(chat_id)
                        elif data_val.startswith('apts_rm_'):
                            rm_str = data_val.replace('apts_rm_', '')
                            if rm_str.isdigit():
                                self.handle_apartments(chat_id, rooms=int(rm_str))
                        elif data_val.startswith('apt_detail_'):
                            aid = int(data_val.replace('apt_detail_', ''))
                            self.handle_apartment_detail(chat_id, aid)
                        elif data_val.startswith('calc_apt_'):
                            aid = int(data_val.replace('calc_apt_', ''))
                            a = Apartment.objects.filter(id=aid).first()
                            if a and a.price:
                                self.handle_calc_start(chat_id, default_price=a.price)
                            else:
                                self.handle_calc_start(chat_id)
                        elif data_val.startswith('book_apt_'):
                            aid = int(data_val.replace('book_apt_', ''))
                            a = Apartment.objects.filter(id=aid).first()
                            p_name = a.project.name if (a and a.project) else "Xon Saroy"
                            note = f"Band qilish uchun xonadon: {p_name}, {a.rooms}-xona, {a.area} m², {fmt_sum(a.price)} so'm" if a else "Xonadonni band qilish"
                            self.request_consultation_prompt(chat_id, note=note)

                        # Calculator
                        elif data_val == 'calc_start':
                            self.handle_calc_start(chat_id)
                        elif data_val.startswith('calc_pr_'):
                            pr_val = data_val.replace('calc_pr_', '')
                            if pr_val == 'custom':
                                self.user_states[chat_id] = {'state': 'calc_custom_amount'}
                                self.send_message(chat_id, "Iltimos, xonadon narxini so‘mda yozib yuboring (masalan: 450000000):")
                            elif pr_val.isdigit():
                                self.handle_calc_select_down(chat_id, float(pr_val))
                        elif data_val.startswith('calc_down_'):
                            pct_val = int(data_val.replace('calc_down_', ''))
                            self.handle_calc_select_period(chat_id, pct_val)
                        elif data_val.startswith('calc_per_'):
                            per_val = int(data_val.replace('calc_per_', ''))
                            self.handle_calc_compute(chat_id, per_val)

                        # Offices
                        elif data_val.startswith('office_loc_'):
                            oid = int(data_val.replace('office_loc_', ''))
                            self.handle_office_location(chat_id, oid)

                        # Consultation
                        elif data_val == 'req_consult':
                            self.request_consultation_prompt(chat_id)

                        # Admin
                        elif data_val == 'admin_recent_leads' and str(chat_id) == self.admin_chat_id:
                            self.handle_admin_recent_leads(chat_id)
                        elif data_val == 'admin_broadcast_prompt' and str(chat_id) == self.admin_chat_id:
                            self.user_states[chat_id] = {'state': 'admin_broadcast_input'}
                            self.send_message(chat_id, "Barcha foydalanuvchilarga yubormoqchi bo‘lgan xabaringizni yozib yuboring:")

            except CommandError:
                raise
            except requests.RequestException as err:
                logger.error("Telegram polling so‘rovi bajarilmadi (%s).", type(err).__name__)
                time.sleep(3)
            except Exception as err:
                logger.error("Polling loop exception (%s).", type(err).__name__)
                time.sleep(3)


# ---------------------------------------------------------------------------
# DJANGO MANAGEMENT COMMAND
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = 'Xon Saroy Telegram Botini ishga tushirish'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Token va polling sozlamalarini tekshiradi, botni ishga tushirmaydi.',
        )

    def handle(self, *args, **options):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '').strip()

        if not bot_token:
            raise CommandError(".env faylida TELEGRAM_BOT_TOKEN topilmadi.")

        bot = TelegramBot(token=bot_token, admin_chat_id=admin_chat_id)
        bot_info = bot.call_api('getMe')
        if not bot_info.get('ok'):
            raise CommandError(
                f"Telegram token tekshiruvi muvaffaqiyatsiz: {bot_info.get('description', 'API javob bermadi')}"
            )

        webhook_info = bot.call_api('getWebhookInfo')
        if not webhook_info.get('ok'):
            raise CommandError(
                f"Telegram webhook holatini tekshirib bo‘lmadi: {webhook_info.get('description', 'API javob bermadi')}"
            )
        webhook_url = webhook_info.get('result', {}).get('url', '')
        if webhook_url:
            raise CommandError(
                "Botda webhook sozlangan. Bu loyiha polling ishlatadi; webhookni o‘chirib, "
                "qayta `python manage.py runbot --check` buyrug‘ini bajaring."
            )

        username = bot_info.get('result', {}).get('username', 'noma’lum')
        status = f"Bot @{username} tokeni va polling sozlamalari to‘g‘ri."
        if admin_chat_id:
            status += " Admin xabarlari yoqilgan."
        else:
            status += " TELEGRAM_ADMIN_CHAT_ID kiritilmagan; admin xabarlari yuborilmaydi."
        if options['check']:
            self.stdout.write(self.style.SUCCESS(status))
            return

        self.stdout.write(self.style.SUCCESS(f"{status} Bot ishga tushmoqda..."))
        bot.run_polling()
