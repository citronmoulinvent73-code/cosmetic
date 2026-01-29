from django.shortcuts import render, redirect ,get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg, Q, Exists, OuterRef, IntegerField
from django.db import models
from django.db.models.functions import Cast, Round
from django import forms

from .forms import LoginForm,UserForm,CosmeForm,ReviewForm, UserReadOnlyForm, ProfileForm
from .models import Product,Review,ReviewFavorite, Category, Profile


def login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()            
            
            auth_login(request, user)
            return redirect(reverse('form_app:home'))
        
    else:
        form = LoginForm()
    
    return render(request, 'form_app/login.html', {'form':form})

def staff_only(user):
    return user.is_staff

def product_detail(request, pk):
    product = get_object_or_404(Product,pk=pk)
    
    reviews = Review.objects.filter(
        product=product,
        is_draft=False
        ).annotate(
            is_favorited=Exists(
                ReviewFavorite.objects.filter(
                    review=OuterRef("pk"),
                    user=request.user)
                )
            )
    
    return render(
        request,
        'form_app/product_detail.html',
        {'product':product,"reviews":reviews,})
    
    
#product_detail、home、ranking（Reviewを取得するviewすべて）で同じannotateを使用
def with_favorite_flag(queryset, user):
    if user.is_authenticated:
        return queryset.annotate(
            is_favorited=Exists(
                ReviewFavorite.objects.filter(
                    review=OuterRef("pk"),
                    user=user
                )
            )
        )
    return queryset.annotate(is_favorited=models.Value(False))


def ranking(request, category=None):
    if category is None:
        category = "skincare"
        
    skin_type = request.GET.get("skin_type")
    age_group = request.GET.get("age_group")
    
    CATEGORY_LABEL = dict(CosmeForm.CATEGORY_CHOICES)
    category_label = CATEGORY_LABEL.get(category, category)
            
    filters = Q(reviews__is_draft=False)
    
    if skin_type:
        filters &= Q(reviews__skin_type=skin_type)
        
    if age_group:
        filters &= Q(reviews__age_group=age_group)
        
    products = Product.objects
    
    if category:
        products = products.filter(category=category)
    
    products = (
        products
        .annotate(#集計
            review_count=Count("reviews", filter=filters, distinct=True),
            avg_rating=Avg("reviews__rating", filter=filters),
        )
        .filter(review_count__gt=0) #0件商品を除外
        .order_by("-review_count","-avg_rating")#並び替え
    )
     
    return render(
        request,
        "form_app/ranking.html",
        {"products": products,
         "category_label": category_label,
         }
    )
    

def ranking_view(request, category="skincare"):
    print("ranking_view called:", category)
    CATEGORY_LABELS ={
        "skincare": "スキンケア",
        "uvcare": "ＵＶケア",
        "basemake": "ベースメイク",
        "pointmake": "ポイントメイク",
        "bodycare": "ボディケア",
        "haircare": "ヘアケア",
        "other": "その他",
    }
    
    ranking_type = category or "skincare" #デフォルト設定
    category_label = CATEGORY_LABELS.get(ranking_type, "スキンケア")
    
    products = (Product.objects
    .filter(category = ranking_type)#商品そのものの条件、DBに元からある項目
    .annotate(
        avg_rating=Avg(
            "reviews__rating",
            filter=Q(reviews__is_draft=False)
        ),
        review_count=Count(
            "reviews",
            filter=Q(reviews__is_draft=False)
        )        
    )
    .filter(review_count__gt=0)#集計結果に対する条件
    .order_by("-avg_rating","review_count"))

    print (products.query)

    return render(request, 
                  "form_app/ranking.html",
                  {
                    "products": products,
                    "ranking_type": ranking_type,
                    "category_label": category_label,
                    }
                )


@login_required
def home(request):
    products = Product.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    ranking_products = (
        Product.objects
        .annotate(avg_rating=Avg('reviews__rating'))
        .filter(avg_rating__isnull=False)
        .order_by('-avg_rating')[:5])

    reviews = Review.objects.annotate(
        is_favorited=Exists(
            ReviewFavorite.objects.filter(
                review=OuterRef("pk"),
                user=request.user)
            )
        )
    
    return render(
        request, 'form_app/home.html',
        {'products':products,
         'ranking_products':ranking_products,})
    
