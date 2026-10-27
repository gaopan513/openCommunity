"""
初始化商品分类预设数据
"""
from django.db import migrations


def seed_categories(apps, schema_editor):
    ProductCategory = apps.get_model('secondhand', 'ProductCategory')
    categories = [
        {'name': '家具家电', 'slug': 'furniture-appliances', 'sort_order': 1},
        {'name': '数码电子', 'slug': 'digital-electronics', 'sort_order': 2},
        {'name': '服饰鞋包', 'slug': 'clothing-bags', 'sort_order': 3},
        {'name': '母婴用品', 'slug': 'maternity-baby', 'sort_order': 4},
        {'name': '图书文具', 'slug': 'books-stationery', 'sort_order': 5},
        {'name': '运动户外', 'slug': 'sports-outdoor', 'sort_order': 6},
        {'name': '美妆护肤', 'slug': 'beauty-skincare', 'sort_order': 7},
        {'name': '食品生鲜', 'slug': 'food-fresh', 'sort_order': 8},
        {'name': '其他', 'slug': 'other', 'sort_order': 99},
    ]
    for cat in categories:
        ProductCategory.objects.get_or_create(slug=cat['slug'], defaults=cat)


def reverse_categories(apps, schema_editor):
    ProductCategory = apps.get_model('secondhand', 'ProductCategory')
    slugs = [
        'furniture-appliances', 'digital-electronics', 'clothing-bags',
        'maternity-baby', 'books-stationery', 'sports-outdoor',
        'beauty-skincare', 'food-fresh', 'other',
    ]
    ProductCategory.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('secondhand', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_categories),
    ]
