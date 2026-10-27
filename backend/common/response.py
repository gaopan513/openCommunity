"""
统一响应格式封装

提供成功和失败响应的标准构造方法。
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message='success', http_status=status.HTTP_200_OK):
    """构造成功响应
    
    Args:
        data: 响应数据（字典、列表或 None）
        message: 成功提示信息
        http_status: HTTP 状态码（默认 200）
        
    Returns:
        Response: 标准格式响应
        
    Example:
        return success_response({'user_id': 1}, '注册成功', 201)
    """
    return Response(
        data={
            'code': 0,
            'message': message,
            'data': data
        },
        status=http_status
    )


def list_response(results, total, page, page_size, message='success'):
    """构造列表分页响应
    
    Args:
        results: 当前页数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页条数
        message: 提示信息
        
    Returns:
        Response: 带分页信息的标准响应
        
    Example:
        return list_response(serializer.data, 100, 1, 20)
    """
    return Response(
        data={
            'code': 0,
            'message': message,
            'data': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'results': results
            }
        },
        status=status.HTTP_200_OK
    )


def error_response(message='操作失败', code=40000, http_status=status.HTTP_400_BAD_REQUEST, data=None):
    """构造错误响应
    
    Args:
        message: 错误描述信息
        code: 业务错误码
        http_status: HTTP 状态码
        data: 附加错误数据（如字段级错误详情）
        
    Returns:
        Response: 标准错误响应
        
    Example:
        return error_response('用户名已存在', code=40001)
    """
    return Response(
        data={
            'code': code,
            'message': message,
            'data': data
        },
        status=http_status
    )


def created_response(data=None, message='创建成功'):
    """构造创建成功响应（201）
    
    Args:
        data: 创建的资源数据
        message: 提示信息
        
    Returns:
        Response: 201 状态码响应
    """
    return success_response(data, message, status.HTTP_201_CREATED)


def no_content_response(message='操作成功'):
    """构造无内容响应（204）
    
    用于删除操作等无需返回数据的场景。
    
    Args:
        message: 提示信息
        
    Returns:
        Response: 204 状态码响应
    """
    return Response(
        data={
            'code': 0,
            'message': message,
            'data': None
        },
        status=status.HTTP_204_NO_CONTENT
    )
