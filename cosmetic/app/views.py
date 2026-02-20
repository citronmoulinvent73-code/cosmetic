from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg, Q, Exists, OuterRef, IntegerField, Value, BooleanField
from django.db.models.functions import Cast, Round
from django.core.exceptions import PermissionDenied
from functools import wraps

from .forms import LoginForm, UserForm, CosmeForm, ReviewForm, UserReadOnlyForm, ProfileForm
from .models import Product, Review, ReviewFavorite, Profile, SKIN_CHOICES, AGE_CHOICES


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()            
            auth_login(request, user)
            return redirect(reverse('form_app:home'))
        
    else:
        form = LoginForm()
    
    return render(request, 'form_app/login.html', {'form':form})


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            #未ログインはログイン画面へ（LOGIN_URLへ）
            return redirect("form_app:login")
        if not request.user.is_staff:
            #ログイン済み一般ユーザーは403
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped



def product_detail(request, pk):
    product = get_object_or_404(Product,pk=pk)
    
    reviews = Review.objects.filter(
        product=product,
        is_draft=False
        )
    
    if request.user.is_authenticated:
        reviews = reviews.annotate(
            is_favorited=Exists(
                ReviewFavorite.objects.filter(
                    review=OuterRef("pk"),
                    user=request.user)
                )
            )
    else:
        reviews = reviews.annotate(
            is_favorited = Value(False, output_field=BooleanField())
        )
    
    return render(
        request,
        'form_app/product_detail.html',
        {'product':product,"reviews":reviews})


def build_popular_ranking_qs(category=None, skin_type=None, age=None):           
    filters = Q(reviews__is_draft=False, reviews__posted_at__isnull=False)

    if skin_type:
        filters &= Q(reviews__skin_type=skin_type)
    if age:
        filters &= Q(reviews__age=age)
        
    qs = Product.objects.all()
    if category is not None:
        qs = qs.filter(category=category)
        
    return (
        qs.annotate(#集計
            review_count=Count("reviews", filter=filters, distinct=True),
            avg_rating=Avg("reviews__rating", filter=filters),
        )
        .filter(review_count__gt=0) #0件商品を除外
        .order_by("-review_count","-avg_rating")#並び替え
    )


def ranking(request, category=None):   
    skin_type = request.GET.get("skin_type")
    age = request.GET.get("age")
    
    CATEGORY_LABEL = dict(CosmeForm.CATEGORY_CHOICES)

    if category is None:
        category_label = "総合人気"
    else:
        category_label = f"{CATEGORY_LABEL.get(category, category)}人気"
        
    products = build_popular_ranking_qs(category=category, skin_type=skin_type, age=age)
           
    return render(request,"form_app/ranking.html",{
        "products": products,
        "products_count": products.count(),
        "category_label": category_label,
        "category": category,
        "skin_type": skin_type,
        "age": age,
        "SKIN_CHOICES": SKIN_CHOICES,
        "AGE_CHOICES": AGE_CHOICES,
        }
    )


def home(request):
    ranking_products = build_popular_ranking_qs()[:5]
    
    reviews = Review.objects.all()

    if request.user.is_authenticated:
        reviews = reviews.annotate(
            is_favorited=Exists(
                ReviewFavorite.objects.filter(
                    review=OuterRef("pk"),
                    user=request.user)
                )
            )
    else:
        reviews = reviews.annotate(
            is_favorited = Value(False, output_field=BooleanField())
        )
    
    return render(
        request, 'form_app/home.html',
        {'ranking_products':ranking_products,
         'reviews':reviews})
    
    
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
    category_label = CATEGORY_LABEL.get(category, category)
    
    products = build_popular_ranking_qs(category=category)
    
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
@login_required
def review_favorite(request, review_id):
   
    review=get_object_or_404(Review, id=review_id)
    
    favorite,created = ReviewFavorite.objects.get_or_create(
        user=request.user,
        review=review
    )
    if not created:
        favorite.delete()
        
    return redirect(request.META.get("HTTP_REFERER","/"))

#お気に入りタブ
@login_required(login_url="form_app:login")
def favorite_review_list(request):
    favorites = ReviewFavorite.objects.filter(
        user=request.user
    ).select_related('review','review__product')
    
    return render(
        request,
        'form_app/favorite_review_list.html',
        {'favorites':favorites})


@login_required
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
    
@staff_required
def admin_my_page(request):   
    return render(request, "form_app/admin_my_page.html")

#商品登録
@staff_required
def product_create(request):
    if request.method == 'POST':
        form = CosmeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('form_app:product_create_success')
    else:
        form =CosmeForm()
            
    return render(request,'form_app/product_create.html',{'form':form})

@staff_required
def product_create_success(request):
    return render(request,'form_app/product_create_success.html')


