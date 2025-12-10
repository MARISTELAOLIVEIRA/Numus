from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
import csv
from .models import Conta, Categorias, UserProfile
from django.contrib import messages
from django.contrib.messages import constants
from .utils import calcula_total, calcula_equilibrio_financeiro
from extrato.models import Valores
from datetime import datetime
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


def get_evolution_data(year: int, user):
    """Return monthly labels and totals for entradas and gastos for a given year."""
    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    meses_labels = []
    entradas_data = []
    gastos_data = []

    for m in range(1, 13):
        meses_labels.append(meses_nomes[m - 1])

        entradas_total = Valores.objects.filter(user=user, data__year=year, data__month=m, tipo='E').aggregate(total=Sum('valor'))
        gastos_total = Valores.objects.filter(user=user, data__year=year, data__month=m, tipo='S').aggregate(total=Sum('valor'))

        entradas_data.append(float(entradas_total['total'] or 0))
        gastos_data.append(float(gastos_total['total'] or 0))

    return meses_labels, entradas_data, gastos_data

def login_view(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('email')  # O template usa 'email'
        password = request.POST.get('password')
        
        # Tentar autenticar com email ou username
        user = None
        try:
            # Primeiro tenta encontrar por username
            user = authenticate(request, username=email_or_username, password=password)
            if user is None and '@' in email_or_username:
                # Se falhar e for email, tenta encontrar o usuário por email
                user_by_email = User.objects.filter(email=email_or_username).first()
                if user_by_email:
                    user = authenticate(request, username=user_by_email.username, password=password)
        except:
            pass
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.add_message(request, constants.ERROR, 'Usuário/Email ou senha inválidos.')
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')  # O template usa 'nome'
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not nome or not nome.strip():
            messages.add_message(request, constants.ERROR, 'Nome é obrigatório.')
            return redirect('register')
        
        if password != password_confirm:
            messages.add_message(request, constants.ERROR, 'As senhas não coincidem.')
            return redirect('register')
        
        if User.objects.filter(username=nome).exists():
            messages.add_message(request, constants.ERROR, 'Esse usuário já existe.')
            return redirect('register')
        
        try:
            user = User.objects.create_user(username=nome, email=email, password=password)
            messages.add_message(request, constants.SUCCESS, 'Usuário cadastrado com sucesso! Faça login.')
            return redirect('login')
        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Erro ao cadastrar: {str(e)}')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    return redirect('landing')

def landing(request):
    return render(request, 'index.html')

@login_required(login_url='login')
def home(request):
    current_year = datetime.now().year
    current_month = datetime.now().month
    meses_labels, entradas_data, gastos_data = get_evolution_data(current_year, request.user)

    valores = Valores.objects.filter(user=request.user, data__month=current_month)
    entradas = valores.filter(tipo='E')
    saidas = valores.filter(tipo='S')

    total_entradas = calcula_total(entradas, 'valor')
    total_saidas = calcula_total(saidas, 'valor')

    contas = Conta.objects.filter(user=request.user)
    total_contas = calcula_total(contas, 'valor')
    
    # Calcular saldo geral: Saldo das contas + Entradas - Saídas
    saldo_geral = float(total_contas) + float(total_entradas) - float(total_saidas)

    percentual_gastos_essenciais, percentual_gastos_nao_essenciais = calcula_equilibrio_financeiro(request.user)

    # Gastos por categoria (mês atual)
    queryset = Valores.objects.filter(user=request.user, data__year=current_year, data__month=current_month, tipo='S')
    agg = queryset.values('categoria__categoria').annotate(total=Sum('valor')).order_by('-total')

    labels = []
    values = []
    for item in agg:
        labels.append(item['categoria__categoria'] or 'Sem categoria')
        total = item['total'] or 0
        try:
            values.append(float(total))
        except Exception:
            values.append(0.0)

    # generate colors (cycle palette)
    palette = ['#10B981', '#06b6d4', '#f97316', '#ef4444', '#60a5fa', '#7c3aed', '#f59e0b', '#14b8a6']
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    # Get user's categorias for planning display
    categorias = Categorias.objects.filter(user=request.user)

    return render(request, 'home.html', {
        'contas' : contas, 
        'total_contas' : total_contas,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_geral': round(saldo_geral, 2),
        'percentual_gastos_essenciais': int(percentual_gastos_essenciais),
        'percentual_gastos_nao_essenciais': int(percentual_gastos_nao_essenciais),
        'meses_labels': meses_labels,
        'entradas_data': entradas_data,
        'gastos_data': gastos_data,
        'selected_year': current_year,
        'labels': labels,
        'values': values,
        'colors': colors,
        'categorias': categorias,
        })

def gerenciar(request):
    contas = Conta.objects.filter(user=request.user)
    categorias = Categorias.objects.filter(user=request.user)
    total_contas = calcula_total(contas, 'valor')
    valores = Valores.objects.filter(user=request.user).select_related('categoria', 'conta').order_by('-data')

    return render(request, 'gerenciar.html', {
        'contas' : contas,
        'total_contas' : total_contas,
        'categorias' : categorias,
        'valores': valores,
    })

def cadastrar_banco(request):
    apelido = request.POST.get('apelido')
    banco = request.POST.get('banco')
    tipo = request.POST.get('tipo')
    valor = request.POST.get('valor')
    icone = request.FILES.get('icone')
    
    if len(apelido.strip()) == 0 or len(valor.strip()) == 0:
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos!')
        return redirect('/perfil/gerenciar/')

    conta = Conta(
        user=request.user,
        apelido=apelido,
        banco=banco,
        tipo=tipo,
        valor=valor,
        icone=icone
    )
    
    conta.save()
    messages.add_message(request, constants.SUCCESS, 'Conta cadastrada com sucesso!')
    return redirect('/perfil/gerenciar/')

def deletar_banco(request, id):
    try:
        conta = Conta.objects.get(id=id, user=request.user)
        # Deletar todos os valores associados a esta conta
        Valores.objects.filter(conta=conta).delete()
        # Depois deletar a conta
        conta.delete()
        
        messages.add_message(request, constants.SUCCESS, 'Conta removida com sucesso')
    except Exception as e:
        messages.add_message(request, constants.ERROR, 'Erro ao remover conta: ' + str(e))
    
    return redirect('/perfil/gerenciar/')

def cadastrar_categoria(request):
    nome = request.POST.get('categoria')
    essencial = bool(request.POST.get('essencial'))

    categoria = Categorias(
        user=request.user,
        categoria=nome,
        essencial=essencial,
        valor_planejado=0,
    )

    categoria.save()
    messages.add_message(request, constants.SUCCESS, 'Categoria cadastrada com sucesso')
    referer = request.META.get('HTTP_REFERER', '/perfil/gerenciar/')
    return redirect(referer)
	

def update_categoria(request, id):
    categoria = Categorias.objects.get(id=id, user=request.user)

    # If POST, update fields (name, valor_planejado, essencial)
    if request.method == 'POST':
        nome = request.POST.get('categoria')
        valor_planejado = request.POST.get('valor_planejado')
        essencial = bool(request.POST.get('essencial'))

        if nome is not None:
            categoria.categoria = nome

        try:
            categoria.valor_planejado = float(valor_planejado) if valor_planejado not in (None, '') else 0
        except ValueError:
            categoria.valor_planejado = 0

        categoria.essencial = essencial
        categoria.save()
        referer = request.META.get('HTTP_REFERER', '/perfil/categorias/')
        return redirect(referer)

    # Default: toggle essencial (backwards-compatible)
    categoria.essencial = not categoria.essencial
    categoria.save()
    referer = request.META.get('HTTP_REFERER', '/perfil/gerenciar/')
    return redirect(referer)


def categorias(request):
    categorias = Categorias.objects.filter(user=request.user)
    return render(request, 'categorias.html', {'categorias': categorias})


def deletar_categoria(request, id):
    # Only allow POST to delete (safer)
    if request.method != 'POST':
        messages.add_message(request, constants.ERROR, 'Ação inválida')
        referer = request.META.get('HTTP_REFERER', '/perfil/gerenciar/')
        return redirect(referer)

    categoria = Categorias.objects.get(id=id, user=request.user)
    categoria.delete()
    messages.add_message(request, constants.SUCCESS, 'Categoria removida com sucesso')
    referer = request.META.get('HTTP_REFERER', '/perfil/gerenciar/')
    return redirect(referer)

def dashboard(request):
    """Dashboard view: aggregate expenses by category for a selected month/year.

    Query params:
    - month (1-12) default: current month
    - year default: current year

    Returns: template with labels, values and color list for Chart.js
    """
    # parse period params
    try:
        month = int(request.GET.get('month') or datetime.now().month)
    except ValueError:
        month = datetime.now().month

    try:
        year = int(request.GET.get('year') or datetime.now().year)
    except ValueError:
        year = datetime.now().year

    # aggregate using ORM for performance
    queryset = Valores.objects.filter(user=request.user, data__year=year, data__month=month, tipo='S')
    agg = queryset.values('categoria__categoria').annotate(total=Sum('valor')).order_by('-total')

    labels = []
    values = []
    for item in agg:
        labels.append(item['categoria__categoria'] or 'Sem categoria')
        # Sum may be Decimal; convert to float for JS
        total = item['total'] or 0
        try:
            values.append(float(total))
        except Exception:
            values.append(0.0)

    # generate colors (cycle palette)
    palette = ['#10B981', '#06b6d4', '#f97316', '#ef4444', '#60a5fa', '#7c3aed', '#f59e0b', '#14b8a6']
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    # Get evolution data for all 12 months of the year (shared with home)
    meses_labels, entradas_data, gastos_data = get_evolution_data(year, request.user)

    return render(request, 'dashboard.html', {
        'labels': labels,
        'values': values,
        'colors': colors,
        'selected_month': month,
        'selected_year': year,
        'meses_labels': meses_labels,
        'entradas_data': entradas_data,
        'gastos_data': gastos_data,
    })


def relatorios(request):
    # Reuse extrato's listing logic to show values filtered by conta/categoria
    from extrato.models import Valores
    contas = Conta.objects.filter(user=request.user)
    categorias = Categorias.objects.filter(user=request.user)

    conta_get = request.GET.get('conta')
    categoria_get = request.GET.get('categoria')

    # Additional filters: date range, search, sort
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')
    sort = request.GET.get('sort')
    page_number = request.GET.get('page')

    valores = Valores.objects.filter(user=request.user, data__month=datetime.now().month)

    if conta_get:
        valores = valores.filter(conta__id=conta_get)

    if categoria_get:
        valores = valores.filter(categoria__id=categoria_get)

    if start_date:
        valores = valores.filter(data__gte=start_date)

    if end_date:
        valores = valores.filter(data__lte=end_date)

    if search:
        valores = valores.filter(descricao__icontains=search)

    # Sorting
    valid_sorts = {
        'data': 'data',
        '-data': '-data',
        'valor': 'valor',
        '-valor': '-valor'
    }
    if sort in valid_sorts:
        valores = valores.order_by(valid_sorts[sort])
    else:
        valores = valores.order_by('-data')

    # Pagination
    paginator = Paginator(valores, 20)
    valores_page = paginator.get_page(page_number)

    return render(request, 'relatorios.html', {
        'valores': valores_page,
        'contas': contas,
        'categorias': categorias,
        'paginator': paginator,
        'page_obj': valores_page,
    })


def relatorios_export_csv(request):
    from extrato.models import Valores
    valores = Valores.objects.filter(data__month=datetime.now().month)

    conta_get = request.GET.get('conta')
    categoria_get = request.GET.get('categoria')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')

    if conta_get:
        valores = valores.filter(conta__id=conta_get)
    if categoria_get:
        valores = valores.filter(categoria__id=categoria_get)
    if start_date:
        valores = valores.filter(data__gte=start_date)
    if end_date:
        valores = valores.filter(data__lte=end_date)
    if search:
        valores = valores.filter(descricao__icontains=search)

    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorios.csv"'

    writer = csv.writer(response)
    writer.writerow(['Conta', 'Categoria', 'Data', 'Tipo', 'Valor', 'Descrição'])
    for v in valores:
        writer.writerow([str(v.conta), str(v.categoria), v.data, v.tipo, v.valor, v.descricao])

    return response


def relatorios_export_pdf(request):
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from io import BytesIO
    from datetime import datetime
    from extrato.models import Valores

    # Get data with filters
    valores = Valores.objects.filter(user=request.user, data__month=datetime.now().month)
    conta_get = request.GET.get('conta')
    categoria_get = request.GET.get('categoria')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')

    if conta_get:
        valores = valores.filter(conta__id=conta_get, conta__user=request.user)
    if categoria_get:
        valores = valores.filter(categoria__id=categoria_get, categoria__user=request.user)
    if start_date:
        valores = valores.filter(data__gte=start_date)
    if end_date:
        valores = valores.filter(data__lte=end_date)
    if search:
        valores = valores.filter(descricao__icontains=search)

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Add title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#064E3B'),
        spaceAfter=12,
        alignment=1  # Center
    )
    elements.append(Paragraph('Relatório de Movimentações', title_style))
    elements.append(Spacer(1, 12))

    # Add info
    info_style = styles['Normal']
    info_text = f'<b>Data de Geração:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}<br/><b>Total de Movimentações:</b> {valores.count()}'
    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 12))

    # Create table data
    table_data = [['Conta', 'Categoria', 'Data', 'Tipo', 'Valor', 'Descrição']]
    
    for valor in valores:
        tipo = 'Saída' if valor.tipo == 'S' else 'Entrada'
        categoria_nome = str(valor.categoria.categoria) if valor.categoria else 'Sem categoria'
        table_data.append([
            str(valor.conta.apelido),
            categoria_nome,
            valor.data.strftime('%d/%m/%Y'),
            tipo,
            f'R$ {valor.valor:.2f}',
            str(valor.descricao)[:30]
        ])

    if not valores.exists():
        table_data.append(['', '', '', '', '', 'Nenhuma movimentação encontrada'])

    # Create table with style
    table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch, 1.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#064E3B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorios.pdf"'
    return response

