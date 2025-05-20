from django.shortcuts import render,HttpResponse
def index(request):
    context = {
        "variable":"Snehal"
    }
    return render(request,"index.html",context)
    #return HttpResponse("this is my homepage")
def about(request):
    return render(request,"about.html")
def contact(request):
   return render(request,"contact.html")
def services(request):
    return HttpResponse("this is my contact page")
# Create your views here.
