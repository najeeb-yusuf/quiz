from urllib import response
from urllib.error import HTTPError
from django.shortcuts import render, redirect
from .models import Section,Question,Option, Grade,Response
from django import forms
import json
from django.http import HttpResponse
from django.urls import reverse

from django.contrib.auth import authenticate,logout
from django.contrib import messages

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail



def language(request):
    return render(request, "quiz/language.html")

def index(request):
    lang = list(request.POST)[1]
    request.session['lang'] = lang
    return render(request,'quiz/mail.html',{
        'lang' : lang
    })

def results(request):
    lang = request.session.get('lang')
    section_totals = {}
    section_max = []
    section_desc = []
    for section in Section.objects.all():
        section_max.append(sum([question.weight for question in section.questions.all()]))
        if lang == 'en':
            section_desc.append(section.title)
        else:
            section_desc.append(section.title_pt)

    
    if request.method == 'POST':
        for i,q_id in enumerate(request.POST):
            if i == 0:
                continue
            if Question.objects.get(q_id=q_id).section.s_id not in section_totals:
                section_totals[Question.objects.get(q_id=q_id).section.s_id] = int(request.POST.get(q_id))
            else:
                section_totals[Question.objects.get(q_id=q_id).section.s_id] += int(request.POST.get(q_id))
    # convert the results to percentages for the pie chart
    results = list(zip(list(section_totals.values()),section_max))
    request.session['results'] = results
    percentages = [x/y*100 for x,y in results]
    # create a new response object to log the database whenever someone answers the quiz
    response = Response(email=request.session.get('mail'))
    response.save()
    for i,grade in enumerate(list(section_totals.values())):
        new_grade = Grade(section=list(Section.objects.all())[i],grade=grade,response=response)
        new_grade.save()

    data = list(zip(list(section_totals.values()),section_max, list(section_totals.keys()),section_desc))
    return render(request, 'quiz/results.html', {
        "data" :data,
        'percentages': percentages,
        'lang': lang,
        })

def enter_mail(request):
    lang = request.session.get('lang')
    if not lang:
        return render(request, "quiz/language.html")
    if request.method == 'POST':
        request.session['mail'] = request.POST['mail']
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
    lang = request.session.get('lang')
    email = request.POST.get('mail')
    if lang == 'en':
        subject = "DIMA Questionnaire results"
        message = "This is a test message"
    else:
        subject = "EDIP resultados do questionário"
        message = "Portugese"
    from_email = 'noreply@2079productions.com'
    results = request.session['results']
    if email:
        message = Mail(from_email=from_email,
                to_emails=email,
                subject=subject,
                plain_text_content="Here are your results",
                html_content=f"""
                <div><strong><u> Results </u> </strong></div>
                <br>
                <table class="GeneratedTable" style="border: 1px solid black;
  border-collapse: collapse;">
                <thead style="border: 1px solid black;
  border-collapse: collapse;">
                    <tr style="border: 1px solid black;
  border-collapse: collapse;">
                    <th>Pillar 1</th>
                    <th>Pillar 2</th>
                    <th>Pillar 3</th>
                    <th>Pillar 4</th>
                    <th>Pillar 5</th>
                    </tr>
                </thead>
                <tbody style="border: 1px solid black;
  border-collapse: collapse;">
                    <tr style="border: 1px solid black;
  border-collapse: collapse;">
                    <td>{results[0][0]}/{results[0][1]}</td>
                    <td>{results[1][0]}/{results[1][1]}</td>
                    <td>{results[2][0]}/{results[2][1]}</td>
                    <td>{results[3][0]}/{results[3][1]}</td>
                    <td>{results[4][0]}/{results[4][1]}</td>
                    </tr>
                </tbody>
                </table>


                """)
        try:
#             make sure you define an environment variable in the production environment
            key = os.getenv('API_KEY')
            sg = SendGridAPIClient(key)
            response = sg.send(message)

            return render(request,'quiz/mail_success.html', {
                'email': email
            })
        except Exception as e:
            return HttpResponse('Error sending mail.')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')

    

def responses(request):
    return render(request, 'quiz/responses.html', {
        'responses':Response.objects.all()
    })


def login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            return render(request,'quiz/responses.html',{
                'responses': Response.objects.all()
            })
        else:
            messages.add_message(request, messages.WARNING, 'Invalid credentials')
            return render(request,'quiz/login.html')

    return render(request,'quiz/login.html')


def logout_user(request):
    logout(request)
    return render(request,'quiz/language.html')
