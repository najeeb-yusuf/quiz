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

def serve(request):
    ''' Is supposed to hold all the logic behind routing the sections and questions.
    Makes sure that everything is served in the correct order and keeps track of the grade.
     '''
    # I'm going to use session variables to store whether the last thing I served was a section or question
    # It's also going to infer what to serve next based on that.
    if not request.session.get('answered'):
        request.session['answered'] = {0:0}
        request.session['visited'] = []
        return redirect(reverse('section', kwargs={'section': 1}))
    else:  
        # breakpoints is a variable that tells me when i have a new section
        # I'm hard coding it for now so that this works but ideally it should be inferred from the models
        if request.method == 'POST':
            q_no = request.POST.get('question')
            value = request.POST.get('value')
            # All the following code is just to store the new value into the session
            # It can probably be neater but this is quick
            answered = request.session.get('answered')
            answered[q_no] = value
            request.session['answered'] = answered 
        
        breakpoints = [6,12,16,21]
        last_answered = int(list(request.session.get('answered'))[-1])
        if last_answered == len(Question.objects.all()):
            return redirect(reverse('results'))
        if last_answered in breakpoints and last_answered not in request.session.get('visited'):
            visited = request.session.get('visited')
            visited.append(last_answered)
            request.session['visited'] = visited 
            return redirect(reverse('section', kwargs={'section': breakpoints.index(last_answered)+2}))
        else:
            return redirect(reverse('question', kwargs={'question': int(last_answered)+1}))



def section(request, section):
    ''' This serves the section that fn.serve orders it to.
    Must have section_number, section_title and section_description '''
    lang = request.session.get('lang')
    section = Section.objects.get(pk=section)
    title = section.title if lang == 'en' else section.title_pt
    desc = section.desc if lang == 'en' else section.desc_pt
    return render(request,'quiz/section.html',{
        'section_number' : section.s_id,
        'section_title' : title,
        'section_description' : desc,
        'section_image' : section.image
    })


def question(request, question):
    ''' This serves the question that fn.serve orders it to.
    Must have lang, question'''
    lang = request.session.get('lang')
    current_section = request.session.get('section_number')
    # Get the length of the current section such that as soon as you've served the last question
    #  for the section, change the current display to section
    length = len(Question.objects.filter(section=current_section))
    curr_question = Question.objects.get(pk=question)

    return render(request,'quiz/question.html', {
        'question': curr_question,
        'lang' : lang,
        'last' : question == 24
    })




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
    for i,q_id in enumerate(request.session.get('answered')):
        if i == 0:
            continue
        if Question.objects.get(q_id=q_id).section.s_id not in section_totals:
            section_totals[Question.objects.get(q_id=q_id).section.s_id] = int(request.session.get('answered').get(q_id))
        else:
            section_totals[Question.objects.get(q_id=q_id).section.s_id] += int(request.session.get('answered').get(q_id))
    # convert the results to percentages for the pie chart
    results = list(zip(list(section_totals.values()),section_max))
    request.session['results'] = results
    percentages = [x/y*100 for x,y in results]

    # define a dictionary for the grades
    grades = {
        1:(17,45,60),
        2:(17,45,60),
        3:(12,30,40),
        4:(15,37,50),
        5:(9,22,30)
        }
    def determine_grade(pillar,grade,lang):
        if 0 <= grade <= grades[pillar][0]:
            return 'Starting' if lang == 'en' else 'Iniciando'
        elif grades[pillar][0]+1 <= grade <= grades[pillar][1]:
            return "Integrating" if lang=='en' else 'Integrando'
        else:
            return "Consolidating" if lang=='en' else 'Consolidando'

    def determine_class(pillar,grade):
        if 0 <= grade <= grades[pillar][0]:
            return 'danger'
        elif grades[pillar][0]+1 <= grade <= grades[pillar][1]:
            return "warning"
        else:
            return "success"
    tags = [determine_grade(i+1,x,lang) for i,x in enumerate(section_totals.values())]
    classes = [determine_class(i+1,x) for i,x in enumerate(section_totals.values())]


    # create a new response object to log the database whenever someone answers the quiz
    response = Response(email=request.session.get('mail'))
    response.save()
    for i,grade in enumerate(list(section_totals.values())):
        new_grade = Grade(section=list(Section.objects.all())[i],grade=grade,response=response)
        new_grade.save()

    data = list(zip(list(section_totals.values()),section_max, list(section_totals.keys()),section_desc,list(tags), list(classes)))
    return render(request, 'quiz/results.html', {
        "data" :data,
        'percentages': percentages,
        'lang': lang,
        })

