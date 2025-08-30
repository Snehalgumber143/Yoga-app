import json
import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils.timezone import now, localdate
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from home.models import Student, Attendance, Contact


def index(request):
    student_name = request.session.get('student_name', 'Guest')
    context = {"variable": student_name}
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

        if not (name and email and password):
            messages.error(request, "Name, email and password are required.")
            return redirect('signup')

        try:
            age = int(age)
            height = float(height)
            weight = float(weight)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid age, height, and weight.")
            return redirect('signup')

        if Student.objects.using('mysql_db').filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        try:
            hashed_password = make_password(password)
            Student.objects.using('mysql_db').create(
                name=name,
                email=email,
                password=hashed_password,
                gender=gender,
                age=age,
                height=height,
                weight=weight
            )
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

    return render(request, 'logins.html')


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        description = request.POST.get('description')
        contact = Contact(name=name, email=email, description=description, date=datetime.today())
        contact.save()
        messages.success(request, "Your feedback is stored; we'll get back to you shortly 😊")
    return render(request, "contact.html")


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
    context = {'room_name': room_name}
    return render(request, "meet.html", context)


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
def save_attendance(request):
    """
    Handles both:
    1. JSON POST requests with multiple attendance entries (API)
    2. Form POST requests (admin portal)
    """
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            attendance_data = data.get('attendance_data', [])
            saved_records = []

            for entry in attendance_data:
                student_id = entry.get('student_id')
                date_str = entry.get('date')
                class_type = entry.get('class_type', 'Yoga')
                instructor = entry.get('instructor', 'Admin')
                status = entry.get('status', 'absent')

                if not student_id or not date_str:
                    continue  # skip invalid entries

                student = Student.objects.using('mysql_db').get(id=student_id)
                is_present = status.lower() == 'present'

                Attendance.objects.using('mysql_db').update_or_create(
                    student_id=student.id,
                    date=date_str,
                    defaults={
                        'class_type': class_type,
                        'instructor': instructor,
                        'is_present': is_present
                    }
                )

                saved_records.append({
                    'student_id': student.id,
                    'name': student.name,
                    'email': student.email,
                    'date': date_str,
                    'is_present': is_present,
                    'class_type': class_type,
                    'instructor': instructor,
                })

            return JsonResponse({'success': True, 'saved_attendance': saved_records})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        try:
            student_id = request.POST.get("student_id")
            if not student_id:
                return JsonResponse({'success': False, 'error': 'Missing student_id'})

            is_present = request.POST.get("is_present") == "true"
            class_type = request.POST.get("class_type", "Yoga")
            instructor = request.POST.get("instructor", "Admin")

            date_str = request.POST.get("date")
            if date_str:
                date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                date_val = now().date()

            Attendance.objects.using('mysql_db').update_or_create(
                student_id=student_id,
                date=date_val,
                class_type=class_type,
                defaults={
                    "is_present": is_present,
                    "instructor": instructor,
                }
            )

            return redirect("admin_portal")

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def delete_attendance(request, id):
    try:
        record = get_object_or_404(Attendance.objects.using('mysql_db'), id=id)
        record.delete()
        return JsonResponse({"success": True, "message": "Attendance deleted"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_GET
def attendance_data_api(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return JsonResponse({"error": "Student not logged in"}, status=401)

    student = get_object_or_404(Student.objects.using('mysql_db'), id=student_id)
    attendance_records = Attendance.objects.using('mysql_db').filter(student=student)

    total_days = attendance_records.count()
    present_days = attendance_records.filter(is_present=True).count()
    absent_days = total_days - present_days
    attendance_rate = round((present_days / total_days) * 100, 2) if total_days else 0

    # Build monthly present counts
    monthly = attendance_records.annotate(month=ExtractMonth('date')).values('month').annotate(
        present_count=Count('id', filter=Q(is_present=True))
    ).order_by('month')

    # Convert to array of 12 months
    monthly_counts = [0]*12
    for m in monthly:
        monthly_counts[m['month']-1] = m['present_count']

    # Build attendance_by_date
    attendance_by_date = {record.date.strftime("%Y-%m-%d"): 1 if record.is_present else 0
                          for record in attendance_records}

    data = {
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_rate": attendance_rate,
        "attendance_by_date": attendance_by_date,
        "monthly": monthly_counts
    }

    return JsonResponse(data)
def export_attendance(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Student', 'Date', 'Status'])

    attendances = Attendance.objects.using('mysql_db').all().select_related('student')

    for record in attendances:
        writer.writerow([
            record.id,
            record.student.name,
            record.date,
            'Present' if record.is_present else 'Absent'
        ])

    return response


def get_students(request):
    students = Student.objects.using('mysql_db').all()
    data = [
        {"id": s.id, "name": s.name, "email": s.email}
        for s in students
    ]
    return JsonResponse(data, safe=False)


def get_logged_in_students(request):
    today = localdate()
    logged_in = Attendance.objects.using('mysql_db').filter(
        date=today, is_present=True
    ).select_related('student')

    data = [
        {"id": a.student.id, "name": a.student.name, "email": a.student.email}
        for a in logged_in
    ]
    return JsonResponse(data, safe=False)
