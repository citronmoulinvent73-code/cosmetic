from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from .models import AGE_CHOICES, GENDER_CHOICES, SKIN_CHOICES,Product,Review,Profile

User = get_user_model()

#共通
class AddFormInputClassMixin:
    def add_form_input_class(self):
        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput,
                                   forms.NumberInput, forms.Select, forms.Textarea, forms.FileInput)):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-input").strip()


#新規登録
class UserForm(AddFormInputClassMixin,UserCreationForm):
    email = forms.EmailField(label='メールアドレス',max_length=255)
    age_group =forms.ChoiceField(label='年齢', choices=AGE_CHOICES)
    gender = forms.ChoiceField(label='性別', choices=GENDER_CHOICES)
    skin_type =forms.ChoiceField(label='肌質', choices=SKIN_CHOICES)
    
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        username = (self.cleaned_data.get("username", "") or "")

        if len(username) < 4:
            raise forms.ValidationError("ユーザー名は4文字以上で入力してください。")

        if len(username) > 20:
            raise forms.ValidationError("ユーザー名は20文字以下で入力してください。")

        return username

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = "" #コロンの削除
        
        self.fields["username"].label = "ユーザー名"
        self.fields["username"].help_text = "4文字以上20文字以下で設定してください<br>※修正不可"
        self.fields["username"].min_length = 4
        self.fields["username"].max_length = 20
    
        self.fields["email"].help_text = "最大200文字で入力してください"
        self.fields["email"].max_length = 200

        self.fields["password1"].label = "パスワード"
        self.fields["password1"].help_text = "8文字以上の英数字を含むパスワードを設定してください"
   
        self.fields["password2"].label  = "パスワード再入力"
        self.fields["password2"].help_text = "確認のため、同じパスワードを入力してください"
    
        self.add_form_input_class()
    
#ログイン
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='メールアドレス')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "メールアドレス"
        })

        self.fields["password"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "パスワード"
        })
        
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if email:
            email = email.strip().lower()
        
        if not email or not password:
            raise forms.ValidationError('メールアドレスとパスワードを入力してください。')
            
        try:
            user = User.objects.get(email=email)
            
        except User.DoesNotExist:
            raise forms.ValidationError('メールアドレスまたはパスワードが間違っています。')

        self.user_cache = authenticate(
            self.request,
            username=user.username,
            password=password
        )
                               
        if self.user_cache is None:
            raise forms.ValidationError('メールアドレスまたはパスワードが間違っています。')
        
        return self.cleaned_data

       
#登録情報フォーム（ユーザー名は表示のみ・メールアドレスは修正可）
class UserEditForm(AddFormInputClassMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["username"].disabled = True
        self.fields["email"].label = "メールアドレス"
        
        self.add_form_input_class()
        
        
#登録情報フォーム'(編集可)
class ProfileForm(AddFormInputClassMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("age", "gender", "skin_type")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_form_input_class()


#パスワード変更
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["old_password"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "現在のパスワード",
        })
        self.fields["old_password"].error_messages["required"] = "現在のパスワードを入力してください。"
        
        self.fields["new_password1"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "新しいパスワード"
        })
        self.fields["new_password1"].error_messages["required"] = "新しいパスワードを入力してください。"
        
        self.fields["new_password2"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "新しいパスワード（確認用）"
        })
        self.fields["new_password2"].error_messages["required"] = "確認のため再度入力してください。"
        

#管理画面
class CosmeCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields =['image','cosme_name','category','price']

class CosmeForm(AddFormInputClassMixin,CosmeCreateForm):    
    CATEGORY_CHOICES = (
        ('', '選択してください'),
        ('skincare', 'スキンケア'),
        ('uvcare','ＵＶケア'),
        ('basemake', 'ベースメイク'),
        ('pointmake', 'ポイントメイク'),
        ('bodycare', 'ボディケア'),
        ('haircare', 'ヘアケア'),
        ('other', 'その他'),
    )
    
    image = forms.ImageField(
        label='画像',
        required=True,
        error_messages={
            'required': '画像を選択してください。'
        })
    cosme_name = forms.CharField(
        label='商品名',
        required=True,
        error_messages={
            'required': '商品名を入力してください。'
        })
    category = forms.ChoiceField(
        label='カテゴリー', 
        choices=CATEGORY_CHOICES, 
        required=True,
        error_messages={
            'required': 'カテゴリーを選択してください。'
        }
        )
    price = forms.IntegerField(
        label='価格',
        required=True,
        error_messages={
            'required': '価格を入力してください。'
        })
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""    #コロンの削除
        self.add_form_input_class()


class ReviewForm(forms.ModelForm):
    goodpoint_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="良い点（20文字以上）"
    )

    badpoint_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="悪い点（20文字以上）"
    )
       
    class Meta:
        model = Review
        fields =["rating","goodpoint_comment","badpoint_comment","image"]
               
    #下書き用 
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args,**kwargs)
        
    def clean(self):
        cleaned = super().clean()
                
        is_draft = "save_draft" in self.data

        rating_raw = (self.data.get("rating")or"").strip()
        good_raw = (self.data.get("goodpoint_comment") or "").strip()
        bad_raw  = (self.data.get("badpoint_comment") or "").strip()

        # 一時保存
        if is_draft:
            if not rating_raw and not good_raw and not bad_raw:
                raise ValidationError("一時保存は、評価・良い点・悪い点のいずれかを入力してください。")
            return cleaned

        # 投稿　submit：3つすべて必須
        if not rating_raw:
            self.add_error("rating", "評価（★）を選択してください。")
        if not good_raw:
            self.add_error("goodpoint_comment", "良い点を入力してください。")
        if not bad_raw:
            self.add_error("badpoint_comment", "悪い点を入力してください。")
        
        # 20文字以上（フォームのmin_lengthでも弾くが、メッセージ統一したいならここでも）
        if good_raw and len(good_raw) < 20:
            self.add_error("goodpoint_comment", "良い点は20文字以上で入力してください。")
        if bad_raw and len(bad_raw) < 20:
            self.add_error("badpoint_comment", "悪い点は20文字以上で入力してください。")

        return cleaned