import os
import sys
import time
import json
import logging
import requests
import html
from urllib.parse import urlparse
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from app.models import Home, Apartment, SalesOffice, Material, Client, User, BotUser, Lead, Category

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
            "• 🏗 Zamonaviy <b>turar-joy majmualarimizni</b> ko'rishingiz mumkin\n"
            "• 🔑 Bo'sh <b>xonadonlar, rejalari va narxlarini</b> ko'rishingiz mumkin\n"
            "• 🧮 0% <b>muddatli to'lov va oylik to'lovni</b> bir zumda hisoblashingiz mumkin\n"
            "• 📍 Eng yaqin <b>sotuv ofislarimiz</b> manzillari va lokatsiyasini olasiz\n"
            "• 📞 1 daqiqada <b>bepul konsultatsiya</b> uchun ariza qoldirishingiz mumkin\n\n"
            "Kerakli bo'limni tanlang 👇"
        ),
        'menu_about': '🏢 Xon Saroy nima?',
        'menu_projects': '🏗 Loyihalarimiz',
        'menu_apartments': '🔑 Xonadonlar va Narxlar',
        'menu_calc': '🧮 To\u2018lov kalkulyatori',
        'menu_offices': '📍 Sotuv ofislari',
        'menu_materials': '🧱 Sifat va Materiallar',
        'menu_reviews': '⭐ Mamnun mijozlar',
        'menu_consult': '📞 Konsultatsiya olish',
        'menu_profile': '👤 Mening profilim',
        'menu_website': '🌐 Veb-saytga o\u2018tish',
        'menu_lang': '🌐 Tilni o\u2018zgartirish',
        'menu_admin': '📊 Admin panel',
        'btn_back': '⬅️ Asosiy menyu',
        'btn_share_contact': '📱 Telefon raqamimni yuborish',
        'about_text': (
            "🏢 <b>XON SAROY NIMA?</b>\n\n"
            "<b>Xon Saroy</b> — O'zbekiston ko'chmas mulk bozorida mustahkam o'ringa ega bo'lgan, "
            "zamonaviy va nufuzli developerlik kompaniyasidir.\n\n"
            "Biz shunchaki ko'p qavatli binolar qurmaymiz, balki insonlar xavfsiz, xotirjam va "
            "farovon yashaydigan <b>yangi hayot tarzini</b> yaratamiz.\n\n"
            "💎 <b>BIZNING USTUNLIKLARIMIZ:</b>\n\n"
            "🔹 <b>9 ballik seysmik chidamlilik:</b> Barcha majmualar eng yuqori mustahkamlik talablariga javob beruvchi monolit-karkas texnologiyasi asosida qad rostlaydi.\n\n"
            "🔹 <b>Mukammal infratuzilma:</b> Yerosti avtoturargohlari, 24/7 qo'riqlash va videokuzatuv xizmati, ekologik toza yashil hovlilar, bolalar va sport maydonchalari.\n\n"
            "🔹 <b>Sifatli va ekologik materiallar:</b> Issiqlik va shovqin izolyatsiyasi yuqori pishiq g'ishtlar, tejamkor panoramik oynalar va ovozsiz tezyurar liftlar.\n\n"
            "🔹 <b>0% foizsiz muddatli to'lov:</b> Boshlang'ich to'lov 15-20% dan boshlab, 36 oygacha qulay to'lov jadvallari.\n\n"
            "🔹 <b>Qonuniy kafolat:</b> Har bir xonadon to'liq qonuniy kadastr hujjatlari bilan o'z vaqtida topshiriladi."
        ),
        'consult_prompt': (
            "📞 <b>BEPUL KONSULTATSIYA OLISH</b>\n\n"
            "Iltimos, telefon raqamingizni qoldiring. <b>Xon Saroy</b> mutaxassisi tez orada siz bilan bog'lanib, "
            "barcha savollaringizga batafsil javob beradi va eng yaxshi takliflarni taqdim etadi.\n\n"
            "Quyidagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing yoki raqamingizni yozib yuboring (masalan: +998901234567):"
        ),
        'lead_success': (
            "✅ <b>Rahmat, {name}!</b>\n\n"
            "Arizangiz muvaffaqiyatli qabul qilindi. Tez orada <b>Xon Saroy</b> sotuv bo'limi mutaxassisi "
            "<b>{phone}</b> raqamingizga qo'ng'iroq qiladi."
        ),
        'profile_text': (
            "👤 <b>SIZNING PROFILINGIZ:</b>\n\n"
            "🆔 <b>Telegram ID:</b> <code>{tg_id}</code>\n"
            "👤 <b>Ism:</b> {name}\n"
            "💬 <b>Username:</b> {username}\n"
            "🌐 <b>Tanlangan til:</b> {lang_name}\n\n"
            "{site_status}\n\n"
            "💡 <i>Eslatma: Telegram ID raqamingizni veb-saytdagi shaxsiy profilingizda kiritib, "
            "hisoblaringizni o'zaro bog'lashingiz mumkin.</i>"
        ),
        'calc_intro': (
            "🧮 <b>MUDDATLI TO'LOV KALKULYATORI</b>\n\n"
            "Xon Saroy majmualarida 0% foizsiz muddatli to'lov asosida xonadon xarid qilishingiz mumkin!\n\n"
            "Kerakli narx toifasini tanlang yoki o'z summasini yozib yuboring 👇"
        ),
        'calc_down_prompt': (
            "💰 <b>Xonadon qiymati:</b> {price} so'm\n\n"
            "Endi <b>boshlang'ich to'lov</b> foizini tanlang 👇"
        ),
        'calc_period_prompt': (
            "💰 <b>Xonadon qiymati:</b> {price} so'm\n"
            "💳 <b>Boshlang'ich to'lov ({pct}%):</b> {down_sum} so'm\n\n"
            "Endi <b>to'lov muddatini</b> tanlang 👇"
        ),
        'calc_result': (
            "🧮 <b>MUDDATLI TO'LOV HISOB-KITOBI:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Xonadon qiymati:</b> {price} so'm\n"
            "💳 <b>Boshlang'ich to'lov ({pct}%):</b> {down_sum} so'm\n"
            "📉 <b>Qolgan summa:</b> {rem_sum} so'm\n"
            "📅 <b>To'lov muddati:</b> {period} oy\n"
            "💵 <b>Oylik to'lov:</b> <b>{monthly} so'm/oy</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>* 0% foizsiz qulay muddatli to'lov shartlari asosida hisoblandi.</i>\n\n"
            "Ushbu shartlar bo'yicha mutaxassis bilan bog'lanmoqchimisiz?"
        ),
        # Apartment section
        'apt_header': "🔑 <b>XONADONLAR VA NARXLAR</b>\n\n",
        'apt_rooms_prompt': "Qanday xonadon qidiryapsiz? Xonalar sonini tanlang 👇",
        'apt_all_rooms': '📋 Barcha xonadonlar',
        'apt_room_btn': '{n} xonali',
        'apt_filter_project': '🏗 Loyiha bo\u2018yicha',
        'apt_count': "Jami <b>{count}</b> ta xonadon topildi:",
        'apt_no_results': "Ushbu parametrlar bo'yicha hozircha xonadonlar topilmadi.",
        'apt_card': (
            "🏢 <b>{project}</b>\n"
            "🚪 {rooms} xonali · 🏢 {floor}-qavat · 📐 {area} m²\n"
            "💰 <b>{price} so'm</b>\n"
            "{status_icon} {status_text}"
        ),
        'apt_detail_header': (
            "🔑 <b>XONADON PASPORTI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Majmua:</b> {project}\n"
            "🔢 <b>Xonadon raqami:</b> {unit}\n"
            "🚪 <b>Xonalar soni:</b> {rooms} xonali\n"
            "🏢 <b>Qavat:</b> {floor}-qavat\n"
            "📐 <b>Umumiy maydon:</b> {area} m²\n"
            "💰 <b>1 m² narxi:</b> ~{m2_price} so'm\n"
            "🏷 <b>Umumiy narx:</b> <b>{price} so'm</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>Boshlang'ich to'lov (15%):</b> {down_15} so'm\n"
            "📅 <b>Oylik to'lov (36 oy):</b> {monthly_36} so'm/oy\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Holati:</b> {availability}\n"
        ),
        'apt_desc_prefix': "\n📝 <b>Tavsif:</b> {desc}\n",
        'btn_calc_apt': '🧮 To\u2018lovni hisoblash',
        'btn_book_apt': '📞 Ushbu xonadonni band qilish',
        'btn_back_apts': '⬅️ Xonadonlar ro\u2018yxati',
        'btn_apt_next': '➡️ Keyingi sahifa',
        'btn_apt_prev': '⬅️ Oldingi sahifa',
        'page_info': '📄 Sahifa {cur}/{total}',
        'availability_available': '🟢 Bo\u2018sh',
        'availability_reserved': '🟡 Bron qilingan',
        'availability_sold': '🔴 Sotilgan',
        'apt_unavailable': '🔒 Bu xonadon band',
        # Projects section
        'proj_header': "🏗 <b>BIZNING LOYIHALARIMIZ</b>\n\n",
        'proj_filter_status': "Holat bo'yicha saralash:",
        'proj_all': '📑 Barcha loyihalar',
        'proj_in_progress': '🟡 Jarayonda',
        'proj_completed': '🟢 Yakunlangan',
        'proj_soon': '🟣 Tez kunda',
        'proj_count': "{count} ta loyiha topildi.\nBatafsil ko'rish uchun loyihani tanlang 👇",
        'proj_no_results': "Loyihalar topilmadi.",
        'proj_detail': (
            "🏢 <b>«{name}»</b>\n\n"
            "📌 <b>Toifasi:</b> {category}\n"
            "📊 <b>Holati:</b> {status}\n"
            "🔑 <b>Mavjud xonadonlar:</b> {apt_count} ta\n\n"
            "{description}\n"
        ),
        'btn_proj_apts': '🔑 Xonadonlarni ko\u2018rish ({count} ta)',
        'btn_proj_consult': '📞 Ushbu loyiha uchun maslahat',
        'btn_proj_back': '⬅️ Loyihalar ro\u2018yxati',
        # Category filter
        'cat_filter': '📂 Kategoriya bo\u2018yicha',
        'cat_all': 'Barchasi',
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
        ),
        # Apartment section
        'apt_header': "🔑 <b>КВАРТИРЫ И ЦЕНЫ</b>\n\n",
        'apt_rooms_prompt': "Какую квартиру ищете? Выберите количество комнат 👇",
        'apt_all_rooms': '📋 Все квартиры',
        'apt_room_btn': '{n}-комнатная',
        'apt_filter_project': '🏗 По проекту',
        'apt_count': "Найдено <b>{count}</b> квартир:",
        'apt_no_results': "По данным параметрам квартиры пока не найдены.",
        'apt_card': (
            "🏢 <b>{project}</b>\n"
            "🚪 {rooms}-комн. · 🏢 {floor} этаж · 📐 {area} м²\n"
            "💰 <b>{price} сум</b>\n"
            "{status_icon} {status_text}"
        ),
        'apt_detail_header': (
            "🔑 <b>КАРТОЧКА КВАРТИРЫ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Комплекс:</b> {project}\n"
            "🔢 <b>Номер квартиры:</b> {unit}\n"
            "🚪 <b>Количество комнат:</b> {rooms}-комнатная\n"
            "🏢 <b>Этаж:</b> {floor}\n"
            "📐 <b>Площадь:</b> {area} м²\n"
            "💰 <b>Цена за 1 м²:</b> ~{m2_price} сум\n"
            "🏷 <b>Общая стоимость:</b> <b>{price} сум</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>Первоначальный взнос (15%):</b> {down_15} сум\n"
            "📅 <b>Ежемесячный платёж (36 мес.):</b> {monthly_36} сум/мес.\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Статус:</b> {availability}\n"
        ),
        'apt_desc_prefix': "\n📝 <b>Описание:</b> {desc}\n",
        'btn_calc_apt': '🧮 Рассчитать рассрочку',
        'btn_book_apt': '📞 Забронировать эту квартиру',
        'btn_back_apts': '⬅️ Список квартир',
        'btn_apt_next': '➡️ Следующая',
        'btn_apt_prev': '⬅️ Предыдущая',
        'page_info': '📄 Страница {cur}/{total}',
        'availability_available': '🟢 Свободна',
        'availability_reserved': '🟡 Забронирована',
        'availability_sold': '🔴 Продана',
        'apt_unavailable': '🔒 Квартира недоступна',
        # Projects section
        'proj_header': "🏗 <b>НАШИ ПРОЕКТЫ</b>\n\n",
        'proj_filter_status': "Фильтр по статусу:",
        'proj_all': '📑 Все проекты',
        'proj_in_progress': '🟡 Строящиеся',
        'proj_completed': '🟢 Завершённые',
        'proj_soon': '🟣 Скоро в продаже',
        'proj_count': "Найдено {count} проектов.\nВыберите проект для подробной информации 👇",
        'proj_no_results': "Проекты не найдены.",
        'proj_detail': (
            "🏢 <b>«{name}»</b>\n\n"
            "📌 <b>Категория:</b> {category}\n"
            "📊 <b>Статус:</b> {status}\n"
            "🔑 <b>Доступно планировок:</b> {apt_count}\n\n"
            "{description}\n"
        ),
        'btn_proj_apts': '🔑 Квартиры ({count})',
        'btn_proj_consult': '📞 Консультация по проекту',
        'btn_proj_back': '⬅️ Список проектов',
        # Category filter
        'cat_filter': '📂 По категории',
        'cat_all': 'Все',
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
        ),
        # Apartment section
        'apt_header': "🔑 <b>APARTMENTS & PRICES</b>\n\n",
        'apt_rooms_prompt': "What apartment are you looking for? Select the number of rooms 👇",
        'apt_all_rooms': '📋 All apartments',
        'apt_room_btn': '{n}-bedroom',
        'apt_filter_project': '🏗 By Project',
        'apt_count': "Found <b>{count}</b> apartments:",
        'apt_no_results': "No apartments found for this filter.",
        'apt_card': (
            "🏢 <b>{project}</b>\n"
            "🚪 {rooms}-bed · 🏢 Floor {floor} · 📐 {area} m²\n"
            "💰 <b>{price} UZS</b>\n"
            "{status_icon} {status_text}"
        ),
        'apt_detail_header': (
            "🔑 <b>APARTMENT DETAILS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 <b>Complex:</b> {project}\n"
            "🔢 <b>Unit Number:</b> {unit}\n"
            "🚪 <b>Rooms:</b> {rooms}-bedroom\n"
            "🏢 <b>Floor:</b> {floor}\n"
            "📐 <b>Area:</b> {area} m²\n"
            "💰 <b>Price per m²:</b> ~{m2_price} UZS\n"
            "🏷 <b>Total Price:</b> <b>{price} UZS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>Down Payment (15%):</b> {down_15} UZS\n"
            "📅 <b>Monthly (36 mos):</b> {monthly_36} UZS/mo\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Status:</b> {availability}\n"
        ),
        'apt_desc_prefix': "\n📝 <b>Description:</b> {desc}\n",
        'btn_calc_apt': '🧮 Calculate installment',
        'btn_book_apt': '📞 Book this apartment',
        'btn_back_apts': '⬅️ Apartments list',
        'btn_apt_next': '➡️ Next page',
        'btn_apt_prev': '⬅️ Previous page',
        'page_info': '📄 Page {cur}/{total}',
        'availability_available': '🟢 Available',
        'availability_reserved': '🟡 Reserved',
        'availability_sold': '🔴 Sold',
        'apt_unavailable': '🔒 Apartment unavailable',
        # Projects section
        'proj_header': "🏗 <b>OUR PROJECTS</b>\n\n",
        'proj_filter_status': "Filter by status:",
        'proj_all': '📑 All Projects',
        'proj_in_progress': '🟡 Active',
        'proj_completed': '🟢 Completed',
        'proj_soon': '🟣 Coming Soon',
        'proj_count': "Found {count} projects.\nSelect a project for details 👇",
        'proj_no_results': "No projects found.",
        'proj_detail': (
            "🏢 <b>«{name}»</b>\n\n"
            "📌 <b>Category:</b> {category}\n"
            "📊 <b>Status:</b> {status}\n"
            "🔑 <b>Available units:</b> {apt_count}\n\n"
            "{description}\n"
        ),
        'btn_proj_apts': '🔑 View Apartments ({count})',
        'btn_proj_consult': '📞 Consult for Project',
        'btn_proj_back': '⬅️ Projects List',
        # Category filter
        'cat_filter': '📂 By Category',
        'cat_all': 'All',
    }
}


