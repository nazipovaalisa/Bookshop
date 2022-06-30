from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect
from django import views
from django.http import HttpResponseRedirect
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.http import urlsafe_base64_decode

from .models import Book, CartProduct, Customer, Genre

from .forms import LoginForm, RegistrationForm, OrderForm

from .mixins import CartMixin

from .utils import send_email_verify
from utils import recalc_cart


User=get_user_model()

class BaseView(CartMixin, views.View): #рендеринг главной страницы

    def get(self, request, *args, **kwargs):
        books = Book.objects.all()
        genres = Genre.objects.all()
        context = {
            'cart': self.cart,
            'genres': genres,
            'books': books,

        }
        return render(request, 'base.html', context)



class GenreView(CartMixin, views.View):

    def get(self,request, *args, **kwargs):
        gen_selected = self.kwargs['genre_slug']
        genres = Genre.objects.all()
        books = Book.objects.filter(genre__slug=gen_selected)
        context = {
            'cart': self.cart,
            'genres': genres,
            'books': books,
            'gen_selected': Genre.objects.get(slug=gen_selected)
        }
        return render(request, 'base.html', context)


class LoginView(views.View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                customer = Customer.objects.get(user=user)
                if not customer.is_active:
                    message = 'Подтвердите вашу учетную запись!'
                    messages.add_message(request, messages.INFO, message)
                    return HttpResponseRedirect('/')
                login(request, user)
                return HttpResponseRedirect('/')
        context = {
            'form': form
        }
        return render(request, 'login.html', context)


class RegistrationView(views.View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            send_email_verify(request, user)
            return redirect('confirm_email')
        context = {
            'form': form
        }
        return render(request, 'registration.html', context)

class EmailVerifyView(views.View):

    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            customer = Customer.objects.get(user=user)
            customer.is_active = True
            customer.save()
            login(request, user)
            message = 'Вы успешно зарегистрированы!'
            messages.add_message(request, messages.INFO, message)
            return HttpResponseRedirect('/')
        return redirect('invalid_verify')

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError,
                User.DoesNotExist, ValidationError):
            user = None
        return user

class InvalidVerify(views.View):

    def get(self, request):
        return render(request, 'invalid_verify.html')

class ConfirmView(views.View):

    def get(self, request):
        return render(request, 'confirm_email.html')

class AccountView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.filter(user=request.user).first()
        context = {
            'customer': customer,
            'cart': self.cart
        }
        return render(request, 'account.html', context)


class CartView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        return render(request, 'cart.html', {"cart": self.cart})


class AddToCartView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        book = Book.objects.get(slug=book_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, book=book
        )
        if created:
            self.cart.books.add(cart_product)
        recalc_cart(self.cart)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class DeleteFromCartView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        book = Book.objects.get(slug=book_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, book = book
        )
        self.cart.books.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class ChangeQTYView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        book = Book.objects.get(slug=book_slug)
        type = kwargs.get('type')
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, book=book
        )
        if type == 1:
            cart_product.qty += 1
        else:
            cart_product.qty -= 1
        cart_product.save()
        recalc_cart(self.cart)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class CheckoutView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'form': form,
        }
        return render(request, 'checkout.html', context)

class MakeOrderView(CartMixin, views.View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            out_of_stock = []
            more_than_on_stock = []
            out_of_stock_message = ""
            more_than_on_stock_message = ""
            for item in self.cart.books.all():
                if not item.book.stock:
                    out_of_stock.append(' - '.join([
                        item.book.name
                    ]))
                if item.book.stock and item.book.stock < item.qty:
                    more_than_on_stock.append(
                        {'book': ' - '.join([item.book.name]),
                         'stock': item.book.stock, 'qty': item.qty}
                    )
            if out_of_stock:
                out_of_stock_products = ', '.join(out_of_stock)
                out_of_stock_message = f'Товара уже нет в наличии: {out_of_stock_products}. \n'

            if more_than_on_stock:
                for item in more_than_on_stock:
                    more_than_on_stock_message += f'Товар: {item["book"]}. ' \
                                                  f'В наличии: {item["stock"]}. ' \
                                                  f'Заказано: {item["qty"]}\n'
            error_message_for_customer = ""
            if out_of_stock:
                error_message_for_customer = out_of_stock_message + '\n'
            if more_than_on_stock_message:
                error_message_for_customer += more_than_on_stock_message + '\n'

            if error_message_for_customer:
                messages.add_message(request, messages.INFO, error_message_for_customer)
                return HttpResponseRedirect('/checkout/')

            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.save()

            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)

            for item in self.cart.books.all():
                item.book.stock -= item.qty
                item.book.save()

            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Следите за статусом')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')


