from django.shortcuts import redirect, render,HttpResponse
from datetime import datetime
from home.models import Student
from home.models import Contact
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
def index(request):
    student_name = request.session.get('student_name', 'Guest')

    context = {
        "variable": student_name
    }

    return render(request, "index.html", context)
def logins(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            student = Student.objects.get(email=email)
            if check_password(password, student.password):  # Use hash checker
                # Store name and ID in session
                request.session['student_name'] = student.name
                request.session['student_id'] = student.id
                return redirect('index')
            else:
                messages.error(request, "Invalid password.")
        except Student.DoesNotExist:
            messages.error(request, "Email not found.")
        
        return redirect('logins')

    return render(request, 'logins.html')
def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        height = request.POST['height']
        weight = request.POST['weight']
        age = request.POST['age']
        gender = request.POST['gender']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if Student.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        student = Student(
            name=name,
            email=email,
            height=height,
            weight=weight,
            age=age,
            gender=gender,
            password=make_password(password)  # Hash password
        )
        student.save()
        messages.success(request, "Signup successful! Please login.")
        return redirect('logins.html')
    
    return render(request, 'signup.html')
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
def admin_portal(request):
    students = Student.objects.all()
    students = Student.objects.all().order_by('-created_at')
    return render(request, 'admin_portal.html', {'students': students})
Student.objects.using('mysql_db').create(
    name='Alice',
    email='alice@example.com',
    password=make_password('test1234'),
    height=160,
    weight=55,
    age=20,
    gender='Female'
)
# Create your views here.
