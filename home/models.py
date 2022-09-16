
# Create your models here.

from cgi import print_form
import email
from pyexpat import model
from django.db import models
from os import PRIO_USER
import django


app_label = 'home' 

class Section(models.Model):
    s_id = models.AutoField(primary_key=True)
    section_number = models.IntegerField(default=1)
    title = models.TextField(verbose_name='title', blank=False)
    desc = models.TextField(verbose_name='text description')
    # portugese title and description
    title_pt = models.TextField(verbose_name='title pt', blank=True, null=True)
    desc_pt = models.TextField(verbose_name='text description pt', blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.title}"
class Question(models.Model):
    q_id = models.AutoField(primary_key=True)
    text = models.TextField()
    text_pt = models.TextField(verbose_name="Text portugese",blank=True, null=True)
    weight = models.IntegerField(default=10)
    section = models.ForeignKey(to=Section, on_delete=models.CASCADE, related_name='questions')

    def __str__(self) -> str:
        return f"{self.q_id}: {self.text}"


class Option(models.Model):
    o_id = models.AutoField(primary_key=True)
    text = models.TextField()
    text_pt = models.TextField(blank=True, null=True)
    weight = models.IntegerField()
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE, related_name='options')

    def __str__(self) -> str:
        return f'{self.question.text} : {self.text}'

class Response(models.Model):
    r_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=128)

    def __str__(self) -> str:
        return super().__str__()
class Grade(models.Model):
    g_id = models.AutoField(primary_key=True)
    section = models.ForeignKey(to=Section, on_delete=models.CASCADE, related_name="section")
    grade = models.IntegerField()
    response = models.ForeignKey(to=Response, on_delete=models.CASCADE, related_name="grades")

    def __str__(self) -> str:
        return f"Section {self.section.section_number}: {self.grade}"


