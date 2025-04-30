from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/game/position/$', consumers.PositionConsumer.as_asgi()),
    re_path(r'^ws/game/bullets/$', consumers.BulletConsumer.as_asgi()),
    re_path(r'^ws/game/state/$', consumers.GameStateConsumer.as_asgi()),
]


