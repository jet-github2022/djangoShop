from django import forms
from .models import Order, Customer, Product
from django.contrib.auth.models import User


class CheckoutForm(forms.ModelForm):
    ordered_by = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    mobile = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Order
        fields = ["ordered_by", "shipping_address", "mobile", "email", "payment_method"]


class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Customer
        fields = ["username", "full_name", "address", "password", "email"]

    def clean_username(self):
        myname = self.cleaned_data.get("username")
        if User.objects.filter(username=myname).exists():
            raise forms.ValidationError("username already exists.")

        return myname


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProductForm(forms.ModelForm):
    # more_images = forms.FileField(required=False, widget=forms.FileInput(attrs={
    #     "class": " form-control",
    #     "allow_multiple": True
    # }))

    class Meta:
        model = Product
        fields = ["title", "slug", "category", "image", "marked_price", "selling_price", "description",
                  "warranty", "return_policy"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product title here...."
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product slug here...."
            }),
            "category": forms.Select(attrs={
                "class": "form-control",
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "marked_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product marked price here...."
            }),
            "selling_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product selling price here...."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter the product description...."
            }),
            "warranty": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product warranty...."
            }),
            "return_policy": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product return policy...."
            })
        }


class PasswordForgotForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Enter user email"
    }))

    def clean_email(self):
        e = self.cleaned_data.get("email")
        if Customer.objects.filter(user__email=e).exists():
            pass
        else:
            raise forms.ValidationError("Customer with this account does not exists...")
        return e


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "autocomplete": "new-password",
        "placeholder": "Enter New Password",
    }), label="New Password")
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "autocomplete": "new-password",
        "placeholder": "Confirm New Password",
    }), label=" Confirm New Password")

    def clean_confirm_new_password(self):
        new_password = self.cleaned_data.get("new password")
        confirm_new_password = self.cleaned_data.get("confirm_new_password")
        if new_password != confirm_new_password:
            raise forms.ValidationError(
                "New Password did not match!"
            )
        return confirm_new_password







