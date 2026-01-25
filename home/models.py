from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=122)
    email = models.CharField(max_length=122)
    description = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.name
from django.db import models

from datetime import date

class Student(models.Model):
    name = models.CharField(max_length=100)

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    legacy_key = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    password = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    fees_paid = models.BooleanField(default=False)
    last_fee_paid_on = models.DateTimeField(null=True, blank=True)
    @property
    def months_enrolled(self):
        today = date.today()
        return (
            (today.year - self.created_at.year) * 12 +
            (today.month - self.created_at.month)
        )

    @property
    def bmi(self):
        if self.height and self.weight and self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return "N/A"
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        return "Obese"

    def __str__(self):
        return self.name

class Admin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    is_superuser = models.BooleanField(default=False)
    students = models.ManyToManyField(Student, related_name='admins', blank=True)

    def __str__(self):
        return self.username
class LegacyRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    total_sessions = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Legacy - {self.student}"
class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.paid_on}"
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()

    is_present = models.BooleanField(default=False)

    session_status = models.CharField(
        max_length=12,
        choices=[
            ('normal', 'Normal'),
            ('frozen', 'Frozen'),
            ('postponed', 'Postponed'),
        ],
        default='normal'
    )

    class_type = models.CharField(max_length=50, default='yoga')
    instructor = models.CharField(max_length=50)

    fee = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date', 'class_type')

    def __str__(self):
        if self.session_status != 'normal':
            return f"{self.student.name} - {self.date} - {self.session_status.title()}"
        return f"{self.student.name} - {self.date} - {'Present' if self.is_present else 'Absent'}"
