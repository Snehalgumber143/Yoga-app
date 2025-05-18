from django.shortcuts import render,HttpResponse
def index(request):
    context = {
        "variable":"Snehal"
    }
    return render(request,"index.html",context)
    #return HttpResponse("this is my homepage")
def about(request):
    return HttpResponse("this is my about")
def services(request):
    return HttpResponse("this is my service page")
def contact(request):
    return HttpResponse("this is my contact page")
# Create your views here.
