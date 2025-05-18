from django.http import HttpResponse,JsonResponse

def index(request):
    return HttpResponse("RTSP Stream Viewer Home")



def ping_view(request):
    return JsonResponse({'message': 'pong from Django!'})