def fmt_sum(val):
    try:
        return f"{int(round(float(val))):,}".replace(',', ' ')
    except Exception:
        return str(val)


APARTMENTS_PER_PAGE = 5


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
        url = f"{self.api_url}/{method}"
        last_error = None

        for attempt in range(1, 4):
            try:
                resp = requests.post(url, data=data, files=files, timeout=35)
                return resp.json()
            except requests.RequestException as err:
                last_error = err
                logger.warning(
                    "Telegram API so'rovi bajarilmadi (%s), urinish %s/3: %s",
                    method,
                    attempt,
                    type(err).__name__,
                )
                if attempt < 3:
                    time.sleep(attempt * 2)
            except Exception as err:
                last_error = err
                logger.error(
                    "Telegram API javobi o'qilmadi (%s): %s",
                    method,
                    type(err).__name__,
                )
                break

        if last_error:
            logger.error("Telegram API so'rovi 3 urinishdan keyin bajarilmadi (%s).", method)
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

    def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode='HTML'):
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        return self.call_api('editMessageText', data)

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

    def send_media_group(self, chat_id, media):
        """Send a group of photos as an album."""
        data = {
            'chat_id': chat_id,
            'media': json.dumps(media),
        }
        return self.call_api('sendMediaGroup', data)

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

    def delete_message(self, chat_id, message_id):
        return self.call_api('deleteMessage', {'chat_id': chat_id, 'message_id': message_id})

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

    def get_availability_text(self, chat_id, availability):
        lang = self.get_lang(chat_id)
        mapping = {
            'available': self.t(chat_id, 'availability_available'),
            'reserved': self.t(chat_id, 'availability_reserved'),
            'sold': self.t(chat_id, 'availability_sold'),
        }
        return mapping.get(availability, mapping['available'])

    def get_availability_icon(self, availability):
        return {'available': '🟢', 'reserved': '🟡', 'sold': '🔴'}.get(availability, '🟢')

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
            "🇺🇿 <b>O'zbekcha</b> — O'zbek tili\n"
            "🇷🇺 <b>Русский</b> — Русский язык\n"
            "🇬🇧 <b>English</b> — English language"
        )
        kb = {
            'inline_keyboard': [
                [{'text': "🇺🇿 O'zbekcha", 'callback_data': 'set_lang_uz'}],
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
        btn_projects = '🏗 Loyihalarni ko\u2018rish' if lang == 'uz' else ('🏗 Смотреть проекты' if lang == 'ru' else '🏗 View Projects')
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
    # HANDLERS: PROJECTS (improved with categories and images)
    # -----------------------------------------------------------------------
    def handle_projects(self, chat_id, status_filter=None, category_filter=None):
        homes = Home.objects.select_related('category').order_by('id')
        if status_filter:
            homes = homes.filter(status=status_filter)
        if category_filter:
            homes = homes.filter(category_id=category_filter)

        lang = self.get_lang(chat_id)
        count = homes.count()

        # Build header
        text = self.t(chat_id, 'proj_header')
        if count == 0:
            text += self.t(chat_id, 'proj_no_results')
            self.send_message(chat_id, text)
            return

        text += self.t(chat_id, 'proj_count', count=count)

        # Status filter row
        filter_row = [
            {'text': self.t(chat_id, 'proj_in_progress'), 'callback_data': 'filter_proj_in_progress'},
            {'text': self.t(chat_id, 'proj_completed'), 'callback_data': 'filter_proj_completed'},
            {'text': self.t(chat_id, 'proj_soon'), 'callback_data': 'filter_proj_soon'}
        ]
        all_row = [{'text': self.t(chat_id, 'proj_all'), 'callback_data': 'filter_proj_all'}]

        # Category filter row
        categories = Category.objects.all()
        cat_buttons = []
        if categories.exists():
            cat_row = [{'text': self.t(chat_id, 'cat_all'), 'callback_data': 'filter_proj_cat_all'}]
            for cat in categories:
                cat_row.append({'text': cat.name, 'callback_data': f"filter_proj_cat_{cat.id}"})
            cat_buttons = [cat_row]

        # Project buttons — each with status icon
        project_buttons = []
        for h in homes:
            icon = '🟢' if h.status == 'completed' else ('🟡' if h.status == 'in_progress' else '🟣')
            apt_count = h.apartments.filter(is_active=True).count()
            btn_text = f"{icon} {h.name}"
            if apt_count > 0:
                btn_text += f" ({apt_count})"
            project_buttons.append([{'text': btn_text, 'callback_data': f"proj_{h.id}"}])

        inline_kb = {'inline_keyboard': [filter_row, all_row] + cat_buttons + project_buttons}
        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_project_detail(self, chat_id, project_id):
        try:
            home = Home.objects.select_related('category').get(id=project_id)
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

        category_name = home.category.name if home.category else ("Turar-joy majmuasi" if lang == 'uz' else ("Жилой комплекс" if lang == 'ru' else "Residential Complex"))
        apts = home.apartments.filter(is_active=True)
        apt_count = apts.count()
        default_desc = {
            'uz': 'Zamonaviy arxitektura, qulay infratuzilma va yerosti avtoturargoh.',
            'ru': 'Современная архитектура, развитая инфраструктура и подземный паркинг.',
            'en': 'Modern architecture, developed infrastructure and underground parking.',
        }

        # Price range
        prices = list(apts.values_list('price', flat=True))
        price_info = ""
        if prices:
            min_p = fmt_sum(min(prices))
            max_p = fmt_sum(max(prices))
            if lang == 'uz':
                price_info = f"\n💰 <b>Narx oralig'i:</b> {min_p} — {max_p} so'm"
            elif lang == 'ru':
                price_info = f"\n💰 <b>Диапазон цен:</b> {min_p} — {max_p} сум"
            else:
                price_info = f"\n💰 <b>Price range:</b> {min_p} — {max_p} UZS"

        # Room stats
        room_counts = {}
        for a in apts:
            room_counts[a.rooms] = room_counts.get(a.rooms, 0) + 1
        room_info = ""
        if room_counts:
            parts = []
            for r in sorted(room_counts.keys()):
                if lang == 'uz':
                    parts.append(f"{r} xonali — {room_counts[r]} ta")
                elif lang == 'ru':
                    parts.append(f"{r}-комн. — {room_counts[r]}")
                else:
                    parts.append(f"{r}-bed — {room_counts[r]}")
            room_info = "\n🚪 " + " | ".join(parts)

        text = self.t(chat_id, 'proj_detail',
            name=home.name,
            category=category_name,
            status=st_text,
            apt_count=apt_count,
            description=home.description or default_desc.get(lang, default_desc['uz'])
        )
        text += price_info
        text += room_info

        # Buttons
        inline_buttons = []
        if apt_count > 0:
            # Room filter buttons for this project
            room_row = []
            for r in sorted(room_counts.keys()):
                if lang == 'uz':
                    label = f"{r} xonali ({room_counts[r]})"
                elif lang == 'ru':
                    label = f"{r}-комн. ({room_counts[r]})"
                else:
                    label = f"{r}-bed ({room_counts[r]})"
                room_row.append({'text': label, 'callback_data': f"apts_proj_{home.id}_rm_{r}"})
            # Split room_row into chunks of 3
            for i in range(0, len(room_row), 3):
                inline_buttons.append(room_row[i:i+3])

            inline_buttons.append([{'text': self.t(chat_id, 'btn_proj_apts', count=apt_count), 'callback_data': f"apts_proj_{home.id}"}])

        inline_buttons.append([{'text': self.t(chat_id, 'btn_proj_consult'), 'callback_data': f"lead_proj_{home.id}"}])
        inline_buttons.append([{'text': self.t(chat_id, 'btn_proj_back'), 'callback_data': 'filter_proj_all'}])

        inline_kb = {'inline_keyboard': inline_buttons}

        img = None
        if home.hero_image and os.path.exists(home.hero_image.path):
            img = home.hero_image.path
        elif home.hero_image_url:
            img = home.hero_image_url
        elif home.image and os.path.exists(home.image.path):
            img = home.image.path
        elif home.image_url:
            img = home.image_url

        if img:
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: APARTMENTS (completely redesigned with pagination, room
    #            filter, project filter, inline cards with images)
    # -----------------------------------------------------------------------
    def _build_apartment_queryset(self, rooms=None, project_id=None, availability=None):
        apts = Apartment.objects.filter(is_active=True).select_related('project')
        if rooms:
            apts = apts.filter(rooms=rooms)
        if project_id:
            apts = apts.filter(project_id=project_id)
        if availability:
            apts = apts.filter(availability=availability)
        return apts.order_by('sort_order', 'id')

    def handle_apartments_menu(self, chat_id):
        """Show room selection menu first, like the website's filter."""
        lang = self.get_lang(chat_id)
        text = self.t(chat_id, 'apt_header')
        text += self.t(chat_id, 'apt_rooms_prompt')

        # Get available room counts
        room_stats = {}
        for apt in Apartment.objects.filter(is_active=True).values('rooms'):
            r = apt['rooms']
            room_stats[r] = room_stats.get(r, 0) + 1
        total = sum(room_stats.values())

        # Build room filter buttons
        room_buttons = []
        for r in sorted(room_stats.keys()):
            label = self.t(chat_id, 'apt_room_btn', n=r)
            label += f" ({room_stats[r]})"
            room_buttons.append({'text': label, 'callback_data': f"apts_rm_{r}_p1"})

        # Split into rows of 2-3
        button_rows = []
        for i in range(0, len(room_buttons), 3):
            button_rows.append(room_buttons[i:i+3])

        # All apartments button
        all_btn = [{'text': f"{self.t(chat_id, 'apt_all_rooms')} ({total})", 'callback_data': 'apts_all_p1'}]

        # Project filter
        projects = Home.objects.filter(apartments__is_active=True).distinct().order_by('name')
        proj_buttons = []
        for p in projects:
            cnt = p.apartments.filter(is_active=True).count()
            proj_buttons.append({'text': f"{p.name} ({cnt})", 'callback_data': f"apts_proj_{p.id}"})
        proj_rows = []
        for i in range(0, len(proj_buttons), 2):
            proj_rows.append(proj_buttons[i:i+2])

        # Availability filter
        avail_row = []
        for val, label_uz in [('available', '🟢'), ('reserved', '🟡')]:
            cnt = Apartment.objects.filter(is_active=True, availability=val).count()
            if cnt > 0:
                lbl = self.get_availability_text(chat_id, val)
                avail_row.append({'text': f"{lbl} ({cnt})", 'callback_data': f"apts_avail_{val}_p1"})

        inline_kb = {'inline_keyboard': button_rows + [all_btn] + proj_rows}
        if avail_row:
            inline_kb['inline_keyboard'].append(avail_row)

        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_apartments_list(self, chat_id, page=1, rooms=None, project_id=None, availability=None):
        """Show paginated apartment list with inline cards."""
        apts = self._build_apartment_queryset(rooms, project_id, availability)
        total_count = apts.count()
        lang = self.get_lang(chat_id)

        if total_count == 0:
            text = self.t(chat_id, 'apt_header')
            text += self.t(chat_id, 'apt_no_results')
            back_btn = [{'text': '⬅️', 'callback_data': 'apts_menu'}]
            self.send_message(chat_id, text, reply_markup={'inline_keyboard': [back_btn]})
            return

        total_pages = (total_count + APARTMENTS_PER_PAGE - 1) // APARTMENTS_PER_PAGE
        page = max(1, min(page, total_pages))
        offset = (page - 1) * APARTMENTS_PER_PAGE
        page_apts = list(apts[offset:offset + APARTMENTS_PER_PAGE])

        # Build filter suffix for callback
        filter_suffix = ""
        if project_id and rooms:
            filter_suffix = f"_proj_{project_id}_rm_{rooms}"
        elif rooms:
            filter_suffix = f"_rm_{rooms}"
        elif project_id:
            filter_suffix = f"_proj_{project_id}"
        elif availability:
            filter_suffix = f"_avail_{availability}"
        else:
            filter_suffix = "_all"

        # Header
        text = self.t(chat_id, 'apt_header')
        text += self.t(chat_id, 'apt_count', count=total_count) + "\n"
        if total_pages > 1:
            text += self.t(chat_id, 'page_info', cur=page, total=total_pages) + "\n"
        text += "\n"

        # Apartment cards inline
        for apt in page_apts:
            p_name = apt.project.name if apt.project else "Xon Saroy"
            avail_text = self.get_availability_text(chat_id, apt.availability)
            avail_icon = self.get_availability_icon(apt.availability)
            text += self.t(chat_id, 'apt_card',
                project=p_name,
                rooms=apt.rooms,
                floor=apt.floor,
                area=apt.area,
                price=fmt_sum(apt.price),
                status_icon=avail_icon,
                status_text=avail_text
            )
            unit_label = apt.unit_number or f"#{apt.id}"
            text += f" · <code>{unit_label}</code>\n\n"

        # Build inline buttons — each apartment detail button
        buttons = []
        for apt in page_apts:
            p_name = apt.project.name if apt.project else "Xon Saroy"
            unit_label = apt.unit_number or f"#{apt.id}"
            if lang == 'uz':
                btn_text = f"📋 {p_name} · {apt.rooms}x · {apt.area}m² · {unit_label}"
            elif lang == 'ru':
                btn_text = f"📋 {p_name} · {apt.rooms}к · {apt.area}м² · {unit_label}"
            else:
                btn_text = f"📋 {p_name} · {apt.rooms}bd · {apt.area}m² · {unit_label}"
            buttons.append([{'text': btn_text, 'callback_data': f"apt_detail_{apt.id}"}])

        # Pagination
        nav_row = []
        if page > 1:
            nav_row.append({'text': self.t(chat_id, 'btn_apt_prev'), 'callback_data': f"aptpage{filter_suffix}_p{page-1}"})
        if page < total_pages:
            nav_row.append({'text': self.t(chat_id, 'btn_apt_next'), 'callback_data': f"aptpage{filter_suffix}_p{page+1}"})
        if nav_row:
            buttons.append(nav_row)

        # Back to filter menu
        buttons.append([{'text': '🔍 ' + (
            'Filtrni o\u2018zgartirish' if lang == 'uz' else ('Изменить фильтр' if lang == 'ru' else 'Change filter')
        ), 'callback_data': 'apts_menu'}])

        inline_kb = {'inline_keyboard': buttons}
        self.send_message(chat_id, text, reply_markup=inline_kb)

    def handle_apartment_detail(self, chat_id, apt_id):
        try:
            apt = Apartment.objects.select_related('project', 'project__category').get(id=apt_id)
        except Apartment.DoesNotExist:
            self.send_message(chat_id, "Xonadon topilmadi.")
            return

        lang = self.get_lang(chat_id)
        proj_name = apt.project.name if apt.project else "Xon Saroy"
        total_price = fmt_sum(apt.price)
        m2_price = fmt_sum(round(float(apt.price) / float(apt.area))) if apt.area else '0'
        down_15 = fmt_sum(round(float(apt.price) * 0.15))
        monthly_36 = fmt_sum(round(float(apt.price) * 0.85 / 36))
        unit_label = apt.unit_number or f"#{apt.id}"

        avail_text = self.get_availability_text(chat_id, apt.availability)

        text = self.t(chat_id, 'apt_detail_header',
            project=proj_name,
            unit=unit_label,
            rooms=apt.rooms,
            floor=apt.floor,
            area=apt.area,
            m2_price=m2_price,
            price=total_price,
            down_15=down_15,
            monthly_36=monthly_36,
            availability=avail_text
        )

        if apt.description:
            text += self.t(chat_id, 'apt_desc_prefix', desc=apt.description)

        # Buttons
        inline_buttons = [
            [{'text': self.t(chat_id, 'btn_calc_apt'), 'callback_data': f"calc_apt_{apt.id}"}],
        ]
        if apt.availability == 'available':
            inline_buttons.append([{'text': self.t(chat_id, 'btn_book_apt'), 'callback_data': f"book_apt_{apt.id}"}])
        else:
            inline_buttons.append([{'text': self.t(chat_id, 'apt_unavailable'), 'callback_data': 'noop'}])

        # Website link for this apartment
        site_url = getattr(settings, 'SITE_URL', 'https://akbarshoh.pythonanywhere.com').rstrip('/')
        inline_buttons.append([
            {'text': '🌐 ' + ('Saytda ko\u2018rish' if lang == 'uz' else ('Смотреть на сайте' if lang == 'ru' else 'View on website')),
             'url': f"{site_url}/#apartments"}
        ])
        inline_buttons.append([{'text': self.t(chat_id, 'btn_back_apts'), 'callback_data': 'apts_menu'}])

        inline_kb = {'inline_keyboard': inline_buttons}

        # Try to send with image
        img = None
        if apt.image and os.path.exists(apt.image.path):
            img = apt.image.path
        elif apt.image_url:
            img = apt.image_url
        elif apt.project:
            if apt.project.hero_image and os.path.exists(apt.project.hero_image.path):
                img = apt.project.hero_image.path
            elif apt.project.hero_image_url:
                img = apt.project.hero_image_url
            elif apt.project.image and os.path.exists(apt.project.image.path):
                img = apt.project.image.path
            elif apt.project.image_url:
                img = apt.project.image_url

        if img:
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: CALCULATOR (MUDDATLI TO'LOV / INSTALLMENTS)
    # -----------------------------------------------------------------------
    def handle_calc_start(self, chat_id, default_price=None):
        text = self.t(chat_id, 'calc_intro')
        lang = self.get_lang(chat_id)

        # Get real price ranges from apartments
        apts_prices = list(Apartment.objects.filter(is_active=True).values_list('price', flat=True).order_by('price'))
        price_buttons = []
        if apts_prices:
            # Show min, median and max as quick picks
            min_price = int(apts_prices[0])
            max_price = int(apts_prices[-1])
            mid_price = int(apts_prices[len(apts_prices)//2])

            seen = set()
            for p in [min_price, mid_price, max_price]:
                rounded = round(p, -6)  # round to nearest million
                if rounded > 0 and rounded not in seen:
                    seen.add(rounded)
                    price_buttons.append({'text': f"{fmt_sum(rounded)} so'm", 'callback_data': f"calc_pr_{rounded}"})

        # Fallback standard prices
        if len(price_buttons) < 2:
            price_buttons = [
                {'text': '350 000 000 so\'m', 'callback_data': 'calc_pr_350000000'},
                {'text': '500 000 000 so\'m', 'callback_data': 'calc_pr_500000000'},
                {'text': '700 000 000 so\'m', 'callback_data': 'calc_pr_700000000'},
                {'text': '1 000 000 000 so\'m', 'callback_data': 'calc_pr_1000000000'},
            ]

        # Split into rows of 2
        btn_rows = []
        for i in range(0, len(price_buttons), 2):
            btn_rows.append(price_buttons[i:i+2])
        custom_label = "✏️ O'z summasini yozish" if lang == 'uz' else ("✏️ Ввести свою сумму" if lang == 'ru' else "✏️ Enter custom amount")
        btn_rows.append([{'text': custom_label, 'callback_data': 'calc_pr_custom'}])

        inline_kb = {'inline_keyboard': btn_rows}

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
                [{'text': '🔄 ' + ('Boshqa summa' if self.get_lang(chat_id) == 'uz' else ('Другая сумма' if self.get_lang(chat_id) == 'ru' else 'Other amount')),
                  'callback_data': 'calc_start'}]
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
                [{'text': "⬅️ Boshlang'ich to'lovni o'zgartirish" if self.get_lang(chat_id) == 'uz' else '⬅️ Изменить первоначальный взнос',
                  'callback_data': f"calc_pr_{int(price)}"}]
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

        note_data = f"Kalkulyator: Narx={fmt_sum(price)}, Boshlang'ich={pct}% ({fmt_sum(down_sum)}), Muddat={period} oy, Oylik={fmt_sum(monthly)}"
        self.user_states[chat_id] = {'state': 'awaiting_contact', 'note': note_data}

        lang = self.get_lang(chat_id)
        btn_consult = '📞 Ushbu shartlarda ariza qoldirish' if lang == 'uz' else ('📞 Оставить заявку' if lang == 'ru' else '📞 Apply with these terms')
        btn_restart = '🔄 Qaytadan hisoblash' if lang == 'uz' else ('🔄 Рассчитать заново' if lang == 'ru' else '🔄 Recalculate')
        btn_apts = '🔑 Xonadonlarni ko\u2018rish' if lang == 'uz' else ('🔑 Смотреть квартиры' if lang == 'ru' else '🔑 View apartments')

        inline_kb = {
            'inline_keyboard': [
                [{'text': btn_consult, 'callback_data': 'req_consult'}],
                [{'text': btn_apts, 'callback_data': 'apts_menu'}],
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
            msg = "Sotuv ofislari ma'lumotlari tez orada joylashtiriladi." if lang == 'uz' else ("Информация скоро появится." if lang == 'ru' else "Sales office info coming soon.")
            self.send_message(chat_id, msg)
            return

        text = (
            "📍 <b>XON SAROY SOTUV OFISLARI:</b>\n\n"
            "Sizni qulay va shinam savdo ofislarimizda kutib qolamiz!\n"
            "🕒 <b>Ish vaqti:</b> Har kuni 09:00 dan 19:00 gacha dam olish kunlarisiz.\n\n"
            if lang == 'uz' else
            "📍 <b>ОФИСЫ ПРОДАЖ XON SAROY:</b>\n\n"
            "Будем рады видеть вас в наших офисах продаж!\n"
            "🕒 <b>Часы работы:</b> Ежедневно с 09:00 до 19:00 без выходных.\n\n"
            if lang == 'ru' else
            "📍 <b>XON SAROY SALES OFFICES:</b>\n\n"
            "We welcome you at our comfortable sales offices!\n"
            "🕒 <b>Working hours:</b> Every day 09:00 — 19:00, no days off.\n\n"
        )

        inline_buttons = []
        for idx, o in enumerate(offices, 1):
            text += f"🏢 <b>{idx}. {o.name}</b>\n📍 {o.address}\n\n"
            if o.latitude and o.longitude:
                btn_name = f"📍 {o.name}" + (" lokatsiyasi" if lang == 'uz' else (" локация" if lang == 'ru' else " location"))
                inline_buttons.append([{'text': btn_name, 'callback_data': f"office_loc_{o.id}"}])

        btn_consult = "📞 " + ("Ofisga qo'ng'iroq" if lang == 'uz' else ("Заказать звонок" if lang == 'ru' else "Request a call"))
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
            "Kompaniyamiz qurilishda jahon standartlariga mos, sertifikatlangan va laboratoriya nazoratidan o'tgan xomashyolardan foydalanadi:\n\n"
            "🏗 <b>Monolit karkas:</b> 9 ballik zilzilaga bardoshli poydevor va ustunlar.\n"
            "🧱 <b>Pishiq g'isht va gazoblok:</b> Ekologik toza, qishda issiq, yozda salqin saqlovchi energiya tejamkor devorlar.\n"
            "🪟 <b>Panoramik romlar:</b> Shovqin va changdan ishonchli himoyalovchi sifatli oynalar.\n"
            "🛗 <b>Tezyurar liftlar:</b> Shovqinsiz, xavfsiz va yuqori yuk ko'tarish quvvatiga ega liftlar.\n\n"
            if lang == 'uz' else
            "🧱 <b>СТАНДАРТЫ КАЧЕСТВА XON SAROY:</b>\n\n"
            "Все объекты строятся из сертифицированных материалов:\n\n"
            "🏗 <b>Монолитный каркас:</b> Сейсмостойкость до 9 баллов.\n"
            "🧱 <b>Жженый кирпич и газоблок:</b> Энергоэффективные стены.\n"
            "🪟 <b>Панорамные окна:</b> Высокая шумо- и теплоизоляция.\n"
            "🛗 <b>Бесшумные скоростные лифты:</b> Безопасность и надежность.\n\n"
            if lang == 'ru' else
            "🧱 <b>XON SAROY QUALITY STANDARDS:</b>\n\n"
            "All projects use certified, lab-tested materials:\n\n"
            "🏗 <b>Monolithic frame:</b> 9-point seismic resistance.\n"
            "🧱 <b>Premium brickwork:</b> Energy-efficient insulated walls.\n"
            "🪟 <b>Panoramic windows:</b> Superior noise & thermal insulation.\n"
            "🛗 <b>High-speed elevators:</b> Silent, safe, reliable.\n\n"
        )

        for idx, m in enumerate(materials, 1):
            text += f"• <b>{m.title}</b>\n"

        btn_consult = "📞 " + ("Sifat haqida maslahat" if lang == 'uz' else ("Консультация" if lang == 'ru' else "Quality consultation"))
        inline_kb = {'inline_keyboard': [[{'text': btn_consult, 'callback_data': 'req_consult'}]]}

        # Send material images as album if available
        mat_images = [m for m in materials if (m.image and os.path.exists(m.image.path)) or m.image_url]
        if mat_images:
            first = mat_images[0]
            img = first.image_url if first.image_url else first.image.path
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
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
            "Minglab oilalar Xon Saroy majmualarida o'z orzularidagi xonadonlarga ega bo'lishdi. "
            "Biz har bir mijozning ishonchini yuksak qadrlaymiz!\n\n"
            if lang == 'uz' else
            "⭐ <b>ОТЗЫВЫ НАШИХ КЛИЕНТОВ:</b>\n\n"
            "Тысячи семей уже выбрали Xon Saroy!\n\n"
            if lang == 'ru' else
            "⭐ <b>OUR HAPPY CLIENTS:</b>\n\n"
            "Thousands of families have chosen Xon Saroy!\n\n"
        )

        for c in clients:
            text += f"✨ <b>{c.name}</b> — Xon Saroy rezidenti\n"

        btn_consult = "📞 " + ("Xonadon xarid qilish" if lang == 'uz' else ("Подобрать квартиру" if lang == 'ru' else "Find an apartment"))
        inline_kb = {'inline_keyboard': [[{'text': btn_consult, 'callback_data': 'req_consult'}]]}

        # Send client images
        client_images = [c for c in clients if (c.image and os.path.exists(c.image.path)) or c.image_url]
        if client_images:
            first = client_images[0]
            img = first.image_url if first.image_url else first.image.path
            self.send_photo(chat_id, img, caption=text, reply_markup=inline_kb)
        else:
            self.send_message(chat_id, text, reply_markup=inline_kb)

    # -----------------------------------------------------------------------
    # HANDLERS: USER PROFILE
    # -----------------------------------------------------------------------
    def handle_profile(self, chat_id, from_user):
        bu = self.get_or_create_user(from_user)
        lang = self.get_lang(chat_id)
        name = html.escape(from_user.get('first_name', 'Foydalanuvchi'))
        username = f"@{from_user.get('username')}" if from_user.get('username') else ("Mavjud emas" if lang == 'uz' else ("Не указан" if lang == 'ru' else "Not set"))

        lang_names = {'uz': "O'zbekcha", 'ru': 'Русский', 'en': 'English'}
        lang_name = lang_names.get(lang, "O'zbekcha")

        web_user = User.objects.filter(telegram_id=str(chat_id)).first()
        if web_user:
            site_status = (
                f"🔗 <b>Veb-sayt hisobi:</b> Bog'langan ✅\n"
                f"👤 <b>Foydalanuvchi nomi:</b> <code>{web_user.username}</code>\n"
                f"📧 <b>Pochta:</b> {web_user.email or 'Kiritilmagan'}"
            )
        else:
            site_status = (
                "🔗 <b>Veb-sayt hisobi:</b> Hali bog'lanmagan ⚠️\n"
                "<i>Saytimiz profil sozlamalarida Telegram ID'ingizni kiritib, hisobingizni bog'lashingiz mumkin.</i>"
                if lang == 'uz' else
                "🔗 <b>Аккаунт на сайте:</b> Не привязан ⚠️\n"
                "<i>Укажите Telegram ID в профиле на сайте.</i>"
                if lang == 'ru' else
                "🔗 <b>Website account:</b> Not linked ⚠️\n"
                "<i>Enter your Telegram ID in website profile settings.</i>"
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
                [{'text': '🌐 ' + ('Saytdagi profilni ochish' if lang == 'uz' else ('Профиль на сайте' if lang == 'ru' else 'Website Profile')), 'url': site_url}],
                [{'text': '🌐 ' + ('Tilni o\u2018zgartirish' if lang == 'uz' else ('Сменить язык' if lang == 'ru' else 'Change Language')), 'callback_data': 'show_lang_modal'}]
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

        BotUser.objects.filter(telegram_id=str(chat_id)).update(phone=phone)

        state = self.user_states.get(chat_id, {})
        full_note = custom_note or state.get('note', '')

        lead = Lead.objects.create(
            name=name,
            phone=phone,
            telegram_id=str(chat_id),
            telegram_username=username,
            source=Lead.Source.TELEGRAM,
            note=full_note
        )

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
                f"👉 <a href='tg://user?id={chat_id}'>Mijoz bilan yozishish</a>"
            )
            self.send_message(self.admin_chat_id, admin_msg)

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
        apts_available = Apartment.objects.filter(is_active=True, availability='available').count()
        apts_reserved = Apartment.objects.filter(is_active=True, availability='reserved').count()

        text = (
            "📊 <b>XON SAROY ADMIN BOSHQARUV PANELI:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Bot foydalanuvchilari:</b> {bot_users_count} ta\n"
            f"📬 <b>Jami arizalar (Leads):</b> {leads_count} ta\n"
            f"🆕 <b>Yangi ko'rilmagan arizalar:</b> {new_leads_count} ta\n"
            f"🏗 <b>Loyihalar soni:</b> {homes_count} ta\n"
            f"🔑 <b>Faol xonadonlar:</b> {apts_count} ta\n"
            f"  🟢 Bo'sh: {apts_available} | 🟡 Bron: {apts_reserved}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Quyidagi buyruqlardan foydalanishingiz mumkin:\n"
            "• So'nggi arizalarni ko'rish\n"
            "• Barcha foydalanuvchilarga xabar yuborish (<code>/broadcast [matn]</code>)"
        )
        kb = {
            'inline_keyboard': [
                [{'text': '📬 So\u2018nggi 5 ta ariza', 'callback_data': 'admin_recent_leads'}],
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

        text = "📬 <b>SO'NGGI 5 TA ARIZA:</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
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

    def broadcast_message(self, chat_id, message):
        sent_count = 0
        failed_count = 0
        users = BotUser.objects.values_list('telegram_id', flat=True)
        for user_id in users:
            response = self.send_message(user_id, message)
            if response.get('ok'):
                sent_count += 1
            else:
                failed_count += 1
                logger.warning(
                    "Broadcast xabari yuborilmadi (chat_id=%s): %s",
                    user_id,
                    response.get('description', 'noma’lum xato'),
                )

        self.send_message(
            chat_id,
            f"✅ Xabar {sent_count} ta foydalanuvchiga yuborildi. "
            f"❌ {failed_count} ta foydalanuvchiga yuborilmadi.",
        )

    # -----------------------------------------------------------------------
    # CALLBACK DATA PARSER for apartment pages
    # -----------------------------------------------------------------------
    def _parse_aptpage_callback(self, data_val):
        """Parse aptpage_<filter>_p<page> callback data."""
        import re
        # aptpage_proj_<id>_rm_<n>_p<page>
        m = re.match(r'aptpage_proj_(\d+)_rm_(\d+)_p(\d+)', data_val)
        if m:
            return {
                'project_id': int(m.group(1)),
                'rooms': int(m.group(2)),
                'page': int(m.group(3)),
            }
        # aptpage_rm_<n>_p<page>
        m = re.match(r'aptpage_rm_(\d+)_p(\d+)', data_val)
        if m:
            return {'rooms': int(m.group(1)), 'page': int(m.group(2))}
        # aptpage_proj_<id>_p<page>
        m = re.match(r'aptpage_proj_(\d+)_p(\d+)', data_val)
        if m:
            return {'project_id': int(m.group(1)), 'page': int(m.group(2))}
        # aptpage_avail_<val>_p<page>
        m = re.match(r'aptpage_avail_(\w+)_p(\d+)', data_val)
        if m:
            return {'availability': m.group(1), 'page': int(m.group(2))}
        # aptpage_all_p<page>
        m = re.match(r'aptpage_all_p(\d+)', data_val)
        if m:
            return {'page': int(m.group(1))}
        return {'page': 1}

    def handle_update(self, update):
        import re

        message = update.get('message')
        callback_query = update.get('callback_query')
        if message:
            chat = message.get('chat')
            from_user = message.get('from', {})
        elif callback_query:
            callback_message = callback_query.get('message') or {}
            chat = callback_message.get('chat')
            from_user = callback_query.get('from', {})
        else:
            return

        if not chat:
            return

        chat_id = chat['id']
        bot_user = self.get_or_create_user(from_user)
        if bot_user.conversation_state:
            self.user_states[chat_id] = bot_user.conversation_state
        else:
            self.user_states.pop(chat_id, None)

        try:
            # 1. MESSAGE UPDATE
            if 'message' in update:
                msg = update['message']
                chat_id = msg['chat']['id']
                text = msg.get('text', '').strip()
                user = msg.get('from', {})

                self.get_or_create_user(user)

                # Contact sharing
                if 'contact' in msg:
                    contact = msg['contact']
                    phone = contact.get('phone_number')
                    self.process_lead(chat_id, user, phone, "Kontakt tugmasi orqali yuborildi")
                    return
                # Text command routing
                if text == '/start':
                    self.handle_start(chat_id, user)

                elif text in ('/lang', '🌐 Tilni o\u2018zgartirish', '🌐 Сменить язык', '🌐 Change Language'):
                    self.handle_lang_prompt(chat_id)

                elif text in ('🏢 Xon Saroy nima?', '🏢 О компании Xon Saroy', '🏢 About Xon Saroy', '/about'):
                    self.handle_about(chat_id)

                elif text in ('🏗 Loyihalarimiz', '🏗 Наши проекты', '🏗 Our Projects', '/projects'):
                    self.handle_projects(chat_id)

                elif text in ('🔑 Xonadonlar va Narxlar', '🔑 Квартиры и цены', '🔑 Apartments & Prices', '/apartments'):
                    self.handle_apartments_menu(chat_id)

                elif text in ('🧮 To\u2018lov kalkulyatori', '🧮 Калькулятор рассрочки', '🧮 Payment Calculator', '/calc'):
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

                elif text in ('🌐 Veb-saytga o\u2018tish', '🌐 Перейти на сайт', '🌐 Visit Website', '/website'):
                    site_url = f"{settings.SITE_URL}/"
                    lang = self.get_lang(chat_id)
                    label = '🌐 Xon Saroy veb-saytini ochish' if lang == 'uz' else ('🌐 Открыть сайт Xon Saroy' if lang == 'ru' else '🌐 Open Xon Saroy website')
                    kb = {'inline_keyboard': [[{'text': label, 'url': site_url}]]}
                    self.send_message(chat_id, "Xon Saroy rasmiy veb-saytiga tashrif buyuring:", reply_markup=kb)

                elif text in ('📊 Admin panel', '/admin'):
                    self.handle_admin_panel(chat_id)

                elif text.startswith('/broadcast') and str(chat_id) == self.admin_chat_id:
                    broadcast_msg = text.replace('/broadcast', '').strip()
                    if broadcast_msg:
                        self.broadcast_message(
                            chat_id,
                            f"📢 <b>XON SAROY YANGILIK:</b>\n\n{broadcast_msg}",
                        )
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
                        self.send_message(chat_id, "Iltimos, to'g'ri summa kiriting (masalan: 500000000):")

                elif self.user_states.get(chat_id, {}).get('state') == 'awaiting_contact':
                    self.process_lead(chat_id, user, text, self.user_states.get(chat_id, {}).get('note', "Qo'lda kiritilgan telefon/xabar"))

                elif self.user_states.get(chat_id, {}).get('state') == 'admin_broadcast_input' and str(chat_id) == self.admin_chat_id:
                    self.broadcast_message(chat_id, f"📢 <b>XON SAROY:</b>\n\n{text}")
                    del self.user_states[chat_id]

                else:
                    self.send_message(
                        chat_id,
                        "Iltimos, quyidagi menyu tugmalaridan birini tanlang yoki /start buyrug'ini bosing 👇",
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

                # Noop
                if data_val == 'noop':
                    return
                # Language selection
                elif data_val.startswith('set_lang_'):
                    lang_code = data_val.replace('set_lang_', '')
                    self.set_lang(chat_id, lang_code)
                    lang_titles = {'uz': "O'zbek tili tanlandi 🇺🇿", 'ru': 'Выбран русский язык 🇷🇺', 'en': 'English language selected 🇬🇧'}
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
                elif data_val == 'filter_proj_cat_all':
                    self.handle_projects(chat_id)
                elif data_val.startswith('filter_proj_cat_'):
                    cat_id = int(data_val.replace('filter_proj_cat_', ''))
                    self.handle_projects(chat_id, category_filter=cat_id)
                elif data_val.startswith('proj_'):
                    pid = int(data_val.replace('proj_', ''))
                    self.handle_project_detail(chat_id, pid)

                # Apartments from project detail — with optional room filter
                elif re.match(r'apts_proj_(\d+)_rm_(\d+)', data_val):
                    m = re.match(r'apts_proj_(\d+)_rm_(\d+)', data_val)
                    pid, rm = int(m.group(1)), int(m.group(2))
                    self.handle_apartments_list(chat_id, page=1, project_id=pid, rooms=rm)
                elif data_val.startswith('apts_proj_'):
                    pid = int(data_val.replace('apts_proj_', ''))
                    self.handle_apartments_list(chat_id, page=1, project_id=pid)
                elif data_val.startswith('lead_proj_'):
                    pid = int(data_val.replace('lead_proj_', ''))
                    h = Home.objects.filter(id=pid).first()
                    note = f"Qiziqqan loyihasi: {h.name}" if h else "Loyiha bo'yicha maslahat"
                    self.request_consultation_prompt(chat_id, note=note)

                # Apartments menu
                elif data_val == 'apts_menu':
                    self.handle_apartments_menu(chat_id)

                # Apartments filter by room + page
                elif re.match(r'apts_rm_(\d+)_p(\d+)', data_val):
                    m = re.match(r'apts_rm_(\d+)_p(\d+)', data_val)
                    rm, pg = int(m.group(1)), int(m.group(2))
                    self.handle_apartments_list(chat_id, page=pg, rooms=rm)

                # All apartments + page
                elif re.match(r'apts_all_p(\d+)', data_val):
                    m = re.match(r'apts_all_p(\d+)', data_val)
                    pg = int(m.group(1))
                    self.handle_apartments_list(chat_id, page=pg)

                # Availability filter
                elif re.match(r'apts_avail_(\w+)_p(\d+)', data_val):
                    m = re.match(r'apts_avail_(\w+)_p(\d+)', data_val)
                    avail, pg = m.group(1), int(m.group(2))
                    self.handle_apartments_list(chat_id, page=pg, availability=avail)

                # Apartment page navigation (aptpage_...)
                elif data_val.startswith('aptpage'):
                    params = self._parse_aptpage_callback(data_val)
                    self.handle_apartments_list(
                        chat_id,
                        page=params.get('page', 1),
                        rooms=params.get('rooms'),
                        project_id=params.get('project_id'),
                        availability=params.get('availability')
                    )

                # Legacy compatibility
                elif data_val == 'apts_rm_all':
                    self.handle_apartments_menu(chat_id)
                elif re.match(r'apts_rm_(\d+)$', data_val):
                    m = re.match(r'apts_rm_(\d+)$', data_val)
                    rm = int(m.group(1))
                    self.handle_apartments_list(chat_id, rooms=rm)

                # Apartment detail
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
                    if not a or a.availability != 'available':
                        self.send_message(chat_id, "Bu xonadon hozir bo'sh emas.")
                        return
                    p_name = a.project.name if (a and a.project) else "Xon Saroy"
                    note = f"Band qilish: {p_name}, {a.rooms}-xona, {a.area} m², {fmt_sum(a.price)} so'm" if a else "Xonadonni band qilish"
                    self.request_consultation_prompt(chat_id, note=note)

                # Calculator
                elif data_val == 'calc_start':
                    self.handle_calc_start(chat_id)
                elif data_val.startswith('calc_pr_'):
                    pr_val = data_val.replace('calc_pr_', '')
                    if pr_val == 'custom':
                        self.user_states[chat_id] = {'state': 'calc_custom_amount'}
                        self.send_message(chat_id, "Iltimos, xonadon narxini so'mda yozib yuboring (masalan: 450000000):")
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
                    self.send_message(chat_id, "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozib yuboring:")

        finally:
            state = self.user_states.get(chat_id) or {}
            BotUser.objects.filter(telegram_id=str(chat_id)).update(conversation_state=state)

    # -----------------------------------------------------------------------
    # POLLING LOOP
    # -----------------------------------------------------------------------
    def run_polling(self):
        import re
        logger.info("Telegram Bot ishga tushirildi! Polling boshlandi...")
        offset = 0
        retry_delay = 3

        while True:
            try:
                resp = requests.get(
                    f"{self.api_url}/getUpdates",
                    params={'offset': offset, 'timeout': 25},
                    timeout=35
                )
                resp.raise_for_status()
                data = resp.json()
                retry_delay = 3
                if not data.get('ok'):
                    if data.get('error_code') in (401, 409):
                        raise CommandError(
                            f"Telegram getUpdates xatosi: {data.get('description', 'token yoki polling muammosi')}"
                        )
                    logger.error("Telegram getUpdates xatosi: %s", data.get('description', "noma'lum xato"))
                    time.sleep(2)
                    continue

                for update in data.get('result', []):
                    offset = update['update_id'] + 1
                    self.handle_update(update)

            except CommandError:
                raise
            except requests.RequestException as err:
                logger.warning(
                    "Telegram polling so'rovi bajarilmadi (%s); %s soniyadan keyin qayta urinadi.",
                    type(err).__name__,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
            except Exception as err:
                logger.exception("Polling loop exception (%s).", type(err).__name__)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)


# ---------------------------------------------------------------------------
# DJANGO MANAGEMENT COMMAND
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = 'Xon Saroy Telegram Botini ishga tushirish'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            '--check',
            action='store_true',
            help='Telegram bot va webhook holatini tekshiradi.',
        )
        mode.add_argument(
            '--set-webhook',
            action='store_true',
            help='Telegram webhookini sayt manziliga sozlaydi.',
        )
        mode.add_argument(
            '--delete-webhook',
            action='store_true',
            help='Telegram webhookini o‘chirib, polling rejimiga qaytaradi.',
        )

    def handle(self, *args, **options):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '').strip()
        webhook_secret = os.getenv('TELEGRAM_WEBHOOK_SECRET', '').strip()

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
                f"Telegram webhook holatini tekshirib bo'lmadi: {webhook_info.get('description', 'API javob bermadi')}"
            )
        webhook_url = webhook_info.get('result', {}).get('url', '')

        username = bot_info.get('result', {}).get('username', "noma'lum")

        if options['set_webhook']:
            if not webhook_secret:
                raise CommandError(".env faylida TELEGRAM_WEBHOOK_SECRET sozlanmagan.")
            if (
                not webhook_secret.isascii()
                or not 1 <= len(webhook_secret) <= 256
                or any(not (char.isalnum() or char in '_-') for char in webhook_secret)
            ):
                raise CommandError(
                    "TELEGRAM_WEBHOOK_SECRET 1–256 ta lotin harfi, raqam, '_' yoki '-' dan iborat bo‘lsin."
                )
            site_url = urlparse(settings.SITE_URL)
            if site_url.scheme != 'https' or not site_url.netloc:
                raise CommandError("Telegram webhook uchun SITE_URL HTTPS manzil bo‘lishi kerak.")

            target_url = f"{settings.SITE_URL.rstrip('/')}/telegram/webhook/"
            response = bot.call_api('setWebhook', {
                'url': target_url,
                'secret_token': webhook_secret,
                'allowed_updates': json.dumps(['message', 'callback_query']),
            })
            if not response.get('ok'):
                raise CommandError(
                    f"Telegram webhook o‘rnatilmadi: {response.get('description', 'API javob bermadi')}"
                )
            self.stdout.write(self.style.SUCCESS(f"Bot @{username} webhookga ulandi: {target_url}"))
            return

        if options['delete_webhook']:
            response = bot.call_api('deleteWebhook')
            if not response.get('ok'):
                raise CommandError(
                    f"Telegram webhook o‘chirilmadi: {response.get('description', 'API javob bermadi')}"
                )
            self.stdout.write(self.style.SUCCESS(f"Bot @{username} webhooki o‘chirildi."))
            return

        status = f"Bot @{username} tokeni to'g'ri."
        if webhook_url:
            status += f" Webhook faol: {webhook_url}"
        else:
            status += " Webhook sozlanmagan; polling rejimi faol emas."
        if admin_chat_id:
            status += " Admin xabarlari yoqilgan."
        else:
            status += " TELEGRAM_ADMIN_CHAT_ID kiritilmagan; admin xabarlari yuborilmaydi."
        if options['check']:
            self.stdout.write(self.style.SUCCESS(status))
            return

        if webhook_url:
            raise CommandError(
                "Webhook faol. Telegram yangiliklari sayt orqali keladi; `runbot` polling jarayonini "
                "alohida ishga tushirmang."
            )

        self.stdout.write(self.style.SUCCESS(f"{status} Bot ishga tushmoqda..."))
        bot.run_polling()
