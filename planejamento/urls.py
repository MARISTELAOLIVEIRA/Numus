from django.urls import path
from . import views

urlpatterns = [
    path('definir_planejamento/', views.definir_planejamento, name="definir_planejamento"),
    path('update_valor_categoria/<int:id>', views.update_valor_categoria, name="update_valor_categoria"),
    path('salvar_valor_categoria/<int:id>', views.salvar_valor_categoria, name="salvar_valor_categoria"),
    path('salvar_valor_categoria_form/', views.salvar_valor_categoria_form, name="salvar_valor_categoria_form"),
    path('ver_planejamento/', views.ver_planejamento, name="ver_planejamento"),
    path('deletar_categoria/<int:id>/', views.deletar_categoria, name="deletar_categoria")
]