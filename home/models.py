from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=122)
    email = models.CharField(max_length=122)
    description = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.name
class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Admin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    is_superuser = models.BooleanField(default=False)

    def __str__(self):
        return self.username
# Create your models here.
