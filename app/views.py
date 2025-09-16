from django.shortcuts import render
from . import forms

def login(request):
    return render(request, 'formapp/login.html')

def register(request):
    form = forms.UserInfo()
    if request.method == 'POST':
        form = forms.UserInfo(request.POST)
        if form.is_valid():
            print('バリデーション成功')
            print(
                f"""name: {form.cleaned_data['name']},
                email: {form.cleaned_data['email']},
                age_group: {form.cleaned_data['age_group']},
                gender: {form.cleaned_data['gender']},
                skin_type: {form.cleaned_data['skin_type']},
                password: {form.cleaned_data['password']},
                repassword: {form.cleaned_data['repassword']},"""
            )
    return render(
        request, 'formapp/register.html',context={
           'form':form
        }
    )
