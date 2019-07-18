import os, sys, json, pandas, string, math, copy
import multiprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

def vast19(request):
    return render(request, "vast/vast19.html")
