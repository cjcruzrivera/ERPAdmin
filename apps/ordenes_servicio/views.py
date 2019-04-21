from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from .forms import *
from django.db import models
from apps.datosmaestros.models.dato import DatoModel
from apps.datosmaestros.models.categoria import CategoriaModel
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

#autocomplete
from apps.usuarios.models import *
from apps.usuarios.forms import *
from django.http import HttpResponseRedirect, JsonResponse

def to_login(request):
    return redirect('/ordenes_servicio/login')

# Create your views here.
def ordenes_login(request):
    if request.user.is_authenticated:
        return redirect("/ordenes_servicio/welcome")
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/ordenes_servicio/welcome/")
        else:
            context = {"message":"Usuario o Contraseña Incorrectos"}
            return render(request, "usuarios/login.html",context)
    else:
        logout(request)
        return render(request, "usuarios/login.html")

def manage_options(request, context):
    context["options"] = [
        {"name": "Inicio", "href": "/ordenes_servicio/welcome/"},
    ]
    if not request.user.is_anonymous:
        context["cargo"] = request.user.cargo
    if request.user.is_superuser:
        context["options"] += [
            {"name": "Django Admin Site", "href": "/admin"},
            {"name": "Crear Cliente", "href": "/ordenes_servicio/crear_cliente/"},
            {"name": "Consultar Clientes", "href": "/ordenes_servicio/consultar_clientes/"}
        ]
        context["boxes"] = [
            {"title": "Clientes Registrados", "value": 0, "color": "bg-aqua", "icon": "ion-person-add"},
        ]
    if request.user.cargo == 'C':
        context["options"] += [
            {"name": "Crear Orden de Servicio", "href": "/ordenes_servicio/crear_orden_servicio/"},
            {"name": "Consultar Ordenes de Servicio", "href": "/ordenes_servicio/consultar_orden_servicio/"}
        ]

        ordenes = OrdenServicio.objects.filter(coordinador=request.user).order_by('-id')
        context["ordenes_timeline"] = ordenes

        registradas = ordenes.count()
        tramite = ordenes.filter(estado="TR").count()
        cerradas = ordenes.filter(estado="CE").count()
        canceladas = ordenes.filter(estado="CA").count()
        context["boxes"] = [
            {"title": "Ordenes Registradas", "value": registradas, "color": "bg-purple", "icon": "ion-clipboard"},
            {"title": "Ordenes en Trámite", "value": tramite, "color": "bg-light-blue-active", "icon": "ion-android-sync"},
            {"title": "Ordenes Cerradas", "value": cerradas, "color": "bg-green-active", "icon": "ion-checkmark"},
            {"title": "Ordenes Canceladas", "value": canceladas, "color": "bg-red-active", "icon": "ion-close"},
        ]


    if request.user.cargo == 'O':
        context["options"] += [
            {"name": "Consultar Ordenes de Servicio", "href": "/ordenes_servicio/consultar_orden_servicio/"}
        ]

        ordenes = OrdenServicio.objects.filter(encargado=request.user).order_by('-id')
        context["ordenes_timeline"] = ordenes

        atender = ordenes.filter(estado="AS").count()
        tramite = ordenes.filter(estado="TR").count()
        cerradas = ordenes.filter(estado="CE").count()
        canceladas = ordenes.filter(estado="CA").count()

        context["boxes"] = [
            {"title": "Ordenes Por Atender", "value": atender, "color": "bg-teal-active", "icon": "ion-folder"},
            {"title": "Ordenes en Trámite", "value": tramite, "color": "bg-light-blue-active", "icon": "ion-android-sync"},
            {"title": "Ordenes Cerradas", "value": cerradas, "color": "bg-green-active", "icon": "ion-checkmark"},
            {"title": "Ordenes Canceladas", "value": canceladas, "color": "bg-red-active", "icon": "ion-close"},
        ]


@login_required(login_url="/ordenes_servicio/login/")
def ordenes_welcome(request):
    context = {}
    manage_options(request,context)
    return render(request, "ordenes_servicio/index.html",context)


def gtfo(request):
    logout(request)
    return redirect("/ordenes_servicio/login/")

@login_required(login_url="/ordenes_servicio/login/")
def crear_orden_servicio(request):
    usuario = request.user
    # Validar que el usuario sea un coordinador de servicios
    print(usuario.get_all_permissions())
    if usuario.has_perm('ordenes_servicio.add_ordenservicio'):
        if request.method == 'POST':
            form = OrdenServicioForm(request.POST)
            if form.is_valid():
                form.instance.coordinador = request.user
                form.save()
                messages.success(request, 'Orden de servicio creada exitosamente')
                form = OrdenServicioForm()
                return redirect('/ordenes_servicio/consultar_orden_servicio')
            else:
                messages.error(request, 'El formulario NO es valido, Por favor corrige los errores')
                for error in form.errors:
                    messages.error(request, "Hay un problema con " + error)
        else:
            form = OrdenServicioForm()

        context = {"form":form}
        manage_options(request,context)
        return render(request, 'ordenes_servicio/crear_orden_servicio.html', context)
    else:
        messages.error(request, 'No estas autorizado para realizar esta acción')
        return redirect('/ordenes_servicio/')

