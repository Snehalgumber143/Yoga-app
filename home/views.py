from django.shortcuts import redirect, render,HttpResponse
from datetime import datetime
from home.models import Contact
from django.contrib import messages
def index(request):
    context = {
        "variable":"Snehal"
    }

    return render(request,"index.html",context)
def logins(request):
     return render(request,"logins.html")
def signup(request):
     return render(request,"signup.html")
def about(request):
    return render(request,"about.html")
def contact(request):
   if request.method == "POST":
       name = request.POST.get('name')
       email = request.POST.get('email')
       description = request.POST.get('description')
       contact = Contact(name=name, email = email, description=description, date = datetime.today())
       contact.save()
       messages.success(request, "Your feedback is stored with us it,in case of any query we'll get back to you shortly😊")
      
   return render(request,"contact.html")
def services(request):
    return HttpResponse("this is my contact page")
def video(request):
        room_name = 'ZenFlowYogaRoom123' 
        context = {
        'room_name': room_name,
    }
        return render(request,"meet.html",context)
# Create your views here.
