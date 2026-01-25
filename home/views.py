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
from home.models import Student, Attendance, Contact,LegacyRecord,FeePayment
from django.shortcuts import redirect
from django.db.models import Sum
from django.contrib.auth import logout



def index(request):
    student = None

    student_id = request.session.get('student_id')
    if student_id:
        try:
            student = Student.objects.using('mysql_db').get(id=student_id)
        except Student.DoesNotExist:
            # session is stale → clean it
            request.session.flush()
            student = None

    context = {
        "student": student,
        "variable": student.name if student else "Guest"
    }

    return render(request, "index.html", context)


INSTRUCTOR_ID = "palak"
INSTRUCTOR_PASSWORD = "root"

def instructor_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username == INSTRUCTOR_ID and password == INSTRUCTOR_PASSWORD:
            request.session["instructor_logged_in"] = True
            return redirect("admin_portal")
        else:
            messages.error(request, "Invalid instructor credentials")

    return render(request, "instructor_login.html")

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
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

        # 🚫 email already used by real account
        if Student.objects.using('mysql_db').filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        hashed_password = make_password(password)

        # 🔥 STEP 1: check legacy student (same name, no email)
        legacy_student = Student.objects.using('mysql_db').filter(
            name__iexact=name,
            email__isnull=True,
            legacy_key__isnull=False
        ).first()

        if legacy_student:
            # ✅ attach login details to legacy record
            legacy_student.email = email
            legacy_student.password = hashed_password
            legacy_student.gender = gender
            legacy_student.age = age
            legacy_student.height = height
            legacy_student.weight = weight
            legacy_student.save()

            messages.success(
                request,
                "Welcome back! Your previous records have been linked."
            )
            return redirect('logins')

        # 🆕 STEP 2: new student
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
def schedule(request):
    return render(request, "schedule.html")
def instructor_logout(request):
    logout(request)   # 🔥 clears session
    return redirect("logins")

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        description = request.POST.get('description')
        contact = Contact(
            name=name,
            email=email,
            description=description,
            date=datetime.today()
        )
        contact.save()
        messages.success(
            request,
            "Your feedback is stored; we'll get back to you shortly 😊"
        )
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

def instructor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("instructor_logged_in"):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Unauthorized"},
                    status=401
                )
            return redirect("instructor_login")
        return view_func(request, *args, **kwargs)
    return wrapper
@instructor_required
def admin_portal(request):
    students = Student.objects.using('mysql_db').all()
    feedbacks = Contact.objects.all().order_by('-date')

    total_students = students.count()

    total_attendance_sessions = Attendance.objects.using(
        'mysql_db'
    ).filter(is_present=True).count()

    total_legacy_amount = (
        LegacyRecord.objects.using('mysql_db')
        .aggregate(Sum("total_amount"))["total_amount__sum"]
        or 0
    )

    total_attendance_amount = (
        Attendance.objects.using('mysql_db')
        .aggregate(Sum("fee"))["fee__sum"]
        or 0
    )

    total_revenue = total_legacy_amount + total_attendance_amount

    student_id = request.GET.get('student_id')
    student = None
    attendance_records = []
    attendance_map = {}

    legacy_sessions = 0
    legacy_amount = 0
    present_count = 0
    total_fee = 0
    total_sessions = 0
    total_paid = 0
    fee_status = "N/A"

    if student_id:
        student = get_object_or_404(
            Student.objects.using('mysql_db'),
            id=student_id
        )

        attendance_records = Attendance.objects.using('mysql_db').filter(
            student=student
        )

        present_count = attendance_records.filter(is_present=True).count()

        total_fee = attendance_records.aggregate(
            total=Sum("fee")
        )["total"] or 0

        legacy_record = getattr(student, "legacyrecord", None)
        if legacy_record:
            legacy_sessions = legacy_record.total_sessions
            legacy_amount = legacy_record.total_amount

        total_sessions = legacy_sessions + present_count
        total_paid = legacy_amount + total_fee

        fee_status = "Paid" if total_paid > 0 else "Due"

        # ✅ CORRECT ATTENDANCE MAP
        attendance_map = {}
        for record in attendance_records:
            if record.session_status == "frozen":
                status = "frozen"
            elif record.session_status == "postponed":
                status = "postponed"
            else:
                status = "present" if record.is_present else "absent"

            attendance_map[record.date.strftime('%Y-%m-%d')] = status

    return render(request, 'admin_portal.html', {
        'students': students,
        'student': student,
        'attendance_map': attendance_map,
        'attendance_records': attendance_records,
        'total_students': total_students,
        'admin_sessions': total_attendance_sessions,
        'total_revenue': total_revenue,
        'legacy_sessions': legacy_sessions,
        'legacy_amount': legacy_amount,
        'present_count': present_count,
        'total_sessions': total_sessions,
        'total_paid': total_paid,
        'fee_status': fee_status,
        'feedbacks': feedbacks
    })

