from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

progressmsg = "start searching"
percent = 0

@csrf_exempt
def progress(request):
    global progressmsg, percent
    percent = int(request.GET.get("progress"))
    print("get percent", percent)
    if progressmsg == "done":
        percent = 100
    elif percent < 90:
        percent += 10
    return JsonResponse({"msg": progressmsg, "percent": percent}, safe=False)

# call back function for progress bar
def progressCallback(msg):
    global progressmsg
    progressmsg = msg
    print("progressCallback", progressmsg)
