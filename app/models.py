from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

AGE_CHOICES = (
    ('teens', '～10代'),
    ('twenties', '20代'),
    ('thirties', '30代'),
    ('forties', '40代'),
    ('fifties', '50代'),
    ('sixties', '60代～'),
)

GENDER_CHOICES = (
    ('male', '男性'),
    ('female', '女性'),
    ('other', 'その他'),
    ('no', '回答しない'),
)

SKIN_CHOICES = (
    ('normal_skin', '普通肌'),
    ('dry_skin', '乾燥肌'),
    ('oily_skin', '脂性肌'),
    ('combination_skin', '混合肌'),
    ('sensitive_skin', '敏感肌'),
)


class Category(models.Model):
    cosme_name = models.CharField(max_length=100)

class Product(models.Model):
    image = models.ImageField(upload_to='product_images/', blank=True, null=True) #商品画像
    cosme_name = models.CharField("商品名",max_length=200)  #商品名
    category = models.CharField("カテゴリー",max_length=50)  #カテゴリー    
    price = models.IntegerField("値段(円)", blank=True, null=True) #値段

    def __str__(self):
        return self.cosme_name
    
class Review(models.Model):
    #商品を紐づく（外部キー）
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product,
                                related_name='reviews',
                                on_delete=models.CASCADE)
    rating = models.IntegerField(
        choices=[
            (1,'☆☆☆☆★'),
            (2,'☆☆☆★★'),
            (3,'☆☆★★★'),
            (4,'☆★★★★'),
            (5,'★★★★★'),
    ], null=True,blank=True)
    
    goodpoint_comment = models.TextField(blank=True)
    badpoint_comment = models.TextField(blank=True)
    
    image = models.ImageField(upload_to='product_images/',blank=True,null=True)

    is_draft= models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add = True) #下書き作成日時
    posted_at = models.DateTimeField(null=True, blank=True) #投稿日時
  
    def __str__(self):
        return f"{self.product.cosme_name}のレビュー"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    age = models.CharField(
        max_length=10,
        choices=AGE_CHOICES,
        blank=True)
    
    gender = models.CharField(
        max_length=50,
        choices=GENDER_CHOICES,
        blank=True)
    
    skin_type = models.CharField(
        max_length=50,
        choices=SKIN_CHOICES,
        blank=True)
    
    def __str__(self):
        return self.user.username



class Cosmetic(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    
    
#レビューお気に入り
class ReviewFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    review = models.ForeignKey(
        Review,on_delete=models.CASCADE,
        related_name="favorites"
    )
    created_at=models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together=("user","review")
        
    def __str__(self):
        return f'{self.user}♡{self.review}'