@csrf_exempt
def save_legacy_record(request):
    if request.method != "POST":
        return JsonResponse({"success": False})

    student_id = request.POST.get("student_id")
    sessions = request.POST.get("sessions", 0)
    amount = request.POST.get("amount", 0)

    student = get_object_or_404(
        Student.objects.using('mysql_db'),
        id=student_id
    )

    LegacyRecord.objects.using('mysql_db').update_or_create(
        student=student,
        defaults={
            "total_sessions": sessions,
            "total_amount": amount
        }
    )

    return JsonResponse({"success": True})

SESSION_FEE = 500 

@instructor_required
@csrf_exempt
 # change if needed
def save_attendance(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    # ---------- JSON / API ----------
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            attendance_data = data.get('attendance_data', [])
            saved_records = []

            for entry in attendance_data:
                student_id = entry.get('student_id')
                student = get_object_or_404(Student, id=student_id)

                date_str = entry.get('date')
                class_type = entry.get('class_type', 'Yoga')
                instructor = entry.get('instructor', 'Admin')
                status = entry.get('status', 'absent').lower()

                # ---- status handling ----
                session_status = 'normal'
                is_present = False
                fee = 0

                if status in ['frozen', 'postponed']:
                    session_status = status
                else:
                    is_present = (status == 'present')
                    fee = SESSION_FEE if is_present else 0

                Attendance.objects.using('mysql_db').update_or_create(
                    student=student,
                    date=date_str,
                    class_type=class_type,
                    defaults={
                        'instructor': instructor,
                        'is_present': is_present,
                        'session_status': session_status,
                        'fee': fee
                    }
                )

                saved_records.append({
                    'student_id': student.id,
                    'name': student.name,
                    'date': date_str,
                    'status': session_status if session_status != 'normal' else status,
                    'fee': fee
                })

            return JsonResponse({'success': True, 'saved_attendance': saved_records})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # ---------- ADMIN FORM ----------
    else:
        try:
            student_id = request.POST.get("student_id")
            if not student_id:
                return JsonResponse({'success': False, 'error': 'Missing student_id'})

            date_str = request.POST.get("date")
            date_val = (
                datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_str else now().date()
            )

            class_type = request.POST.get("class_type", "Yoga")
            instructor = request.POST.get("instructor", "Admin")
            status = request.POST.get("status", "absent").lower()

            session_status = 'normal'
            is_present = False
            fee = 0

            if status in ['frozen', 'postponed']:
                session_status = status
            else:
                is_present = (status == 'present')
                fee = SESSION_FEE if is_present else 0

            Attendance.objects.using('mysql_db').update_or_create(
                student_id=student_id,
                date=date_val,
                class_type=class_type,
                defaults={
                    'is_present': is_present,
                    'session_status': session_status,
                    'instructor': instructor,
                    'fee': fee
                }
            )

            return redirect("admin_portal")

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@instructor_required
@csrf_exempt
def delete_attendance(request, id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    try:
        record = get_object_or_404(
            Attendance.objects.using('mysql_db'),
            id=id
        )
        record.delete()
        return JsonResponse({"success": True, "message": "Attendance deleted"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@require_GET
def attendance_data_api(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return JsonResponse({"error": "Student not logged in"}, status=401)

    student = get_object_or_404(
        Student.objects.using('mysql_db'),
        id=student_id
    )

    attendance_records = Attendance.objects.using('mysql_db').filter(student=student)

    # ---- stats (exclude frozen/postponed) ----
    normal_sessions = attendance_records.filter(session_status='normal')

    total_days = normal_sessions.count()
    present_days = normal_sessions.filter(is_present=True).count()
    absent_days = total_days - present_days
    attendance_rate = round((present_days / total_days) * 100, 2) if total_days else 0

    # ---- monthly present count ----
    monthly = normal_sessions.annotate(
        month=ExtractMonth('date')
    ).values('month').annotate(
        present_count=Count('id', filter=Q(is_present=True))
    ).order_by('month')

    monthly_counts = [0] * 12
    for m in monthly:
        monthly_counts[m['month'] - 1] = m['present_count']

    # ---- attendance calendar ----
    attendance_by_date = {}
    for record in attendance_records:
        if record.session_status != 'normal':
            attendance_by_date[record.date.strftime("%Y-%m-%d")] = record.session_status
        else:
            attendance_by_date[record.date.strftime("%Y-%m-%d")] = (
                'present' if record.is_present else 'absent'
            )

    return JsonResponse({
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_rate": attendance_rate,
        "attendance_by_date": attendance_by_date,
        "monthly": monthly_counts
    })

@instructor_required
def export_attendance(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Student', 'Date', 'Status', 'Instructor', 'Class Type'])

    attendances = (
        Attendance.objects.using('mysql_db')
        .select_related('student')
        .all()
        .order_by('date')
    )

    for record in attendances:
        if record.session_status != 'normal':
            status = record.session_status.capitalize()
        else:
            status = 'Present' if record.is_present else 'Absent'

        writer.writerow([
            record.id,
            record.student.name,
            record.date,
            status,
            record.instructor,
            record.class_type
        ])

    return response

@instructor_required
def add_legacy_student(request):
    if request.method == "POST":
        name = request.POST.get("name").strip()
        legacy_key = request.POST.get("legacy_key").strip()
        total_sessions = request.POST.get("total_sessions")
        total_amount = request.POST.get("total_amount")
        notes = request.POST.get("notes", "")

        if not all([name, legacy_key, total_sessions, total_amount]):
            messages.error(request, "All fields are required")
            return redirect("add_legacy_student")

        # create student without email/password
        student = Student.objects.using('mysql_db').create(
            name=name,
            legacy_key=legacy_key
        )

        LegacyRecord.objects.using('mysql_db').create(
            student=student,
            total_sessions=total_sessions,
            total_amount=total_amount,
            notes=notes
        )

        messages.success(request, "Legacy student added successfully")
        return redirect("admin_portal")

    return render(request, "add_legacy_student.html")


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

def admin_student_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.using('mysql_db'),
        id=student_id
    )

    legacy = getattr(student, "legacyrecord", None)

    present_days = Attendance.objects.using('mysql_db').filter(
        student=student,
        is_present=True
    ).count()

    return JsonResponse({
        "name": student.name,
        "email": student.email,
        "age": student.age,
        "gender": student.gender,
        "present_days": present_days,
        "legacy_sessions": legacy.total_sessions if legacy else 0,
        "legacy_amount": legacy.total_amount if legacy else 0,
    })

@csrf_exempt
def api_save_legacy(request):
 
    print("🔥 api_save_legacy HIT")

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        print("📦 DATA:", data)

        student_id = data.get("student_id")
        total_sessions = data.get("total_sessions")
        total_amount = data.get("total_amount")

        if not student_id:
            return JsonResponse({"success": False, "error": "Missing student_id"})

        student = Student.objects.using("mysql_db").get(id=student_id)

        LegacyRecord.objects.using("mysql_db").update_or_create(
            student=student,
            defaults={
                "total_sessions": total_sessions,
                "total_amount": total_amount
            }
        )

        print("✅ LEGACY SAVED")
        return JsonResponse({"success": True})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
def update_fee_status(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        amount = data.get("amount")

        if not student_id or not amount:
            return JsonResponse(
                {"success": False, "error": "Missing student_id or amount"},
                status=400
            )

        student = Student.objects.get(id=student_id)

        FeePayment.objects.create(
            student=student,
            amount=amount
        )

        student.fees_paid = True
        student.last_fee_paid_on = now()
        student.save(update_fields=["fees_paid", "last_fee_paid_on"])

        return JsonResponse({
            "success": True,
            "last_paid": student.last_fee_paid_on.strftime("%d %b %Y, %I:%M %p")
        })

    except Student.DoesNotExist:
        return JsonResponse({"success": False, "error": "Student not found"}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
def paid_students_api(request):
    payments = (
        FeePayment.objects
        .select_related("student")
        .order_by("-paid_on")
    )

    data = []
    for p in payments:
        data.append({
            "student": p.student.name,
            "email": p.student.email,
            "amount": float(p.amount),
            "paid_on": p.paid_on.strftime("%d %b %Y, %I:%M %p")
        })

    return JsonResponse({"payments": data}, safe=False)
