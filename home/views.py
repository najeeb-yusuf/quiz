from urllib.error import HTTPError
from django.shortcuts import render
from .models import Section,Question,Option
from django import forms
import json

# Create your views here.

def index(request):
    return render(request,"quiz/index.html", {
        'sections' : Section.objects.all()
    })

def results(request):
    section_totals = {}
    section_max = []
    section_desc = []
    for section in Section.objects.all():
        section_max.append(sum([question.weight for question in section.questions.all()]))
        section_desc.append(section.title)
    
    if request.method == 'POST':
        for i,q_id in enumerate(request.POST):
            if i == 0:
                continue
            if Question.objects.get(q_id=q_id).section.s_id not in section_totals:
                section_totals[Question.objects.get(q_id=q_id).section.s_id] = int(request.POST.get(q_id))
            else:
                section_totals[Question.objects.get(q_id=q_id).section.s_id] += int(request.POST.get(q_id))
  
    percentages = [x/y*100 for x,y in zip(list(section_totals.values()),section_max)]
        
    return render(request, 'quiz/results.html', {
        "data" : list(zip(list(section_totals.values()),section_max, list(section_totals.keys()),section_desc)),
        'percentages': percentages
        })