@login_required(login_url="/ordenes_servicio/login/")
def aceptar_orden_servicio(request):
    if request.is_ajax():
        id = request.GET.get('orden_id', None)
        try:
            orden_servicio_aux = OrdenServicio.objects.get(id=id)
            usuario = request.user
            encargado = usuario.encargado_set.all().filter(id=id).count() == 1
            if usuario.has_perm('ordenes_servicio.operate_ordenservicio') and encargado:
                orden_servicio_aux.estado = "TR"
                orden_servicio_aux.save()
                messages.success(request, 'Orden de Servicio Aceptada')
                return JsonResponse({'success': True})
            else:
                messages.error(request, 'No estas autorizado para realizar esta acción')
                return JsonResponse({'success': False})
        except:
            return JsonResponse({'orden_id': 0})


@login_required(login_url="/ordenes_servicio/login/")
def cerrar_orden_servicio(request):
    if request.is_ajax():
        id = request.GET.get('orden_id', None)
        try:
            orden_servicio_aux = OrdenServicio.objects.get(id=id)
            usuario = request.user
            encargado = usuario.encargado_set.all().filter(id=id).count() == 1
            if usuario.has_perm('ordenes_servicio.operate_ordenservicio') and encargado:
                orden_servicio_aux.estado = "CE"
                orden_servicio_aux.save()
                messages.success(request, 'Orden de Servicio Cerrada')
                return JsonResponse({'success': True})
            else:
                messages.error(request, 'No estas autorizado para realizar esta acción')
                return JsonResponse({'success': False})
        except:
            return JsonResponse({'orden_id': 0})


@login_required(login_url="/ordenes_servicio/login/")
def cancelar_orden_servicio(request):
    if request.is_ajax():
        id = request.GET.get('orden_id', None)
        comentarios = request.GET.get('comentarios', None)
        try:
            orden_servicio_aux = OrdenServicio.objects.get(id=id)
        except:
            return JsonResponse({'success': False})
        pertenece_a_usuario =  request.user.encargado_set.all().filter(id=id).count() == 1
        if request.user.has_perm('ordenes_servicio.cancel_ordenservicio') or (request.user.has_perm('ordenes_servicio.operate_ordenservicio') and pertenece_a_usuario):
            error = False
            if(orden_servicio_aux.estado == "CA"):
                messages.error(request, "No se puede cancelar una orden de servicio ya cancelada")
                error = True
            elif(orden_servicio_aux.estado == "CE"):
                messages.error(request, "No se puede cancelar una orden de servicio cerrada")
                error = True
            if comentarios != "":
                orden_servicio_aux.comentarios = comentarios
                orden_servicio_aux.estado = "CA"
                orden_servicio_aux.save()
                messages.success(request, 'Orden de Servicio Cancelada Exitósamente')
                return JsonResponse({'success': True})
            else:
                error = True
                messages.error(request, 'Debe agregar un comentarios de cancelacion')
            if error:
                return JsonResponse({'success': False})
        else:
            messages.error(request, 'No estas autorizado para realizar esta acción')
            return JsonResponse({'success': False})

@login_required(login_url="/ordenes_servicio/login/")
def consultar_orden_servicio(request):
    usuario = request.user
    if usuario.has_perm('ordenes_servicio.list_ordenservicio'):
        context ={'ordenes': listar_ordenes(usuario)}
        manage_options(request,context)
        return render(request, 'ordenes_servicio/consultar_orden_servicio.html', context)
    else:
        messages.error(request, 'No estas autorizado para realizar esta acción')
        return redirect('/ordenes_servicio/')

def listar_ordenes(usuario):
    return OrdenServicio.get_data(usuario)

def operadores_autocomplete(request):
    # user = request.user
    json = []
    if request.GET.get('q'):
        q = request.GET['q']
        criterio_uno = (models.Q(cedula__icontains=q) | models.Q(first_name__icontains=q) | models.Q(last_name__icontains=q))
        criterio_dos = models.Q(cargo="O") # Tiene que ser operario
        data = User.objects.filter(criterio_uno & criterio_dos).values_list('cedula', 'first_name', 'last_name', 'id')[:10]
        arr = list(data)
        for tupla in arr:
            cedula = tupla[0]
            nombre = tupla[1]
            apellidos = tupla[2]
            id = tupla[3]
            json.append({'id': id, 'text':cedula + ' - ' + nombre + ' ' + apellidos})
    return JsonResponse(json, safe=False, json_dumps_params={'ensure_ascii':False})

def clientes_autocomplete(request):
    # user = request.user
    json = []
    if request.GET.get('q'):
        q = request.GET['q']
        categoria = CategoriaModel.objects.get(nombre = 'clientes')
        clientes_query = DatoModel.objects.filter(categoria = categoria.id).distinct()
        data =clientes_query.filter(valormodel__valor__icontains=q).values_list('id')[:10]
        arr = list(data)
        for tupla in arr:
            id = tupla[0]
            cedula = DatoModel.objects.get(id=id).valormodel_set.all().get(nombre="cedula").valor
            nombres = DatoModel.objects.get(id=id).valormodel_set.all().get(nombre="nombres").valor
            apellidos = DatoModel.objects.get(id=id).valormodel_set.all().get(nombre="apellidos").valor
            json.append({'id': id, 'text':cedula + ' - ' + nombres + ' ' + apellidos})
    return JsonResponse(json, safe=False, json_dumps_params={'ensure_ascii':False})

@login_required(login_url="/ordenes_servicio/login/")
def crear_cliente(request):
    if request.user.is_superuser:
        context = {"form": CrearClienteForm}
        manage_options(request,context)
        return render(request,"usuarios/crear_cliente.html",context)

@login_required(login_url="/ordenes_servicio/login/")
def consultar_clientes(request):
    if request.user.is_superuser:
        context = {"clientes": Cliente.objects.all()}
        manage_options(request,context)
        return render(request,"usuarios/consultar_clientes.html",context)