def enter_mail(request):
    lang = request.session.get('lang')
    # reset the session variables if they exist
    if request.session.get('answered'):
        del request.session['answered']
    if request.session.get('visited'):
        del request.session['visited']
    if not lang:
        return render(request, "quiz/language.html")
    if request.method == 'POST':
        request.session['mail'] = request.POST['mail']
        return render(request,"quiz/dima-intro.html", {
                    'lang' : lang
                })
    else:
        return render(request, "quiz/language.html")


def send_email(request):
    grades = {
        1:(17,45,60),
        2:(17,45,60),
        3:(12,30,40),
        4:(15,37,50),
        5:(9,22,30)
        }
    def determine_grade(pillar,grade,lang):
        if 0 <= grade <= grades[pillar][0]:
            return 'Starting' if lang == 'en' else 'Iniciando'
        elif grades[pillar][0]+1 <= grade <= grades[pillar][1]:
            return "Integrating" if lang=='en' else 'Integrando'
        else:
            return "Consolidating" if lang=='en' else 'Consolidando'

    lang = request.session.get('lang')
    email = request.POST.get('mail')
    from_email = 'noreply@2079productions.com'
    results = request.session['results']
    if email:
        if lang == 'en':
            subject = "DIMA Questionnaire results"
            message = "This is a test message"
            html_content = f"""
                <div><strong><u> Results </u> </strong></div>
                <br>
                <table class="GeneratedTable" style="border: 1px solid black;
  border-collapse: collapse;">
                <thead style="border: 1px solid black;
  border-collapse: collapse;">
                    <tr style="border: 1px solid black;
  border-collapse: collapse;">
                    <th>Pillar 1: Mission, Values & Behaviors</th>
                    <th>Pillar 2: Governance & Company Operations</th>
                    <th>Pillar 3: Policies, Compliance & Protective Measures</th>
                    <th>Pillar 4: Business Partnerships & External Relationships</th>
                    <th>Pillar 5: Proactive Equity Outreach</th>
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
                    <tr style="border: 1px solid black;
  border-collapse: collapse;">
                    <td>{determine_grade(1,results[0][0],lang)}</td>
                    <td>{determine_grade(2,results[1][0],lang)}</td>
                    <td>{determine_grade(3,results[2][0],lang)}</td>
                    <td>{determine_grade(4,results[3][0],lang)}</td>
                    <td>{determine_grade(5,results[4][0],lang)}</td>

                    </tr>
                </tbody>
                </table>


                """
        else:
            subject = "EDIP resultados do questionário"
            message = "Portugese"
            html_content = f"""
                <div><strong><u> Resultados </u> </strong></div>
                <br>
                <table class="GeneratedTable" style="border: 1px solid black;
  border-collapse: collapse;">
                <thead style="border: 1px solid black;
  border-collapse: collapse;">
                    <tr style="border: 1px solid black;
  border-collapse: collapse;">
                    <th>Pillar 1: Missão, Valores e Comportamentos</th>
                    <th>Pillar 2: Governança e  Operações da empresa</th>
                    <th>Pillar 3: Policies, Compliance & Protective Measures</th>
                    <th>Pillar 4: Parcerias de Negócios e Relacionamentos Externos</th>
                    <th>Pillar 5: Ações Proativas de Equidade</th>
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


                """

        message = Mail(from_email=from_email,
                to_emails=email,
                subject=subject,
                plain_text_content="Here are your results",
                html_content=html_content)
        try:
#             make sure you define an environment variable in the production environment
            key = os.getenv('API_KEY')
            sg = SendGridAPIClient(key)
            response = sg.send(message)

            return render(request,'quiz/mail_success.html', {
                'email': email,
                'lang' : lang
            })
        except Exception as e:
            print(e.to_dict)
            return HttpResponse(f'''
            Error sending mail.
            <br>
            Error code {e}
            ''')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')

    

def responses(request):
    return render(request, 'quiz/responses.html', {
        'responses':Response.objects.all().desc()
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
