import os
import csv
import requests
from django.shortcuts import render, redirect
from livro.models import Livro
from livro.forms import LivroCreate
from django.http import HttpResponse, Http404
from bibliotecapp.settings import STATIC_URL, STATIC_ROOT, MEDIA_URL, MEDIA_ROOT
from django.contrib.auth.decorators import login_required, permission_required


# Create your views here.
def index(request):
    shelf = Livro.objects.all()
    return render(request, 'livro/biblioteca.html', {'shelf': shelf})

@permission_required('livro.add_livro', raise_exception=False)
@login_required()
def upload(request):
    upload = LivroCreate()
    if request.method == 'POST':
        upload = LivroCreate(request.POST, request.FILES)
        if upload.is_valid():
            upload.save()
            return redirect('livro:index')
        else:
            return render(request,'livro/upload_form.html', {'upload_form':upload, 'error':upload.errors})
    else:
        return render(request, 'livro/upload_form.html', {'upload_form':upload,'titulo':"Upload"})

@permission_required('livro.change_livro', raise_exception=False)
@login_required()
def update_livro(request, livro_id):
    livro_id = int(livro_id)
    try:
        livro_sel = Livro.objects.get(id = livro_id)
    except Livro.DoesNotExist:
        return redirect('livro:index')
    livro_form = LivroCreate(request.POST or None, instance = livro_sel)

    if request.method == 'POST':
        livro_form = LivroCreate(request.POST, request.FILES, instance = livro_sel)
        if livro_form.is_valid():
            livro_form.save()
        return redirect('livro:index')
    return render(request, 'livro/upload_form.html', {'upload_form':livro_form,'titulo':"Update"})

@permission_required('livro.delete_livro', raise_exception=False)
@login_required()
def delete_livro(request, livro_id):
    livro_id = int(livro_id)
    try:
        livro_sel = Livro.objects.get(id = livro_id)
    except Livro.DoesNotExist:
        return redirect('livro:index')
    livro_sel.delete()
    return redirect('livro:index')

@permission_required('livro.view_livro', raise_exception=False)
def download(request, livro_id):
    livro_id = int(livro_id)
    try:
        livro_sel = Livro.objects.get(id = livro_id)
    except Livro.DoesNotExist:
        return redirect('livro:index')

    file_path = os.path.join(MEDIA_ROOT, livro_sel.document.url)
    file_path = os.getcwd() + file_path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def catalogo(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dump.csv"'
    header = [f.name for f in Livro._meta.get_fields()]

    writter = csv.writer(response)
    writter.writerow(header)
    for registro in Livro.objects.all():
        writter.writerow([getattr(registro, col) for col in header])

    return response

def livro(request, livro_id):
    livro_id = int(livro_id)
    try:
        livro = Livro.objects.get(id=livro_id)
    except Livro.DoesNotExist:
        return redirect('livro:index')

    descricao = livro.descricao

    URL = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    KEY = 'trnsl.1.1.20191212T131903Z.88805ef800f95e27.cbfc26202a49817df29b23f4eb069d3a92a22d9a'
    LANG = 'pt-en'
    req = '''{0}?key={1}&text={2}&lang={3}'''.format(URL, KEY, descricao, LANG)
    resposta = requests.post(req)
    if resposta.status_code != 200:
        traducao = "Traducao Indisponível"
    else:
        traducao = resposta.json()['text'][0]
    return render(request, 'livro/livro.html', {'livro':livro, 'traducao': traducao,'req':req})

def error_404(request, exception):
    return render(request,'error.html', {'erro': '404'})

def error_500(request):
    return render(request,'error.html', {'erro': '500'})