#商品検索
def product_search(request):
    query = request.GET.get("q","")
    products = Product.objects.none()
    
    if query:
        published = Q(reviews__is_draft=False, reviews__posted_at__isnull=False)
        
        products = (
            Product.objects
            .filter(cosme_name__icontains=query)
            .annotate(
                avg_rating=Avg('reviews__rating', filter=published),
                avg_rating_int=Cast(Round(Avg('reviews__rating', filter=published)),IntegerField()),
                review_count=Count('reviews', filter=published, distinct=True),
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


@login_required
def review_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    profile, _ = Profile.objects.get_or_create(user=request.user)

    
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
        
        #下書き
        if action == "draft":
            #一時保存（is_valid通さない）
            review = draft if draft else Review()
            review.user =request.user
            review.product = product
            
            review.skin_type = profile.skin_type or ""
            review.age = profile.age or ""
                       
            review.goodpoint_comment = request.POST.get("goodpoint_comment","")
            review.badpoint_comment = request.POST.get("badpoint_comment","")
            
            if request.FILES.get("image"):
                review.image = request.FILES["image"]

            #未選択OK
            r = request.POST.get("rating")
            review.rating = int(r) if r else None
            
            review.is_draft = True
            review.save()
            if request.user.is_staff:
                return redirect("form_app:admin_my_page")
            else:
                return redirect("form_app:my_page")
            
            
        
        #投稿(必ずバリデーション)
        form = ReviewForm(request.POST, request.FILES, instance=draft, request=request)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product            
            review.is_draft = False
            review.posted_at = timezone.now()
            
            review.skin_type = profile.skin_type or ""
            review.age = profile.age or ""

            review.save()
            return redirect("form_app:review_success")
        
    else:
        form = ReviewForm(instance=draft, request=request)
        
    return render(request, "form_app/review_create.html",{
        "form":form,
        "product":product,
        "reviews":reviews,
    })            
    
    
#レビュー確定後の処理
@login_required
def review_submit(request,pk):
    review = Review.objects.get(pk=pk, user=request.user)
    
    review.is_draft = False
    review.posted_at=timezone.now() #投稿した日時
    review.save()
    
    return redirect("form_app:my_page")


#一時保存　(統一)
@login_required
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
@login_required
def review_draft_edit(request, pk):
    review = get_object_or_404(
        Review, pk=pk, user=request.user,
        is_draft=True
    )
    
    if request.method == "POST":
        form =ReviewForm(request.POST, request.FILES, instance=review, request=request)
        
        action = request.POST.get("action")
        
        #下書き保存はバリエーション通さず
        if action =="draft":
            review.goodpoint_comment = request.POST.get("goodpoint_comment","")
            review.badpoint_comment = request.POST.get("badpoint_comment","")
            review.rating = request.POST.get("rating") or None
            
            if request.FILES.get("image"):
                review.image = request.FILES["image"]

            review.is_draft = True
            review.save()
            return redirect("form_app:review_draft_list")
        
        #投稿
        if form.is_valid():
            review = form.save(commit=False)            
            review.is_draft = False
            review.posted_at = timezone.now()
            review.save()
            return redirect("form_app:review_success")
                          
    else:
        form = ReviewForm(instance=review, request=request)
        
    return render(request, "form_app/review_create.html",{
        "form":form,"product":review.product
    })

#一時保存の削除
@login_required
def review_draft_delete(request, pk):
    draft = get_object_or_404(
        Review, pk=pk, user=request.user,
        is_draft=True
    )
    
    if request.method == "POST":
        draft.delete()
        
    return redirect("form_app:review_draft_list")

@login_required
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
                if review.posted_at is None:
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
@login_required
def review_success(request):
    return render(request, 'form_app/review_success.html')


#レビュー削除ボタン
@login_required
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
@login_required
def review_entry(request):
    drafts=(
        Review.objects
        .filter(user=request.user, is_draft=True)
        .order_by("-created_at") 
    )
    
    return render(request, "form_app/review_entry.html",
                  {"drafts":drafts})

#マイページから遷移できるレビュー一覧
@login_required
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


#商品編集,商品更新
@staff_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = CosmeForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return render(request, "form_app/product_create_success.html", {
                "message": "商品を更新しました",
            })    
    else:
        form = CosmeForm(instance=product)

    return render(request, 'form_app/product_edit.html',
                  {'form': form,
                   'product':product,})

#商品削除view
@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect("form_app:product_list")

#商品一覧
@staff_required
def product_list(request):
    products = Product.objects.all()
    return render(
        request,
        'form_app/product_list.html',
        {'products':products})
    

def portfolio(request):
#ポートフォリオ表示用（既存アプリとは独立）
    return render(request, "portfolio/index.html")