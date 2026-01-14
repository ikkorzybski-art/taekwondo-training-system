from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0008_userquizanswer'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='max_group',
            field=models.CharField(
                default='black',
                max_length=20,
                choices=[
                    ('white', 'Grupa Biały pas (10-9 kup)'),
                    ('yellow', 'Grupa Żółty pas (8-7 kup)'),
                    ('green', 'Grupa Zielony pas (6-5 kup)'),
                    ('blue', 'Grupa Niebieski pas (4-3 kup)'),
                    ('red', 'Grupa Czerwony pas (2-1 kup)'),
                    ('black', 'Grupa Czarny pas (Dan)'),
                ],
                verbose_name='Maksymalna grupa',
            ),
        ),
    ]
