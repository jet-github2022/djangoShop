from django.contrib import admin
from .models import *

admin.site.register([Customer, Category, Cart, Product, CartProduct, Order, Admin, ProductImage])
