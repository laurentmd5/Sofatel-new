"""
Cache decorators for performance optimization with Redis

Provides reusable cache decorators that work with the Flask-Caching instance
"""

from functools import wraps
from extensions import cache
from flask import request
from flask_login import current_user


def cached_performance_route(timeout=300):
    """
    Cache decorator for performance/KPI routes
    
    Args:
        timeout: Cache TTL in seconds (default 5 min)
        
    Caches by: user_role + zone (if applicable) + period parameter
    Invalidates when: page parameter differs or user zone differs
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key based on user and request params
            user_id = current_user.id if current_user.is_authenticated else 'anon'
            user_role = current_user.role if current_user.is_authenticated else 'anon'
            user_zone = getattr(current_user, 'zone', None) if current_user.is_authenticated else None
            
            period = request.args.get('period', 'day')
            sort_by = request.args.get('sort', 'score')
            page = request.args.get('page', 1)
            
            cache_key = f"{f.__name__}:{user_id}:{user_role}:{user_zone}:{period}:{sort_by}:{page}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result
            result = f(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


def cache_kpi_data(timeout=300):
    """
    Decorator specifically for KPI data endpoints
    
    Respects:
    - User role (chef_pur, chef_zone, admin)
    - User zone (for zone-scoped chefs)
    - Period filter (day/week/month/year)
    - Sort parameter
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return f(*args, **kwargs)
            
            # Build cache key
            period = request.args.get('period', 'month')
            sort_by = request.args.get('sort', 'score')
            
            # Zone-aware caching
            zone_filter = None
            if current_user.role == 'chef_zone':
                zone_filter = current_user.zone
            
            cache_key = f"kpi_route:{current_user.id}:{zone_filter}:{period}:{sort_by}"
            
            # Try cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute
            result = f(*args, **kwargs)
            
            # Cache with 5 min default for KPI
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


def invalidate_performance_cache(zone=None):
    """
    Manually invalidate performance cache
    Useful when KPI data is recalculated
    
    Args:
        zone: Optional zone to invalidate (None = invalidate all)
    """
    try:
        if zone:
            # Invalidate cache for specific zone
            cache_key = f"perf_data:{zone}:*"
            # Note: Redis doesn't support wildcards in delete, so we'd need to iterate
            # For now, just invalidate the main keys
            for period in ['day', 'week', 'month']:
                for sort_by in ['score', 'taux', 'anomalie']:
                    key = f"perf_data:{zone}:{period}:{sort_by}"
                    cache.delete(key)
        else:
            # Invalidate all performance cache
            for zone_name in [None, 'Dakar', 'Mbour', 'Kaolack', 'Fatick']:
                for period in ['day', 'week', 'month']:
                    for sort_by in ['score', 'taux', 'anomalie']:
                        key = f"perf_data:{zone_name}:{period}:{sort_by}"
                        cache.delete(key)
        
        # Also invalidate KPI route caches (these are user-specific)
        # Note: Without Redis SCAN, we can't easily iterate user-specific keys
        # This is a limitation of simple cache - with Redis we could use SCAN
        
    except Exception as e:
        print(f"⚠️  Cache invalidation warning: {e}")
