from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

progressmsg = "start searching"
percent = 0

@csrf_exempt
def progress(request):
    global progressmsg, percent
    return JsonResponse({"msg": progressmsg, "percent": percent})

def resetProgress():
    global progressmsg, percent
    percent = 0
    progressmsg = "start searching"

# call back function for progress bar
def progressCallback(progress, msg):
    global progressmsg, percent
    percent = progress
    progressmsg = msg
    print("progressCallback", percent, progressmsg)
