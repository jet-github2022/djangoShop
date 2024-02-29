from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.views.generic import TemplateView, View, CreateView, FormView, DetailView, ListView
from .forms import CheckoutForm, CustomerRegistrationForm, LoginForm, ProductForm, PasswordForgotForm, PasswordResetForm
from django.contrib.auth import authenticate, login, logout
from .models import *
from django.core.paginator import Paginator

from .utils import password_reset_token


class StoreMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)


class HomeView(StoreMixin, TemplateView):
    template_name = 'store/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = Product.objects.all().order_by("-id")
        paginator = Paginator(all_products, 4)
        page_number = self.request.GET.get("page")
        product_list = paginator.get_page(page_number)
        context["product_list"] = product_list
        return context


class CategoryView(StoreMixin, TemplateView):
    template_name = 'store/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class ProductDetailView(StoreMixin, TemplateView):
    template_name = 'store/product-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product = Product.objects.get(slug=url_slug)
        product.view_count += 1
        product.save()
        context['product'] = product
        return context


class AddCartView(StoreMixin, TemplateView):
    template_name = 'store/add-cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # get product id from requested url
        product_id = self.kwargs['pro_id']

        # get product
        product_obj = Product.objects.get(id=product_id)

        # check if cart exists
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(product=product_obj)

            # items already exists in cart
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            #     new item added to cart
            else:
                cartproduct = CartProduct.objects.create(cart=cart_obj, product=product_obj,
                                                         rate=product_obj.selling_price, quantity=1,
                                                         subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(cart=cart_obj, product=product_obj,
                                                     rate=product_obj.selling_price, quantity=1,
                                                     subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        return context


class MyCartView(StoreMixin, TemplateView):
    template_name = 'store/mycart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context["cart"] = cart
        return context


class ManageViewCart(StoreMixin, View):
    def get(self, request, *args, **kwargs):
        cartpro_id = self.kwargs["cartpro_id"]
        action = request.GET.get("action")
        cartpro_obj = CartProduct.objects.get(id=cartpro_id)
        cart_obj = cartpro_obj.cart

        if action == "inc":
            cartpro_obj.quantity += 1
            cartpro_obj.subtotal += cartpro_obj.rate
            cartpro_obj.save()
            cart_obj.total += cartpro_obj.rate
            cart_obj.save()

        elif action == "dcr":
            cartpro_obj.quantity -= 1
            cartpro_obj.subtotal -= cartpro_obj.rate
            cartpro_obj.save()
            cart_obj.total -= cartpro_obj.rate
            cart_obj.save()
            if cartpro_obj.quantity == 0:
                cartpro_obj.delete()

        elif action =="rmv":
            cart_obj.total -= cartpro_obj.subtotal
            cartpro_obj.save()
            cartpro_obj.delete()
        else:
            return redirect("store:mycart")


class EmptyCartView(StoreMixin, View):
    def get(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect("store:mycart")


class CheckoutView(StoreMixin, CreateView):
    template_name = 'store/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy("store:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/login/?next=/check-out/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context["cart"] = cart_obj
        return context

    def form_valid(self, form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session["cart_id"]
            pm = form.cleaned_data.get("payment_method")
            order = form.save()
            if pm == "Paystack":
                return redirect(reverse("store:paystackrequest"))
        else:
            return redirect("store:home")
        return super().form_valid(form)


class PaystackRequestView(View):
    def get(self, request, *args, **kwargs):
        context = {
        }
        return render(request, "store/paystackrequest.html", context)


class CustomerRegistration(CreateView):
    template_name = "store/registration.html"
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy("store:home")

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("store:home")


class LoginView(FormView):
    template_name = "store/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("store:home")

    # form_valid method is a type of post method and its available in createview, formview and upadateview
    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=uname, password=pword)
        if usr is not None and Customer.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class,
                                                             "error": "Invalid Credentials"})

        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


class AboutView(StoreMixin, TemplateView):
    template_name = 'store/about.html'


class ContactView(StoreMixin, TemplateView):
    template_name = 'store/contact.html'


class ProfileView(TemplateView):
    template_name = "store/profile.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context["customer"] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")
        context["orders"] = orders
        return context


class OrderDetailView(DetailView):
    template_name = "store/orderdetail.html"
    model = Order
    context_object_name = "order_obj"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id = self.kwargs["pk"]
            order = Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect("store:profile")
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)


class ForgotPasswordView(FormView):
    template_name = "store/forgotpassword.html"
    form_class = PasswordForgotForm
    success_url = "/forgot-password/?m=s"

    def form_valid(self, form):
        # get email from user
        email = form.cleaned_data.get("email")
        # get current host ip/domain
        url = self.request.META["HTTP_HOST"]
        # get customer and user
        customer = Customer.objects.get(user__email=email)
        user = customer.user
        # send mail to the user with email
        text_content = "Please click the link below to reset your password."
        html_content = url + "/password-reset/" + email + \
            "/" + password_reset_token.make_token(user) + "/"
        send_mail(
            "Password Reset Link | Django Ecommerce",
            text_content + html_content,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return super().form_valid(form)


class PasswordResetView(FormView):
    template_name = "store/passwordreset.html"
    form_class = PasswordResetForm
    success_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        email = self.kwargs.get("email")
        user = User.objects.get(email=email)
        token = self.kwargs.get("token")
        if user is not None and password_reset_token.check_token(user, token):
            pass
        else:
            return redirect(reverse("store:forgotpassword") + "?m=e")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        password = form.cleaned_data["new password"]
        email = self.kwargs.get("email")
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        return super().form_valid(form)


# admin pages
class AdminLoginView(FormView):
    template_name = "adminpages/admin.html"
    form_class = LoginForm
    success_url = reverse_lazy("store:adminhome")

    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=uname, password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class,
                                                             "error": "Invalid Credentials"})
        return super().form_valid(form)


class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/admin-login/")
        return super().dispatch(request, *args, **kwargs)


class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name = "adminpages/adminhome.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pendingorders"] = Order.objects.filter(order_status="Order Received").order_by("-id")
        return context


class AdminOderDetailView(AdminRequiredMixin, DetailView):
    template_name = "adminpages/adminorderdetail.html"
    model = Order
    context_object_name = "order_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allstatus'] = ORDER_STATUS
        return context


class AllOderView(AdminRequiredMixin, ListView):
    template_name = "adminpages/orderlist.html"
    queryset = Order.objects.all().order_by("-id")
    context_object_name = "allorders"


class AdminOrderStatusChangeView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order_obj = Order.objects.get(id=order_id)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy("store:adminorderdetail", kwargs={"pk": order_id}))


class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = "adminpages/adminproductlist.html"
    queryset = Product.objects.all().order_by("-id")
    context_object_name = "allproducts"


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name = 'adminpages/adminproductcreate.html'
    form_class = ProductForm
    success_url = reverse_lazy("store:productlist")

    # def form_valid(self, form):
    #     p = form.save()
    #     images = self.request.FILES.getlist("more_images")
    #     for i in images:
    #         ProductImage.objects.create(product=p, image=i)
    #     return super().form_valid(form)


class SearchProductView(TemplateView):
    template_name = "store/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get("keyword")
        results = Product.objects.filter(Q(title__contains=kw) | Q(description__icontains=kw))
        context["results"] = results
        return context





















