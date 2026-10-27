"""
自定义 DRF 权限类

提供基于角色的访问控制权限：
- IsOwnerOrReadOnly: 对象所有者可编辑，其他人只读
- IsAdminUser: 仅管理员可访问
- IsMerchantUser: 仅商家角色可访问
- IsAuthenticatedOrCreate: 已认证用户可创建，其他人只读
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """对象所有者或只读权限
    
    允许对象的所有者进行编辑操作，其他用户仅允许读取。
    需要视图提供 get_object() 方法返回带有 user/author/seller 属性的对象。
    """
    
    # 所有者字段名列表，按优先级查找
    owner_fields = ('user', 'author', 'seller', 'owner')
    
    def has_object_permission(self, request, view, obj):
        """检查对象级权限
        
        Args:
            request: DRF 请求对象
            view: 视图实例
            obj: 目标对象
            
        Returns:
            bool: 是否有权限
        """
        # 安全方法（GET, HEAD, OPTIONS）始终允许
        if request.method in SAFE_METHODS:
            return True
        
        # 检查是否为对象所有者
        for field in self.owner_fields:
            owner = getattr(obj, field, None)
            if owner is not None:
                return owner == request.user
        
        return False


class IsAdminUser(BasePermission):
    """管理员权限
    
    仅允许 role='admin' 的用户访问。
    """
    message = '需要管理员权限。'
    
    def has_permission(self, request, view):
        """检查请求级权限
        
        Args:
            request: DRF 请求对象
            view: 视图实例
            
        Returns:
            bool: 是否为管理员
        """
        return (
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, 'role', None) == 'admin'
        )


class IsMerchantUser(BasePermission):
    """商家角色权限
    
    仅允许 role='merchant' 的用户访问。
    """
    message = '需要商家权限。'
    
    def has_permission(self, request, view):
        """检查请求级权限
        
        Args:
            request: DRF 请求对象
            view: 视图实例
            
        Returns:
            bool: 是否为商家角色
        """
        return (
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, 'role', None) == 'merchant'
        )


class IsAuthenticatedOrCreate(BasePermission):
    """已认证可创建，其他人只读
    
    未认证用户仅允许 GET 请求，已认证用户允许所有操作。
    """
    
    def has_permission(self, request, view):
        """检查请求级权限
        
        Args:
            request: DRF 请求对象
            view: 视图实例
            
        Returns:
            bool: 是否有权限
        """
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(BasePermission):
    """对象所有者或管理员权限
    
    允许对象所有者或管理员进行编辑操作。
    """
    
    owner_fields = ('user', 'author', 'seller', 'owner')
    
    def has_object_permission(self, request, view, obj):
        """检查对象级权限
        
        Args:
            request: DRF 请求对象
            view: 视图实例
            obj: 目标对象
            
        Returns:
            bool: 是否有权限
        """
        if request.method in SAFE_METHODS:
            return True
        
        # 管理员始终有权限
        if getattr(request.user, 'role', None) == 'admin':
            return True
        
        # 检查是否为对象所有者
        for field in self.owner_fields:
            owner = getattr(obj, field, None)
            if owner is not None:
                return owner == request.user
        
        return False
