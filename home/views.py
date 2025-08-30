import json
from datetime import date
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from datetime import datetime
import json
import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from home.models import Student,Attendance
from django.views.decorators.http import require_POST
from home.models import Contact
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.db import transaction
from django.utils.timezone import now, localdate
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from django.contrib.auth.decorators import login_required, user_passes_test
def index(request):
    student_name = request.session.get('student_name', 'Guest')

    context = {
        "variable": student_name
    }

    return render(request, "index.html", context)
@csrf_exempt
def save_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attendance_data = data.get('attendance_data', [])

            saved_records = []

            for entry in attendance_data:
                student_id = entry.get('student_id')
                date = entry.get('date')
                class_type = entry.get('class_type')
                instructor = entry.get('instructor')
                status = entry.get('status')  # 'present' or 'absent'

                # Convert status to boolean
                is_present = True if status == 'present' else False

                Attendance.objects.using('mysql_db').update_or_create(
                    student_id=student_id,
                    date=date,
                    defaults={
                        'class_type': class_type,
                        'instructor': instructor,
                        'is_present': is_present
                    }
                )

                student = Student.objects.using('mysql_db').get(id=student_id)
                saved_records.append({
                    'student_id': student.id,
                    'name': student.name,
                    'email': student.email,
                    'date': date,
                    'is_present': is_present,
                    'class_type': class_type,
                    'instructor': instructor,
                })

            return JsonResponse({'success': True, 'saved_attendance': saved_records})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Invalid request method'})
def get_students(request):
    students = Student.objects.using('mysql_db').all()
    data = [
        {"id": s.id, "name": s.name, "email": s.email}  # adapt fields to your Student model
        for s in students
    ]
    return JsonResponse(data, safe=False)
def get_logged_in_students(request):
    """
    Return students who logged in (attendance marked) today.
    """
    today = localdate()  # today's date

    logged_in = Attendance.objects.using('mysql_db').filter(
        date=today, status="Present"   # adjust field names as per your model
    ).select_related('student')

    data = [
        {"id": a.student.id, "name": a.student.name, "email": a.student.email}
        for a in logged_in
    ]
    return JsonResponse(data, safe=False)
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
def export_attendance(request):
    """
    Export attendance records as a CSV file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Student', 'Date', 'Status'])  # adjust fields

    attendances = Attendance.objects.using('mysql_db').all().select_related('student')

    for record in attendances:
        writer.writerow([
            record.id,
            record.student.name,   # adjust field
            record.date,
            record.status
        ])

    return response
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
    student_email = request.session.get('student_email', 'guest@example.com')
    student_id = request.session.get('student_id')

    attendance_records = []
    if student_id:
        attendance_records = Attendance.objects.using('mysql_db').filter(student_id=student_id).order_by('-date')


    context = {
        "student_name": student_name,
        "student_email": student_email,
        "attendance_records": attendance_records
    }

    return render(request, "attendance.html", context)
def video(request):
        room_name = 'ZenFlowYogaRoom123' 
        context = {
        'room_name': room_name,
    }
        return render(request,"meet.html",context)
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_portal(request):
    students = Student.objects.using('mysql_db').all()
    student_id = request.GET.get('student_id')
    student = None
    attendance_map = {}
    attendance_records = []
    if student_id:
        student = get_object_or_404(Student.objects.using('mysql_db'), id=student_id)
        attendance_records = Attendance.objects.using('mysql_db').filter(student=student)

        # Build attendance_map with date -> 'present' or 'absent'
        for record in attendance_records:
            date_str = record.date.strftime('%Y-%m-%d')
            attendance_map[date_str] = 'present' if record.is_present else 'absent'

    return render(request, 'admin_portal.html', {
        'students': students,
        'student': student,
        'attendance_map': attendance_map,
        'attendance_records': attendance_records
    })

@csrf_exempt
def delete_attendance(request, id):
    try:
        record = get_object_or_404(Attendance.objects.using('mysql_db'), id=id)
        record.delete()
        return JsonResponse({"success": True, "message": "Attendance deleted"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def attendance_data_api(request):
    student_id = request.session.get("student_id")

    if not student_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    # Use MySQL DB
    records = Attendance.objects.using("mysql_db").filter(student_id=student_id).order_by("date")

    total_days = records.count()
    present_days = records.filter(is_present=True).count()
    absent_days = records.filter(is_present=False).count()
    attendance_rate = round((present_days / total_days) * 100, 2) if total_days else 0

    # Monthly counts
    monthly_counts = (
        records.annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(present=Count("id", filter=Q(is_present=True)))
        .order_by("month")
    )
    monthly = [m["present"] for m in monthly_counts]

    # Daily array (0 = absent, 1 = present)
    daily = [1 if r.is_present else 0 for r in records]

    return JsonResponse({
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_rate": attendance_rate,
        "monthly": monthly,
        "daily": daily,
    })