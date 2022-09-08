
# Create your models here.

from django.db import models
from os import PRIO_USER
import django


app_label = 'home' 

class Section(models.Model):
    s_id = models.AutoField(primary_key=True)
    section_number = models.IntegerField(default=1)
    title = models.TextField(verbose_name='title', blank=False)
    desc = models.TextField(verbose_name='text description')

    def __str__(self) -> str:
        return f"{self.title}"
class Question(models.Model):
    q_id = models.AutoField(primary_key=True)
    text = models.TextField()
    weight = models.IntegerField(default=10)
    section = models.ForeignKey(to=Section, on_delete=models.CASCADE, related_name='questions')

    def __str__(self) -> str:
        return f"{self.q_id}: {self.text}"


class Option(models.Model):
    o_id = models.AutoField(primary_key=True)
    text = models.TextField()
    weight = models.IntegerField()
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE, related_name='options')

    def __str__(self) -> str:
        return f'{self.question.q_id} : {self.text}'
