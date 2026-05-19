import re
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from orders.models import OrderItem, Order
from menu.models import Product

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


# ── Handlers Chatbot ──────────────────────────────────────────────────────────
def handle_ventas_hoy():
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


# ── Vista Chatbot ─────────────────────────────────────────────────────────────
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


# ── Vista Recomendador SPRINT 5 ───────────────────────────────────────────────
class RecommendProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, producto_id):
        # 1. Obtener todas las órdenes completadas
        items = OrderItem.objects.filter(pedido__estado='entregado').values('pedido_id', 'producto_id', 'cantidad')
        df = pd.DataFrame(items)

        if df.empty or len(df['pedido_id'].unique()) < 5:
            # Fallback si no hay suficientes datos en la DB aún
            return Response([])

        # 2. Crear una matriz de co-ocurrencia (Usuarios/Pedidos x Productos)
        matrix = df.pivot_table(index='pedido_id', columns='producto_id', values='cantidad', fill_value=0)
        
        # Si el producto solicitado nunca se ha vendido, devolver vacío
        if int(producto_id) not in matrix.columns:
            return Response([])

        # 3. Calcular la similitud del coseno entre los productos (transponemos la matriz)
        item_similarity = cosine_similarity(matrix.T)
        similarity_df = pd.DataFrame(item_similarity, index=matrix.columns, columns=matrix.columns)

        # 4. Obtener los productos más similares al producto actual (excluyendo el mismo)
        similar_items = similarity_df[int(producto_id)].sort_values(ascending=False)
        top_similar_ids = similar_items.drop(int(producto_id)).head(3).index.tolist()

        # 5. Formatear la respuesta
        recomendados = Product.objects.filter(id__in=top_similar_ids, disponible=True)
        from menu.serializers import ProductSerializer # Importación retrasada para evitar importes circulares
        
        return Response(ProductSerializer(recomendados, many=True, context={'request': request}).data)