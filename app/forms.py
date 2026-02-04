from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import AGE_CHOICES, GENDER_CHOICES, SKIN_CHOICES,Product,Review,Profile

class UserForm(UserCreationForm):
        
    AGE_CHOICES =[
        ('teens','～10代'),
        ('20s','20代'),
        ('30s','30代'),
        ('40s','40代'),
        ('50s','50代'),
        ('60plus','60代～'),
    ]
    GENDER_CHOICES =[
        ('male','男性'),
        ('female','女性'),
        ('other','その他'),
        ('no','回答しない'),
    ]
    SKIN_CHOICES =[
        ('normal','普通肌'),
        ('dry','乾燥肌'),
        ('oily','脂性肌'),
        ('combination','混合肌'),
        ('sensitive','敏感肌'),
    ]
    email = forms.EmailField(label='メールアドレス',max_length=255)
    age_group =forms.ChoiceField(label='年齢', choices=AGE_CHOICES)
    gender = forms.ChoiceField(label='性別', choices=GENDER_CHOICES)
    skin_type =forms.ChoiceField(label='肌質', choices=SKIN_CHOICES)
    
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    #コロンの削除
        self.label_suffix = ""
    

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label='ユーザー名'
        self.fields['username'].max_length = 20
        self.fields['password'].label='パスワード'

       
#登録情報フォーム（表示のみ・修正不可）
class UserReadOnlyForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.disabled = True

#登録情報フォーム'(編集可)
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("age", "gender", "skin_type")


#管理画面
class CosmeCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields =['image','cosme_name','category','price']

class CosmeForm(CosmeCreateForm):    
    CATEGORY_CHOICES = (
        ('skincare', 'スキンケア'),
        ('uvcare','ＵＶケア'),
        ('basemake', 'ベースメイク'),
        ('pointmake', 'ポイントメイク'),
        ('bodycare', 'ボディケア'),
        ('haircare', 'ヘアケア'),
        ('other', 'その他'),
    )
    
    category = forms.ChoiceField(label='カテゴリー', choices=CATEGORY_CHOICES)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""    #コロンの削除


class ReviewForm(forms.ModelForm):
    RATTING_CHOICES = [
        (1,'☆☆☆☆★'),
        (2,'☆☆☆★★'),
        (3,'☆☆★★★'),
        (4,'☆★★★★'),
        (5,'★★★★★'),
    ]

    rating = forms.ChoiceField(
        choices=RATTING_CHOICES,
        required=True,
        widget=forms.RadioSelect,
        label="評価"
        )

    goodpoint_comment = forms.CharField(
        min_length=20,
        widget=forms.Textarea,
        label="コメント（20文字以上）"
    )

    badpoint_comment = forms.CharField(
        min_length=20,
        widget=forms.Textarea,
        label="コメント（20文字以上）"
    )

       
    class Meta:
        model = Review
        fields =["rating","goodpoint_comment","badpoint_comment","image"]
        exclude = ("product","user","is_draft")

        widgets={
            'rating' : forms.RadioSelect(attrs={'class':'rating-radio'}),  
            'goodpoint_comment':forms.Textarea(attrs={"class":"form-control","rows":3}),
            'badpoint_comment':forms.Textarea(attrs={"class":"form-control","rows":3}),
        }
       
    #下書き用 
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        
        if self.data.get("action") =="draft":
            for f in self.fields.values():
                f.required = False