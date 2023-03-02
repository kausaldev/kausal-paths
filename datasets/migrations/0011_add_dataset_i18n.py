# Generated by Django 3.2.18 on 2023-02-27 18:09

from django.db import migrations
import django.db.models.deletion
import modelcluster.fields
import modeltrans.fields


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0010_alter_datasetdimensionselectedcategory_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('name',), required_languages=(), virtual_fields=True),
        ),
        migrations.AlterField(
            model_name='dimensioncategory',
            name='dimension',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='datasets.dimension'),
        ),
    ]
