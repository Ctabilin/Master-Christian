from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('about/',views.about, name='about'),
    path('services/',views.services, name='services'),
    path('shop/',views.shop, name='shop'),
    path('login/',views.login_user, name='login'),
    path('logout/',views.logout_user, name='logout'),
    path('register/',views.register_user, name='register'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:foo>', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'),
    path('update_user/', views.update_user, name='update_user'),
    path('update_password/', views.update_password, name="update_password"),
    path('update_info/', views.update_info, name='update_info'),
    path('search/', views.search, name='search'),
    path('user_order/', views.user_order, name='user_order'),
    path('user_order_summary/', views.user_order_summary, name='user_order_summary'),
    path('customize/', views.customize, name='customize'),
    path('customize_tshirt/', views.customize_tshirt, name='customize_tshirt'),
    path('customize_bag/', views.customize_bag, name='customize_bag'),
    path('customize_fan/', views.customize_fan, name='customize_fan'),
    path('customize_mpad/', views.customize_mpad, name='customize_mpad'),
]