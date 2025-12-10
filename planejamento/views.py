from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import constants
from perfil.models import Categorias
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def definir_planejamento(request):
    categorias = Categorias.objects.filter(user=request.user)
    return render(request, 'definir_planejamento.html', {'categorias': categorias})

@csrf_exempt
def update_valor_categoria(request, id):
    novo_valor = json.load(request)['novo_valor']
    categoria = Categorias.objects.get(id=id, user=request.user)
    categoria.valor_planejado = novo_valor
    categoria.save()
    return JsonResponse({'Status': 'Sucesso'})

def ver_planejamento(request):
    categorias = Categorias.objects.filter(user=request.user)
    return render(request, 'ver_planejamento.html', {'categorias': categorias})


def salvar_valor_categoria(request, id):
    if request.method == 'POST':
        novo_valor = request.POST.get('novo_valor', '').strip()
        try:
            valor = float(novo_valor) if novo_valor not in (None, '') else 0
        except ValueError:
            valor = 0

        categoria = Categorias.objects.get(id=id, user=request.user)
        categoria.valor_planejado = valor
        categoria.save()
        messages.add_message(request, constants.SUCCESS, 'Valor planejado salvo com sucesso.')

    # After saving, show the planning overview so the user can see the updated values
    return redirect('ver_planejamento')


def salvar_valor_categoria_form(request):
    # Accepts POST with 'categoria_id' and 'novo_valor' from the top form
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        novo_valor = request.POST.get('novo_valor', '').strip()
        if not categoria_id:
            messages.add_message(request, constants.ERROR, 'Selecione uma categoria.')
            return redirect('definir_planejamento')

        try:
            valor = float(novo_valor) if novo_valor not in (None, '') else 0
        except ValueError:
            messages.add_message(request, constants.ERROR, 'Valor inválido.')
            return redirect('definir_planejamento')

        try:
            categoria = Categorias.objects.get(id=int(categoria_id), user=request.user)
            categoria.valor_planejado = valor
            categoria.save()
            messages.add_message(request, constants.SUCCESS, 'Valor planejado salvo com sucesso.')
        except Categorias.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'Categoria não encontrada.')

    # After saving from the top form, show the planning overview
    return redirect('ver_planejamento')


def deletar_categoria(request, id):
    if request.method == 'POST':
        try:
            categoria = Categorias.objects.get(id=id, user=request.user)
            categoria_nome = categoria.categoria
            categoria.delete()
            messages.add_message(request, constants.SUCCESS, f'Categoria "{categoria_nome}" deletada com sucesso.')
        except Categorias.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'Categoria não encontrada.')
    
    return redirect('definir_planejamento')