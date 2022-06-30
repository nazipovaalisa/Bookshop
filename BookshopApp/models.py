
from django.db import models


from django.conf import settings
from django.db.models.signals import pre_save
from django.contrib.contenttypes.models import ContentType


class Genre(models.Model):
    """Жанр"""

    name = models.CharField(max_length=100, verbose_name='Название жанра')
    slug = models.SlugField(verbose_name='URL')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Book(models.Model):
    """Книга"""

    name = models.CharField(max_length=100, verbose_name='Название книги')
    slug = models.SlugField(verbose_name='URL')
    image = models.ImageField(upload_to="images/", height_field="image_height", width_field="image_width",
                              verbose_name = 'Изображение')
    image_height = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
        default="525"
    )
    image_width = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
        default="260"
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name='Жанр')
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена', default = 0)
    stock = models.IntegerField(default=1, verbose_name='Наличие на складе')
    out_of_stock = models.BooleanField(default=False, verbose_name='Нет в наличии')

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

class CartProduct(models.Model):
    """Продукт корзины"""

    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE)
    book = models.ForeignKey( Book, on_delete=models.CASCADE, verbose_name='Книга')
    qty = models.PositiveIntegerField(default=1, verbose_name='Количество')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Cумма')

    def __str__(self):
        return f"Книга: {self.book.name} (для корзины)"

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.book.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Книга в корзине'
        verbose_name_plural = 'Книги в корзине'


class Cart(models.Model):
    """Корзина"""

    owner = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    books = models.ManyToManyField(
        CartProduct, blank=True, related_name='related_cart', verbose_name='Книги для корзины'
    )
    total_products = models.IntegerField(default=0, verbose_name='Общее кол-во')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Сумма', null=True, blank=True)
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    def products_in_cart(self):
        return [c.book for c in self.books.all()]

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

class Order(models.Model):
    """Заказ пользователя"""

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка курьером')
    )

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ получен покупателем')
    )


    customer = models.ForeignKey('Customer', verbose_name='Покупатель', related_name='orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    status = models.CharField(max_length=100, verbose_name='Статус заказа', choices=STATUS_CHOICES, default=STATUS_NEW)
    cart = models.ForeignKey(Cart, verbose_name='Корзина', null=True, blank=True, on_delete=models.CASCADE)
    address = models.CharField(max_length=1024, verbose_name='Адрес')
    buying_type = models.CharField(max_length=100, verbose_name='Тип доставки', choices=BUYING_TYPE_CHOICES)
    created_at = models.DateField(verbose_name='Дата создания заказа', auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

class Customer(models.Model):
    """Покупатель"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='Пользователь', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False, verbose_name='Активный?')
    customer_orders = models.ManyToManyField(
        Order, blank=True, verbose_name='Заказы покупателя', related_name='related_customer'
    )
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


def check_previous_qty(instance, **kwargs):
    try:
        product = Book.objects.get(id=instance.id)
    except Book.DoesNotExist:
        return None
    instance.out_of_stock = True if not product.stock else False

pre_save.connect(check_previous_qty, sender=Book)