def adicionar_valor(request):
    if request.method == 'POST':
        valor = request.POST.get('valor')
        categoria_id = request.POST.get('categoria')
        descricao = request.POST.get('descricao')
        data = request.POST.get('data')
        conta_id = request.POST.get('conta')
        tipo = request.POST.get('tipo')
        
        if not valor or not data or not conta_id:
            messages.add_message(request, constants.ERROR, 'Preencha todos os campos obrigatórios!')
            return redirect(request.META.get('HTTP_REFERER', '/perfil/home/'))
        
        try:
            categoria = None
            if categoria_id:
                categoria = Categorias.objects.get(id=categoria_id, user=request.user)
            
            conta = Conta.objects.get(id=conta_id, user=request.user)
            
            novo_valor = Valores(
                user=request.user,
                valor=valor,
                categoria=categoria,
                descricao=descricao,
                data=data,
                conta=conta,
                tipo=tipo
            )
            novo_valor.save()
            
            # Update conta balance
            valor_float = float(valor)
            if tipo == "E":
                conta.valor += valor_float
            elif tipo == "S":
                conta.valor -= valor_float
            conta.save()
            
            messages.add_message(request, constants.SUCCESS, f'{"Entrada" if tipo == "E" else "Saída"} registrada com sucesso!')
            return redirect('/perfil/home/')
        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Erro ao registrar: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', '/perfil/home/'))
    
    tipo_valor = request.GET.get('tipo', 'E')
    categorias = Categorias.objects.filter(user=request.user)
    contas = Conta.objects.filter(user=request.user)
    
    return render(request, 'adicionar_valor.html', {
        'tipo_valor': tipo_valor,
        'categorias': categorias,
        'contas': contas
    })