def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect(reverse('form_app:login'))
    else:
        form =UserForm()
            
    return render(
        request,
        'form_app/register.html',
        context={'form':form}
        )

def category_product_list(request, category):
    #form.pyのchoicesを辞書化
    CATEGORY_LABEL = dict(CosmeForm.CATEGORY_CHOICES)
    category_label =CATEGORY_LABEL.get(category, category)
    
    products = (
        Product.objects
        .filter(category=category)
        .annotate(review_count=Count(
            "reviews",
            filter=Q(reviews__is_draft=False)
            ),
            avg_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_draft=False)
                )
            ) #商品の総レビュー数
        .order_by("-review_count", "-avg_rating")
    )
    return render(
        request,
        "form_app/category_product_list.html",
        {
            "products":products,
            "category":category,
            "category_label":category_label,
            }
        )


#レビューお気に入り追加（トグル処理）
def review_favorite(request, review_id):
    if not request.user.is_authenticated:
        return redirect("login")
    
    review=get_object_or_404(Review, id=review_id)
    
    favorite,created = ReviewFavorite.objects.get_or_create(
        user=request.user,
        review=review
    )
    if not created:
        favorite.delete()
        
    return redirect(request.META.get("HTTP_REFERER","/"))

#お気に入りタブ
def favorite_review_list(request):
    favorites = ReviewFavorite.objects.filter(
        user=request.user
    ).select_related('review','review__product')
    
    return render(
        request,
        'form_app/favorite_review_list.html',
        {'favorites':favorites})



def user_logout(request):
    logout(request)
    return redirect(reverse('form_app:login'))

def search_result_view(request):
    query = request.GET.get('q')
    products = Product.objects.none()

    if query:
        products = (
            Product.objects
            .filter(cosme_name__icontains=query)
            )
    
    return render(request, "form_app/search_result.html",{
        "query": query,
        "products": products,
        })
    
    
