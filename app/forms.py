from django import forms

class UserInfo(forms.Form):
    AGE_CHOICES =[
        ('teens','～10代'),
        ('twenties','20代'),
        ('therties','30代'),
        ('forties','40代'),
        ('fivteies','50代'),
        ('teens','60代～'),
    ]
    GENDER_CHOICES =[
        ('male','男性'),
        ('female','女性'),
        ('other','その他'),
        ('no','回答しない'),
    ]
    SKIN_CHOICES =[
        ('normal_skin','普通肌'),
        ('dry_skin','乾燥肌'),
        ('oily_skin','脂性肌'),
        ('combination_skin','混合肌'),
        ('sensitive_skin','敏感肌'),
    ]
    name = forms.CharField(label='ユーザー名', max_length=20)
    email = forms.EmailField(label='メールアドレス',max_length=255)
    age_group =forms.ChoiceField(label='年齢', choices=AGE_CHOICES)
    gender = forms.ChoiceField(label='性別', choices=GENDER_CHOICES)
    skin_type =forms.ChoiceField(label='肌質', choices=SKIN_CHOICES)
    password = forms.CharField(label='パスワード', max_length=255)
    repassword =forms.CharField(label='パスワード再入力', max_length=255)