def adicionar_entrada(request):
    request.GET = request.GET.copy()
    request.GET['tipo'] = 'E'
    return adicionar_valor(request)

def adicionar_saida(request):
    request.GET = request.GET.copy()
    request.GET['tipo'] = 'S'
    return adicionar_valor(request)

@login_required(login_url='login')
def perfil_usuario(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'perfil_usuario.html', {'user_profile': user_profile})

@login_required(login_url='login')
def editar_perfil(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Atualiza foto de perfil se enviada
        foto_file = request.FILES.get('foto_perfil')
        if foto_file:
            user_profile.foto_perfil = foto_file

        user_profile.bio = request.POST.get('bio', '')
        user_profile.telefone = request.POST.get('telefone', '')
        user_profile.data_nascimento = request.POST.get('data_nascimento') or None
        user_profile.cpf = request.POST.get('cpf', '')
        user_profile.endereco = request.POST.get('endereco', '')
        user_profile.cidade = request.POST.get('cidade', '')
        user_profile.estado = request.POST.get('estado', '')
        user_profile.save()
        
        messages.add_message(request, constants.SUCCESS, 'Perfil atualizado com sucesso!')
        return redirect('editar_perfil')
    
    return render(request, 'editar_perfil.html', {'user_profile': user_profile})

@login_required(login_url='login')
def configuracoes(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'gerais':
            user_profile.idioma = request.POST.get('idioma', 'pt-BR')
            user_profile.moeda = request.POST.get('moeda', 'BRL')
            user_profile.formato_data = request.POST.get('formato_data', 'DD/MM/YYYY')
            user_profile.save()
            messages.add_message(request, constants.SUCCESS, 'Configurações atualizadas!')
        elif action == 'privacidade':
            user_profile.tema = request.POST.get('tema', 'light')
            user_profile.notificacoes = request.POST.get('notificacoes') == 'on'
            user_profile.save()
            messages.add_message(request, constants.SUCCESS, 'Preferências atualizadas!')
        
        return redirect('configuracoes')
    
    return render(request, 'configuracoes.html', {'user_profile': user_profile})

# class DeletarBancoView(DeleteView):
#     model = Conta
#     success_url = reverse_lazy('gerenciar')
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         self.object.delete()

#         return HttpResponseRedirect(self.get_success_url())