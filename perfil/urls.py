from django.urls import path
from . import views

urlpatterns = [
    path('landing/', views.landing, name="landing"),
    path('login/', views.login_view, name="login"),
    path('register/', views.register_view, name="register"),
    path('logout/', views.logout_view, name="logout"),
    path('home/', views.home, name="home"),
    path('perfil/', views.perfil_usuario, name="perfil"),
    path('editar_perfil/', views.editar_perfil, name="editar_perfil"),
    path('configuracoes/', views.configuracoes, name="configuracoes"),
    path('gerenciar/', views.gerenciar, name="gerenciar"),
    path('cadastrar_banco/', views.cadastrar_banco, name="cadastrar_banco"),
    path('deletar_banco/<int:id>', views.deletar_banco, name="deletar_banco"),
    path('cadastrar_categoria/', views.cadastrar_categoria, name="cadastrar_categoria"),
    path('update_categoria/<int:id>', views.update_categoria, name="update_categoria"),
    path('categorias/', views.categorias, name="categorias"),
    path('deletar_categoria/<int:id>', views.deletar_categoria, name="deletar_categoria"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('relatorios/', views.relatorios, name="relatorios"),
    path('relatorios/export_csv/', views.relatorios_export_csv, name='relatorios_export_csv'),
    path('relatorios/export_pdf/', views.relatorios_export_pdf, name='relatorios_export_pdf'),
    path('adicionar_valor/', views.adicionar_valor, name="adicionar_valor"),
    path('adicionar_entrada/', views.adicionar_entrada, name="adicionar_entrada"),
    path('adicionar_saida/', views.adicionar_saida, name="adicionar_saida"),
]