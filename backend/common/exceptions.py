"""
自定义异常与全局异常处理器

提供业务异常基类和统一的异常响应格式。
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessError(APIException):
    """业务逻辑异常基类
    
    用于抛出可预期的业务错误，如"商家名称已存在"、"库存不足"等。
    
    Usage:
        raise BusinessError('商家名称已存在', code=40001)
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '业务处理失败'
    default_code = 'business_error'
    
    def __init__(self, detail=None, code=None, status_code=None):
        """初始化业务异常
        
        Args:
            detail: 错误描述信息
            code: 业务错误码（如 40001）
            status_code: HTTP 状态码（默认 400）
        """
        if status_code is not None:
            self.status_code = status_code
        if detail is not None:
            self.detail = detail
        else:
            self.detail = self.default_detail
        if code is not None:
            self.code = code


class NotFoundError(BusinessError):
    """资源不存在异常"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '请求的资源不存在'
    default_code = 'not_found'


class ForbiddenError(BusinessError):
    """权限不足异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '权限不足，无法执行此操作'
    default_code = 'forbidden'


class StatusTransitionError(BusinessError):
    """状态流转异常
    
    用于状态机中不合法的状态转换，如"已售出的商品不能再编辑"。
    """
    default_detail = '当前状态不允许此操作'
    default_code = 'invalid_status_transition'


def custom_exception_handler(exc, context):
    """全局异常处理器

    将所有异常统一转换为标准响应格式：
    {
        "code": <错误码>,
        "message": <错误信息>,
        "data": null
    }

    Args:
        exc: 异常实例
        context: 异常上下文（包含 view, request 等）

    Returns:
        Response: 统一格式的响应对象
    """
    # 先调用 DRF 默认处理器
    response = exception_handler(exc, context)

    if response is not None:
        # 提取错误信息
        if isinstance(response.data, dict):
            detail = response.data.get('detail', '')
            if not detail:
                # 字段级错误，拼接所有字段错误
                errors = []
                for field, messages in response.data.items():
                    if isinstance(messages, list):
                        errors.append(f"{field}: {messages[0]}")
                    else:
                        errors.append(f"{field}: {messages}")
                detail = '; '.join(errors)
        elif isinstance(response.data, list):
            detail = response.data[0] if response.data else '请求参数错误'
        else:
            detail = str(response.data)

        # 获取业务错误码
        error_code = getattr(exc, 'code', response.status_code)
        if isinstance(error_code, str):
            error_code = response.status_code

        response.data = {
            'code': error_code,
            'message': str(detail),
            'data': None
        }
        return response

    # DRF 默认处理器未捕获的非 APIException 异常（如 DoesNotExist / TypeError / ValueError /
    # IntegrityError 等），在 DEBUG=False 下会被 Django 兜底为 500 HTML 页，破坏统一 JSON 响应格式。
    # 此处统一转换为 500 JSON 响应，避免前端因解析 HTML 而降级为"请求失败"提示。
    import logging
    logger = logging.getLogger(__name__)
    logger.exception('未捕获的异常: %s', exc)
    from rest_framework.response import Response
    return Response(
        data={
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        },
        status=500
    )
