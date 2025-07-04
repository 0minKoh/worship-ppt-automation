# Generated by Django 5.2.3 on 2025-06-24 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_worshipinfo_worship_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="worshipinfo",
            name="ads_manager",
            field=models.CharField(max_length=100, verbose_name="광고 담당자"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="benediction_minister",
            field=models.CharField(max_length=100, verbose_name="축도자"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="offering_minister",
            field=models.CharField(max_length=100, verbose_name="봉헌자"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="prayer_minister",
            field=models.CharField(max_length=100, verbose_name="기도자"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="sermon_scripture",
            field=models.CharField(max_length=255, verbose_name="설교 본문 범위"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="sermon_title",
            field=models.CharField(max_length=200, verbose_name="설교 제목"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="speaker",
            field=models.CharField(max_length=100, verbose_name="설교자"),
        ),
        migrations.AlterField(
            model_name="worshipinfo",
            name="worship_announcements",
            field=models.JSONField(default=list, verbose_name="광고 목록"),
        ),
    ]
