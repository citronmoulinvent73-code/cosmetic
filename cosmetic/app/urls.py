from django.urls import path,reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from . import views
from .views import admin_my_page
from .forms import CustomPasswordChangeForm

app_name = 'form_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('ranking/', views.ranking, name='ranking_all'),
    path('ranking/<str:category>/', views.ranking, name='ranking_by_category'),
    
    path('favorites/', views.favorite_review_list, name='favorite_review_list'),
    path('my_page/', views.my_page, name='my_page'),   
    path('logout/', views.user_logout, name='logout'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('password_change/', 
         auth_views.PasswordChangeView.as_view(
             template_name="form_app/password_change.html",
             form_class=CustomPasswordChangeForm,
             success_url=reverse_lazy('form_app:my_page'),
             ),
         name='password_change',
         ),

    path('reviews/', views.review_list, name='review_list'),
    #レビュー投稿の入り口
    path('review/entry/', views.review_entry, name='review_entry'),
    #実際のレビュー作成
    path('review/create/<int:product_id>/', views.review_create, name='review_create'),
    path('review_success/',views.review_success, name='review_success'),
    path('review/<int:pk>/delete/',views.review_delete, name='review_delete'),
    path('review_drafts/',views.review_draft_list, name='review_draft_list'),
    path('review_drafts/<int:pk>/edit/',views.review_draft_edit, name='review_draft_edit'),
    path('review_drafts/<int:pk>/delete/',views.review_draft_delete, name='review_draft_delete'),
    path('review/edit/<int:review_id>',views.review_edit, name='review_edit'),
    path('review/<int:review_id>/favorites/',views.review_favorite,name='review_favorite'),
    
    path('category/<str:category>/', views.category_product_list, name='category_product_list'),
    path('search_result/', views.search_result_view, name='search_result'),
    path('admin_my_page/', views.admin_my_page, name='admin_my_page'),
    path('product_create/', views.product_create, name='product_create'),
    path('product/create/success/', views.product_create_success, name='product_create_success'),
    path('products/search/', views.product_search, name='product_search'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    #ポートフォリオ表示用（既存アプリとは独立）
    path('portfolio/', views.portfolio, name='portfolio'),    
]

