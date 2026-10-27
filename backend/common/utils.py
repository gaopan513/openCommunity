"""
工具函数

提供文件上传路径生成、时间格式化等通用工具。
"""
import os
import uuid
from datetime import datetime

from django.db import IntegrityError, transaction
from django.db.models import F


def generate_upload_path(instance, filename, folder='uploads'):
    """生成唯一的文件上传路径
    
    格式：media/{folder}/{YYYYMM}/{uuid}.{ext}
    避免文件名冲突和中文路径问题。
    
    Args:
        instance: 模型实例
        filename: 原始文件名
        folder: 存储子目录名
        
    Returns:
        str: 生成的相对路径
        
    Example:
        class ProductImage(models.Model):
            image = models.ImageField(
                upload_to=lambda inst, fn: generate_upload_path(inst, fn, 'products')
            )
    """
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        ext = '.jpg'
    
    # 按月份分目录，避免单目录文件过多
    date_dir = datetime.now().strftime('%Y%m')
    unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
    
    return os.path.join(folder, date_dir, unique_name)


def avatar_upload_path(instance, filename):
    """用户头像上传路径"""
    return generate_upload_path(instance, filename, 'avatars')


def merchant_upload_path(instance, filename):
    """商家图片上传路径"""
    return generate_upload_path(instance, filename, 'merchants')


def product_upload_path(instance, filename):
    """二手商品图片上传路径"""
    return generate_upload_path(instance, filename, 'products')


def post_upload_path(instance, filename):
    """帖子图片上传路径"""
    return generate_upload_path(instance, filename, 'posts')


def activity_upload_path(instance, filename):
    """活动图片上传路径"""
    return generate_upload_path(instance, filename, 'activities')


def merchant_logo_upload_path(instance, filename):
    """商家 Logo 上传路径"""
    return generate_upload_path(instance, filename, 'merchant_logos')


def housekeeping_upload_path(instance, filename):
    """家政服务图片上传路径"""
    return generate_upload_path(instance, filename, 'housekeeping')


def format_datetime(dt):
    """格式化日期时间为可读字符串
    
    Args:
        dt: datetime 对象
        
    Returns:
        str: 格式化后的字符串，如 "2026-07-27 14:30"
    """
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M')


def calculate_average_rating(ratings):
    """计算平均评分
    
    Args:
        ratings: 评分列表（如 [5, 4, 3, 5]）
        
    Returns:
        float: 平均分（保留一位小数），无评分时返回 0.0
        
    Example:
        >>> calculate_average_rating([5, 4, 3])
        4.0
    """
    if not ratings:
        return 0.0
    return round(sum(ratings) / len(ratings), 1)


def toggle_like(like_model, target, user, rel_field):
    """原子化切换「用户对目标对象」的点赞状态

    统一收敛帖子/问题/回答三个点赞端点的并发处理，返回最新状态供视图组装响应。

    并发语义：
    - 未点赞：在事务内创建点赞记录并 like_count + 1；
      若唯一约束冲突（双击/并发首赞，另一请求已抢先创建），本次幂等返回「已赞」，
      不重复计数（不能用 get_or_create：它内部吞掉 IntegrityError 并返回 created=False，
      会把并发首赞误判为取消点赞而删掉对方刚建的记录）。
    - 已点赞：仅当本请求真正删除了记录时才 like_count - 1，
      避免两个并发取消请求重复减计数；like_count__gt=0 兜底防止跌穿 0。

    Args:
        like_model: 点赞模型类（如 PostLike / QuestionLike / AnswerLike）
        target: 被点赞对象实例（需带 like_count 字段）
        user: 发起点赞的用户
        rel_field: 点赞模型指向目标对象的外键字段名（如 'post' / 'question' / 'answer'）

    Returns:
        tuple[bool, int]: (当前是否处于已赞状态, 最新点赞数)
    """
    target_model = type(target)
    existing = like_model.objects.filter(**{rel_field: target, 'user': user}).first()

    if existing is None:
        try:
            # 建记录与计数 +1 必须同事务，任一失败整体回滚，避免计数与点赞表脱节
            with transaction.atomic():
                like_model.objects.create(**{rel_field: target, 'user': user})
                target_model.objects.filter(pk=target.pk).update(
                    like_count=F('like_count') + 1
                )
        except IntegrityError:
            # 并发请求已完成首赞（唯一约束冲突）：事务已随 with 块回滚，
            # 此处幂等返回已赞状态，计数以抢先提交的请求为准
            target.refresh_from_db()
            return True, target.like_count
        target.refresh_from_db()
        return True, target.like_count

    with transaction.atomic():
        # delete() 返回实际删除条数；并发取消时败方删除 0 条，不得再减计数
        deleted, _ = existing.delete()
        if deleted:
            target_model.objects.filter(pk=target.pk, like_count__gt=0).update(
                like_count=F('like_count') - 1
            )
    target.refresh_from_db()
    return False, target.like_count
