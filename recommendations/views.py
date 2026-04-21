"""
Chatbot operacional — Sprint 4
Usa NLTK para tokenización y detección de intención por palabras clave.
Responde preguntas sobre pedidos activos, ventas del día e inventario.
"""
import re
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# ── Importación segura de NLTK ────────────────────────────────────────────────
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    STOP_ES = set(stopwords.words('spanish'))
    NLTK_OK = True
except Exception:
    NLTK_OK = False


def tokenizar(texto):
    """Devuelve lista de tokens en minúsculas sin stopwords."""
    texto = texto.lower()
    if NLTK_OK:
        tokens = word_tokenize(texto, language='spanish')
        return [t for t in tokens if t.isalpha() and t not in STOP_ES]
    # fallback sin NLTK
    return re.findall(r'[a-záéíóúüñ]+', texto)


# ── Definición de intenciones ─────────────────────────────────────────────────
INTENTS = [
    {
        'name':     'ventas_hoy',
        'keywords': {'venta', 'ventas', 'ingreso', 'ingresos', 'dinero', 'hoy',
                     'facturado', 'ganado', 'recaudado', 'total'},
    },
    {
        'name':     'pedidos_activos',
        'keywords': {'pedido', 'pedidos', 'activo', 'activos', 'pendiente',
                     'espera', 'preparacion', 'cocina', 'cuantos'},
    },
    {
        'name':     'top_productos',
        'keywords': {'producto', 'productos', 'vendido', 'vendidos', 'popular',
                     'populares', 'top', 'mejor', 'mejores', 'favorito'},
    },
    {
        'name':     'stock_critico',
        'keywords': {'stock', 'inventario', 'agotado', 'agotados', 'critico',
                     'criticos', 'rojo', 'reponer', 'reposicion'},
    },
    {
        'name':     'cancelados',
        'keywords': {'cancelado', 'cancelados', 'cancelacion', 'anulado', 'anulados'},
    },
    {
        'name':     'saludo',
        'keywords': {'hola', 'buenos', 'buenas', 'saludos', 'hey', 'ola'},
    },
    {
        'name':     'ayuda',
        'keywords': {'ayuda', 'ayudame', 'puedes', 'hacer', 'consulta', 'preguntar',
                     'que', 'como', 'info', 'informacion'},
    },
]


def detectar_intencion(tokens):
    scores = {}
    for intent in INTENTS:
        score = len(intent['keywords'].intersection(set(tokens)))
        if score > 0:
            scores[intent['name']] = score
    if not scores:
        return 'desconocido'
    return max(scores, key=scores.get)


# ── Handlers ──────────────────────────────────────────────────────────────────
def handle_ventas_hoy():
    from orders.models import Order
    hoy   = timezone.now().date()
    total = (
        Order.objects.filter(creado_en__date=hoy, estado='entregado')
        .aggregate(s=Sum('total'))['s'] or 0
    )
    count = Order.objects.filter(creado_en__date=hoy, estado='entregado').count()
    return (
        f"💰 **Ventas de hoy ({hoy.strftime('%d/%m/%Y')})**\n"
        f"• Total recaudado: **Bs. {float(total):.2f}**\n"
        f"• Pedidos entregados: **{count}**"
    )


def handle_pedidos_activos():
    from orders.models import Order
    activos = Order.objects.filter(
        estado__in=['en_espera', 'confirmado', 'en_preparacion']
    )
    espera      = activos.filter(estado='en_espera').count()
    confirmado  = activos.filter(estado='confirmado').count()
    preparacion = activos.filter(estado='en_preparacion').count()
    return (
        f"📋 **Pedidos activos ahora**\n"
        f"• En espera de pago: **{espera}**\n"
        f"• Confirmados (esperando cocina): **{confirmado}**\n"
        f"• En preparación: **{preparacion}**\n"
        f"• **Total activos: {espera + confirmado + preparacion}**"
    )


