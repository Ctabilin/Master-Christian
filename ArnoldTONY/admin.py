from django.contrib import admin
from .models import Category,Customer,Product,Order,Profile
from django.contrib.auth.models import User

# Register your models here.

admin.site.register(Category)
admin.site.register(Customer)

admin.site.register(Order)
admin.site.register(Profile)

class ProfileInline(admin.StackedInline):
    model = Profile

class UserAdmin(admin.ModelAdmin):
    model = User
    field = ["username","first_name","last_name","email"]
    inlines = [ProfileInline]

admin.site.unregister(User)

admin.site.register(User, UserAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_sale', 'sale_price', 'user_design_image']
    search_fields = ['name', 'category__name']
    list_filter = ['is_sale', 'category']

admin.site.register(Product)