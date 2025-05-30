from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from datetime import datetime
from home.models import Student
from home.models import Contact
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
def index(request):
    student_name = request.session.get('student_name', 'Guest')

    context = {
        "variable": student_name
    }

    return render(request, "index.html", context)
def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        gender = request.POST.get('gender', '')
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')

        # Validate required fields
        if not (name and email and password):
            messages.error(request, "Name, email and password are required.")
            return redirect('signup')

        # Convert numeric values safely
        try:
            age = int(age)
            height = float(height)
            weight = float(weight)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid age, height, and weight.")
            return redirect('signup')

        # Check if email already exists
        if Student.objects.using('mysql_db').filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        try:
            hashed_password = make_password(password)
            # Save the student to MySQL database
            Student.objects.using('mysql_db').create(
                name=name,
                email=email,
                password=hashed_password,
                gender=gender,
                age=age,
                height=height,
                weight=weight
            )
            print(f"Saving: {name}, {email}, {password}, {gender}, {age}, {height}, {weight}")
            messages.success(request, "Signup successful!")
            return redirect('logins')
        except Exception as e:
            messages.error(request, f"Error saving data: {str(e)}")
            return redirect('signup')

    return render(request, 'signup.html')

def logins(request):
    if request.method == 'POST':
        email = request.POST['email'].strip().lower()
        password = request.POST['password']

        try:
            
            student = Student.objects.using('mysql_db').get(email__iexact=email)
            if check_password(password, student.password):
                request.session['student_name'] = student.name
                request.session['student_id'] = student.id
                request.session['student_email'] = student.email
                return redirect('home')
            else:
                messages.error(request, "Invalid password.")
        except Student.DoesNotExist:
            messages.error(request, "Email not found.")
        
        return redirect('logins')

    # For GET requests, just render the login page
    return render(request, 'logins.html')

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
    student_name = request.session.get('student_name', 'Guest')
    student_email = request.session.get('student_email', 'Guest')  
    context = {
        "student_name": student_name,
        "student_email": student_email
    }

    return render(request,"attendance.html",context)
def video(request):
        room_name = 'ZenFlowYogaRoom123' 
        context = {
        'room_name': room_name,
    }
        return render(request,"meet.html",context)
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_portal(request):
    students = Student.objects.all().order_by('-created_at')
    return render(request, 'admin_portal.html', {'students': students})
def delete_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        messages.success(request, f"Student '{student.name}' has been deleted.")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('admin_portal')
# Create your views here.
