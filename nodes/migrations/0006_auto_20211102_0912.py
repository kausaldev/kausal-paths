# Generated by Django 3.2.8 on 2021-11-02 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0005_auto_20211030_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instanceconfig',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='instancehostname',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='nodeconfig',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
