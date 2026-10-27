"""
通用验证器

提供手机号、图片文件等常用验证逻辑。
"""
import re
import os
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    """验证中国大陆手机号格式
    
    Args:
        value: 手机号字符串
        
    Raises:
        ValidationError: 格式不正确时抛出
        
    Example:
        phone = models.CharField(validators=[validate_phone_number])
    """
    if not value:
        return
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('请输入正确的手机号码（11位数字，以1开头）')


def validate_image_size(image):
    """验证上传图片大小不超过 5MB
    
    Args:
        image: 上传的图片文件对象
        
    Raises:
        ValidationError: 文件过大时抛出
    """
    max_size = 5 * 1024 * 1024  # 5MB
    if image.size > max_size:
        raise ValidationError('图片大小不能超过 5MB')


def validate_image_extension(image):
    """验证图片文件扩展名
    
    仅允许 jpg, jpeg, png, webp 格式。
    
    Args:
        image: 上传的图片文件对象
        
    Raises:
        ValidationError: 格式不支持时抛出
    """
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'不支持的图片格式 "{ext}"，仅支持：jpg, jpeg, png, webp'
        )


def validate_image(image):
    """图片综合验证（大小 + 格式）
    
    组合调用大小和格式验证。
    
    Args:
        image: 上传的图片文件对象
        
    Raises:
        ValidationError: 验证不通过时抛出
    """
    validate_image_size(image)
    validate_image_extension(image)


def validate_positive_price(value):
    """验证价格为正数
    
    Args:
        value: 价格数值
        
    Raises:
        ValidationError: 价格非正数时抛出
    """
    if value is not None and value < 0:
        raise ValidationError('价格不能为负数')


def validate_rating(value):
    """验证评分在 1-5 之间
    
    Args:
        value: 评分数值
        
    Raises:
        ValidationError: 评分超出范围时抛出
    """
    if value is not None and (value < 1 or value > 5):
        raise ValidationError('评分必须在 1 到 5 之间')
