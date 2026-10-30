import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')
django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    print("Xon Saroy Telegram Bot ishga tushmoqda...")
    call_command('runbot')
