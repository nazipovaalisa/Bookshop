from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *


@admin.register(Book)
class ProductAdmin(admin.ModelAdmin):

    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('show_image',)

    def show_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="60" height="90">')

    show_image.short_description = "Изображение"


@admin.register(Genre)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)



