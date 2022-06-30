from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import BaseView,  AddToCartView, ChangeQTYView, DeleteFromCartView, LoginView, \
    RegistrationView, AccountView, CartView, CheckoutView, MakeOrderView, GenreView, EmailVerifyView, ConfirmView, InvalidVerify

urlpatterns = [
    path('add-to-cart/<str:book_slug>/', AddToCartView.as_view(), name='add_to_cart'),
    path('delete-from-cart/<str:book_slug>/', DeleteFromCartView.as_view(), name='delete_from_cart'),
    path('change-qty/<str:book_slug>/<int:type>/', ChangeQTYView.as_view(), name='change_gty'),
    path('', BaseView.as_view(), name='base'),
    path('category/<slug:genre_slug>/', GenreView.as_view(), name='genre'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('verify_email/<uidb64>/<token>', EmailVerifyView.as_view(), name='verify_email'),
    path('confirm_email/', ConfirmView.as_view(), name='confirm_email'),
    path('invalid_verify/', InvalidVerify.as_view(), name='invalid_verify'),
    path('account/', AccountView.as_view(), name='account'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('make-order/', MakeOrderView.as_view(), name='make-order'),
]