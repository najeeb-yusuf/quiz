from urllib.error import HTTPError
from django.shortcuts import render, redirect
from .models import Section,Question,Option
from django import forms
import json
from django.http import HttpResponse
from django.urls import reverse
# Create your views here.

from django.core.mail import send_mail, BadHeaderError

def language(request):
    return render(request, "quiz/language.html")

def index(request):
    lang = list(request.POST)[1]
    request.session['lang'] = lang
    return render(request,'quiz/mail.html',{
        'lang' : lang
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

def enter_mail(request):
    lang = request.session.get('lang')
    if not lang:
        return render(request, "quiz/language.html")
    if request.method == 'POST':
        request.session['mail'] = list(request.POST)[1] 
        if lang == 'en':
            return render(request,"quiz/index.html", {
                    'sections' : Section.objects.all()
                })
        else:
            return render(request,"quiz/index-pt.html", {
                    'sections_pt' : Section.objects.all()
                })
    else:
        return render(request, "quiz/language.html")



def send_email(request):
    email = request.POST.get('email')
    subject = "DIMA Questionnaire results"
    message = " <h1>This is a test message </h1>"
    from_email = 'yusufnajlawal@gmail.com'
    if email:
        try:
            send_mail(subject, message, from_email, [email])
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return HttpResponse('<h1> Done. </h1>')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')