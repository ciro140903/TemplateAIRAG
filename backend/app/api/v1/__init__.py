"""
API v1 Routes
Portale Aziendale - Versione 1.0
"""

from . import auth_routes
from . import users
from . import chat
from . import admin
from . import health

__all__ = [
    "auth_routes",
    "users", 
    "chat",
    "admin",
    "health"
] 