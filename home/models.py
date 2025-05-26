from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=122)
    email = models.CharField(max_length=122)
    description = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.name
from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    height = models.FloatField()
    weight = models.FloatField()
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    password = models.CharField(max_length=128)  # hashed password
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Admin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    is_superuser = models.BooleanField(default=False)
    students = models.ManyToManyField(Student, related_name='admins', blank=True)

    def __str__(self):
        return self.username

