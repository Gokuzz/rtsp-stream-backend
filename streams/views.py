
from django.http import HttpResponse

def index(request):
    return HttpResponse("RTSP Stream Viewer Home")