def handle_top_productos():
    from orders.models import OrderItem
    top = (
        OrderItem.objects
        .values('producto__nombre')
        .annotate(qty=Sum('cantidad'))
        .order_by('-qty')[:5]
    )
    if not top:
        return "📦 Aún no hay datos de ventas registrados."
    lines = "\n".join(
        f"  {i+1}. {t['producto__nombre']} — {t['qty']} unidades"
        for i, t in enumerate(top)
    )
    return f"🏆 **Top 5 productos más vendidos**\n{lines}"


def handle_stock_critico():
    from menu.models import Granel, Extra
    granel_rojo = list(Granel.objects.filter(estado='rojo').values_list('nombre', flat=True))
    extras_rojo = list(Extra.objects.filter(estado='rojo').values_list('nombre', flat=True))
    from menu.models import Product
    envasados_0 = list(
        Product.objects.filter(tipo='envasado', stock__lte=0).values_list('nombre', flat=True)
    )
    items = granel_rojo + extras_rojo + envasados_0
    if not items:
        return "✅ No hay productos en estado crítico de inventario en este momento."
    lista = "\n".join(f"  • {n}" for n in items)
    return f"🚨 **Productos con stock crítico ({len(items)})**\n{lista}"


def handle_cancelados():
    from orders.models import Order
    hoy = timezone.now().date()
    count_hoy  = Order.objects.filter(creado_en__date=hoy, estado='cancelado').count()
    count_mes  = Order.objects.filter(
        creado_en__month=timezone.now().month,
        creado_en__year=timezone.now().year,
        estado='cancelado'
    ).count()
    return (
        f"❌ **Pedidos cancelados**\n"
        f"• Hoy: **{count_hoy}**\n"
        f"• Este mes: **{count_mes}**"
    )


def handle_saludo():
    from django.utils import timezone as tz
    hora = tz.localtime().hour
    momento = "Buenos días" if hora < 12 else ("Buenas tardes" if hora < 19 else "Buenas noches")
    return (
        f"👋 {momento}! Soy el asistente operacional de **Kusillu**.\n"
        f"Puedo ayudarte con información sobre:\n"
        f"  • Ventas del día\n"
        f"  • Pedidos activos\n"
        f"  • Productos más vendidos\n"
        f"  • Stock crítico\n"
        f"  • Pedidos cancelados\n"
        f"¿Qué quieres consultar?"
    )


def handle_ayuda():
    return (
        "🤖 **Consultas disponibles**\n"
        "• _'¿Cuánto vendimos hoy?'_ → ventas del día\n"
        "• _'¿Cuántos pedidos activos hay?'_ → pedidos en curso\n"
        "• _'¿Cuáles son los más vendidos?'_ → top productos\n"
        "• _'¿Hay stock crítico?'_ → alertas de inventario\n"
        "• _'¿Cuántos pedidos cancelados?'_ → cancelaciones"
    )


HANDLERS = {
    'ventas_hoy':      handle_ventas_hoy,
    'pedidos_activos': handle_pedidos_activos,
    'top_productos':   handle_top_productos,
    'stock_critico':   handle_stock_critico,
    'cancelados':      handle_cancelados,
    'saludo':          handle_saludo,
    'ayuda':           handle_ayuda,
}


# ── Vista ─────────────────────────────────────────────────────────────────────
class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mensaje = request.data.get('mensaje', '').strip()
        if not mensaje:
            return Response({'error': 'Mensaje vacío.'}, status=400)

        tokens    = tokenizar(mensaje)
        intencion = detectar_intencion(tokens)
        handler   = HANDLERS.get(intencion)

        if handler:
            respuesta = handler()
        else:
            respuesta = (
                "🤔 No entendí bien tu consulta. Puedes preguntarme sobre:\n"
                "ventas, pedidos activos, productos más vendidos, stock crítico o cancelaciones."
            )

        return Response({
            'mensaje':   mensaje,
            'intencion': intencion,
            'respuesta': respuesta,
        })