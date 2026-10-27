"""
统一分页器配置

提供标准的分页参数和响应格式。
"""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """标准分页器
    
    默认每页 20 条，支持客户端通过 page_size 参数调整（最大 100）。
    
    响应格式：
    {
        "code": 0,
        "message": "success",
        "data": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "results": [...]
        }
    }
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class SmallPagination(PageNumberPagination):
    """小分页器
    
    用于评论、留言等数量较少的场景，默认每页 10 条。
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'
