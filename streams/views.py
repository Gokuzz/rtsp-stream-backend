from django.http import HttpResponse,JsonResponse
import logging



logger = logging.getLogger(__name__)



def index(request):
    return HttpResponse("RTSP Stream Viewer Home")



def ping_view(request):
    print('**************')
    return JsonResponse({'message': 'pong from Django!'})