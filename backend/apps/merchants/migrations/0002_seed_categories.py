"""
初始化商家分类预设数据
"""
from django.db import migrations


def seed_categories(apps, schema_editor):
    MerchantCategory = apps.get_model('merchants', 'MerchantCategory')
    categories = [
        {'name': '餐饮美食', 'slug': 'food', 'icon': '🍜', 'sort_order': 1},
        {'name': '生鲜超市', 'slug': 'grocery', 'icon': '🛒', 'sort_order': 2},
        {'name': '家政服务', 'slug': 'housekeeping', 'icon': '🧹', 'sort_order': 3},
        {'name': '维修安装', 'slug': 'repair', 'icon': '🔧', 'sort_order': 4},
        {'name': '教育培训', 'slug': 'education', 'icon': '📚', 'sort_order': 5},
        {'name': '美容美发', 'slug': 'beauty', 'icon': '💇', 'sort_order': 6},
        {'name': '医疗健康', 'slug': 'health', 'icon': '🏥', 'sort_order': 7},
        {'name': '宠物服务', 'slug': 'pet', 'icon': '🐾', 'sort_order': 8},
        {'name': '其他', 'slug': 'other', 'icon': '📦', 'sort_order': 99},
    ]
    for cat in categories:
        MerchantCategory.objects.get_or_create(slug=cat['slug'], defaults=cat)


def reverse_categories(apps, schema_editor):
    MerchantCategory = apps.get_model('merchants', 'MerchantCategory')
    slugs = [
        'food', 'grocery', 'housekeeping', 'repair', 'education',
        'beauty', 'health', 'pet', 'other',
    ]
    MerchantCategory.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('merchants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_categories),
    ]
