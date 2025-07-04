import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import streams.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rtsp_viewer.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": 
        URLRouter(
            streams.routing.websocket_urlpatterns
        )
    ,
})