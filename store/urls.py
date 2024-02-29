from django.urls import path
from .views import *

app_name = "store"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("categories/", CategoryView.as_view(), name="all-categories"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),

    path("add-cart-<int:pro_id>/", AddCartView.as_view(), name="add-cart"),
    path("my-cart/", MyCartView.as_view(), name="mycart"),
    path("manage-cart/<int:cartpro_id>/", ManageViewCart.as_view(), name="managecart"),
    path("empty-cart/", EmptyCartView.as_view(), name="emptycart"),
    path("check-out/", CheckoutView.as_view(), name="checkout"),
    path("paystack-request", PaystackRequestView.as_view(), name="paystackrequest"),
    path("search/", SearchProductView.as_view(), name="search"),

    # customer side
    path("registration/", CustomerRegistration.as_view(), name="registration"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/-<int:pk>/", OrderDetailView.as_view(), name="orderdetail"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgotpassword"),
    path("password-reset/<email>/<token>/", PasswordResetView.as_view(), name="passwordreset"),

    # admin side
    path("admin-login", AdminLoginView.as_view(), name="adminlogin"),
    path("admin-home", AdminHomeView.as_view(), name="adminhome"),
    path("admin-order-detail/<int:pk>/", AdminOderDetailView.as_view(), name="adminorderdetail"),
    path("admin-all-orders/", AllOderView.as_view(), name="allorderlist"),
    path("admin-order-<int:pk>-change/", AdminOrderStatusChangeView.as_view(), name="statuschange"),
    path("admin-product/list/", AdminProductListView.as_view(), name="productlist"),
    path("admin-product/add/", AdminProductCreateView.as_view(), name="productcreate"),
]