def admin_my_page(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("権限がありません")
    
    return render(request, "form_app/admin_my_page.html")

def product_create(request):
    
    if request.method == 'POST':
        form = CosmeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('form_app:product_create')#登録後同じ画面に戻る
    else:
        form =CosmeForm()
            
    return render(request,'form_app/product_create.html',{'form':form})

#商品検索
def product_search(request):
    query = request.GET.get("q","")
    products = Product.objects.none()
    
    if query:
        products = (
            Product.objects
            .filter(cosme_name__icontains=query)
            .annotate(
                avg_rating=Avg('reviews__rating'),
                avg_rating_int=Cast(Round(Avg('reviews__rating')),IntegerField()),
                review_count=Count('reviews')
            )
        )
    
    mode = request.GET.get("mode","normal")
    
    if mode == "review":
        tpl = "form_app/product_search.html"
    else:
        tpl = "form_app/search_result.html"

    return render(request, tpl, {
        "products": products,
        "query": query,
    })


def review_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    #下書きがあれば取得
    draft = Review.objects.filter(
        user=request.user,
        product=product,
        is_draft=True
    ).first()
    
    reviews =Review.objects.filter(
        product=product,
        is_draft=False
    )
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "draft":
            #一時保存（is_valid通さない）
            review = draft if draft else Review()
            review.user =request.user
            review.product = product            
            review.goodpoint_comment = request.POST.get("goodpoint_comment","")
            review.badpoint_comment = request.POST.get("badpoint_comment","")
            review.rating = request.POST.get("rating")or None
            review.is_draft = True
            review.save()
            return redirect("form_app:my_page")
        
        #投稿(必ずバリデーション)
        form = ReviewForm(request.POST, request.FILES, instance=draft)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product            
            review.is_draft = False
            review.posted_at = timezone.now()
            review.save()
            return redirect("form_app:review_success")
        
    else:
        form = ReviewForm(instance=draft)
        
    return render(request, "form_app/review_create.html",{
        "form":form,
        "product":product,
        "reviews":reviews,
    })            
    
    
#レビュー確定後の処理
def review_submit(request,pk):
    review = Review.objects.get(pk=pk, user=request.user)
    
    review.is_draft = False
    review.posted_at=timezone.now() #投稿した日時
    review.save()
    
    return redirect("form_app:my_page")


#一時保存　(統一)
def review_draft_list(request):
    drafts = (Review.objects
        .filter(user=request.user,is_draft=True)
        .select_related("product")
        .order_by("-created_at")
    )
    
    return render(request, 
                  "form_app/review_draft_list.html",
                  {"drafts":drafts})
    
#下書きを編集画面に復元
def review_draft_edit(request, pk):
    review = get_object_or_404(
        Review, pk=pk, user=request.user,
        is_draft=True
    )
    
    if request.method == "POST":
        form =ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            
            if request.POST.get("action") == "submit":
                review.is_draft = False
                review.posted_at = timezone.now()
                review.save()
                return redirect("form_app:review_success")
            
            elif request.POST.get("action") == "draft":
                review.is_draft = True
                review.save()
                return redirect("form_app:draft_success")
                
    else:
        form = ReviewForm(instance=review)
        
    return render(request, "form_app/review_create.html",{
        "form":form,"product":review.product
    })

#一時保存の削除
def review_draft_delete(request, pk):
    draft = get_object_or_404(
        Review, pk=pk, user=request.user,
        is_draft=True
    )
    
    if request.method == "POST":
        draft.delete()
        
    return redirect("form_app:review_draft_list")


def review_edit(request, review_id):
    review=get_object_or_404(
        Review,
        id=review_id,
        user=request.user,
    )
    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            
            
            action = request.POST.get("action") 
            if action == "submit":
                review.is_draft = False
                if review.posted_ is None:
                    review.posted_at =timezone.now()
            elif action =="draft":
                review.is_draft = True
            
            review.save()
            if review.is_draft:
                return redirect("form_app:review_draft_list")
            else:
                return redirect("form_app:review_success")
            
    else:
        form = ReviewForm(instance=review)
        
    return render(
        request,
        "form_app/review_create.html",
        {"form":form, "product":review.product}
        )
       
@login_required
def edit_profile(request): #プロフィール修正    
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("form_app:my_page")
    
    else:
        profile_form = ProfileForm(instance=profile)
    
    user_form = UserReadOnlyForm(instance=request.user)
    
    return render(request, "form_app/edit_profile.html",
                  {
                      "user_form":user_form,
                      "profile_form":profile_form,
        })
 
    
#レビュー投稿    
def review_success(request):
    return render(request, 'form_app/review_success.html')


#レビュー削除ボタン
def review_delete(request, pk):
    if request.user.is_staff:
        review=get_object_or_404(Review, pk=pk)
    else:
        review=get_object_or_404(Review, 
        pk=pk,
        user=request.user,
        is_draft=False) #他人のレビュー修正防止
    
    review.delete()    
    return redirect("form_app:review_list")

@login_required
def my_page(request): #マイページ
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    reviews = (
        Review.objects
        .filter(user=request.user, is_draft=False)
        .order_by("-posted_at")[:1]
        .select_related("product")
    )
    
    latest_review=(
        Review.objects
        .filter(user=request.user,is_draft=False)
        .select_related("product") #投稿日時
        .order_by("-posted_at")
        .first()#１件のみ表示
    )

    return render(request, "form_app/my_page.html",{
        "profile":profile,"reviews": reviews,"review":latest_review,
    })

#レビュー投稿TOPの選択画面（一時保存か新規）
def review_entry(request):
    drafts=(
        Review.objects
        .filter(user=request.user, is_draft=True)
        .order_by("-created_at") 
    )
    
    return render(request, "form_app/review_entry.html",
                  {"drafts":drafts})

#マイページから遷移できるレビュー一覧
def review_list(request):
    reviews = (Review.objects
               .filter(user=request.user,
                       is_draft=False,
                       posted_at__isnull=False
                    )
               .select_related("product","user")
               .order_by("-posted_at")
               )
    return render(request, 
                  'form_app/review_list.html',
                  {'reviews':reviews})



#削除view
@user_passes_test(staff_only)
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect("form_app:product_list")

#商品一覧
@login_required
@user_passes_test(staff_only)
def product_list(request):
    products = Product.objects.all()
    return render(
        request,
        'form_app/product_list.html',
        {'products':products})