from django.contrib.auth.hashers import make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def hash_existing_reset_codes(apps, schema_editor):
    reset_code_model = apps.get_model('app', 'PasswordResetCode')
    for reset_code in reset_code_model.objects.all().iterator():
        reset_code.code = make_password(reset_code.code)
        reset_code.save(update_fields=['code'])


def invalidate_reset_codes(apps, schema_editor):
    reset_code_model = apps.get_model('app', 'PasswordResetCode')
    reset_code_model.objects.all().update(code='000000', is_used=True)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_home_coordinates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='home',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-90), MaxValueValidator(90)],
                verbose_name='Loyiha kengligi',
            ),
        ),
        migrations.AlterField(
            model_name='home',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-180), MaxValueValidator(180)],
                verbose_name='Loyiha uzunligi',
            ),
        ),
        migrations.AlterField(
            model_name='salesoffice',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-90), MaxValueValidator(90)],
                verbose_name='Kenglik',
            ),
        ),
        migrations.AlterField(
            model_name='salesoffice',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-180), MaxValueValidator(180)],
                verbose_name='Uzunlik',
            ),
        ),
        migrations.AlterField(
            model_name='passwordresetcode',
            name='code',
            field=models.CharField(max_length=128, verbose_name='Tasdiqlash kodi xeshi'),
        ),
        migrations.RunPython(hash_existing_reset_codes, invalidate_reset_codes),
    ]
