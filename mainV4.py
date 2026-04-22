import streamlit as st
import pandas as pd
import numpy as np
import datetime
import uuid
import time


# ==========================================
# 1. DEFINICIÓN DE CLASES (MODELO DE DOMINIO)
# ==========================================

class InterfazLumenSmart:
    """Interfaz para la comunicación con el sistema de iluminación del campus."""

    @staticmethod
    def recibir_estado_farolas():
        """Simula la respuesta de la API de infraestructura."""
        estados = ["encendida", "apagada", "averiada"]
        # Pesos para que la mayoría estén encendidas normalmente
        return np.random.choice(estados, p=[0.7, 0.15, 0.15])


class Tramo:
    """Representa un segmento físico del campus con su estado de iluminación."""

    def __init__(self, id_tramo: str, lat: float, lon: float):
        self.id_tramo = id_tramo
        self.lat = lat
        self.lon = lon
        self.estado_farola = "encendida"  # Estado por defecto
        self.color_mapa = "#00FF00"  # Verde por defecto

    def actualizar_lumen_smart(self):
        """CU-21: Actualiza el estado mediante la interfaz LumenSmart."""
        self.estado_farola = InterfazLumenSmart.recibir_estado_farolas()
        # Mapeo de colores para el mapa de Streamlit (RGB/Hex)
        if self.estado_farola == "encendida":
            self.color_mapa = "#228B22"  # Verde Bosque
        elif self.estado_farola == "apagada":
            self.color_mapa = "#FF0000"  # Rojo
        else:  # averiada
            self.color_mapa = "#8B0000"  # Rojo Oscuro


class ContactoConfianza:
    def __init__(self, nombre: str, telefono: str):
        self.nombre = nombre
        self.telefono = telefono


class Incidencia:
    def __init__(self, tipo: str, ubicacion: str, autor: str):
        self.tipo = tipo
        self.ubicacion = ubicacion
        self.fecha = datetime.date.today().strftime("%d/%m/%Y")
        self.hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.estado = "Pendiente"
        self.autor = autor
        self.ticket_id = f"TICKET-{str(uuid.uuid4())[:8].upper()}"


class ControladorSeguridad:
    def __init__(self, tiempo_wait: int = 10):
        self.tiempo_wait = tiempo_wait

    def disparar_alerta_automatica(self, usuario, contacto):
        return f"🚨 ALERTA: {usuario.nombre} no responde. Enviando coordenadas a Seguridad URJC y a {contacto.nombre} ({contacto.telefono})."


# Jerarquía de Usuarios
class Usuario:
    def __init__(self, nombre, nick, email, password):
        self.nombre = nombre
        self.nick = nick
        self.email_corporativo = email
        self.password = password
        self.contacto = ContactoConfianza("Padre/Madre", "600112233")

    def obtener_rol(self): return self.__class__.__name__

    def reportar_incidencia(self, t, u): return Incidencia(t, u, self.nick)


class Estudiante(Usuario): pass


class PDI(Usuario): pass


class PTGAS(Usuario):
    def __init__(self, n, ni, e, p, admin=False):
        super().__init__(n, ni, e, p)
        self.administrador = admin


# ==========================================
# 2. CONFIGURACIÓN DEL ENTORNO Y PERSISTENCIA
# ==========================================

def inicializar_datos():
    if 'db_usuarios' not in st.session_state:
        st.session_state.db_usuarios = {
            "e.martinez@alumnos.urjc.es": Estudiante("Elena Martínez", "elenam", "e.martinez@alumnos.urjc.es", "123"),
            "admin.sistemas@urjc.es": PTGAS("Ana Gómez", "anag", "admin.sistemas@urjc.es", "123", admin=True)
        }
    if 'incidencias' not in st.session_state: st.session_state.incidencias = []

    # Inicializar Tramos del Campus (Móstoles) si no existen
    if 'tramos_campus' not in st.session_state:
        # Coordenadas reales aprox. Campus Móstoles URJC
        coordenadas = [
            (40.3325, -3.8830), (40.3340, -3.8820), (40.3350, -3.8850),
            (40.3310, -3.8810), (40.3330, -3.8860), (40.3360, -3.8840)
        ]
        st.session_state.tramos_campus = [Tramo(f"T-{i}", c[0], c[1]) for i, c in enumerate(coordenadas)]
        # Primera carga de LumenSmart
        for t in st.session_state.tramos_campus: t.actualizar_lumen_smart()


# ==========================================
# 3. VISTAS DE LA APLICACIÓN
# ==========================================

def vista_mapa_seguridad():
    st.header("🗺️ Mapa de Seguridad (LumenSmart)")
    st.markdown("Estado de la infraestructura lumínica del Campus en tiempo real.")

    if st.button("🔄 Refrescar API LumenSmart"):
        for t in st.session_state.tramos_campus:
            t.actualizar_lumen_smart()
        st.toast("Conectando con LumenSmart... ¡Datos actualizados!")

    # Preparar DataFrame para el mapa
    data = {
        'lat': [t.lat for t in st.session_state.tramos_campus],
        'lon': [t.lon for t in st.session_state.tramos_campus],
        'ID': [t.id_tramo for t in st.session_state.tramos_campus],
        'Estado': [t.estado_farola for t in st.session_state.tramos_campus],
        'color': [t.color_mapa for t in st.session_state.tramos_campus]
    }
    df = pd.DataFrame(data)

    # Mostrar Mapa (usando st.map con soporte de colores en versiones recientes)
    st.map(df, color="color", size=20)

    # Comprobar estados críticos
    deficiencias = df[df['Estado'].isin(['apagada', 'averiada'])]
    if not deficiencias.empty:
        st.warning(
            f"⚠️ **Atención:** Se han detectado {len(deficiencias)} farolas con iluminación deficiente. El algoritmo de rutas penalizará estos tramos para garantizar tu seguridad.")
    else:
        st.success("☀️ Todos los tramos principales cuentan con iluminación óptima.")

    st.write("### Detalle técnico de luminarias")
    st.table(df[['ID', 'Estado']])


def vista_voy_contigo():
    st.header("🛡️ Modo 'Voy Contigo'")
    if 'voy_contigo_activo' not in st.session_state: st.session_state.voy_contigo_activo = False
    if 'en_prealerta' not in st.session_state: st.session_state.en_prealerta = False

    usuario = st.session_state.usuario_actual
    controlador = ControladorSeguridad()

    if not st.session_state.voy_contigo_activo:
        if st.button("Activar Modo Voy Contigo", type="primary", use_container_width=True):
            st.session_state.voy_contigo_activo = True
            st.rerun()
    else:
        st.success("🛰️ Compartiendo ubicación activa...")
        if not st.session_state.en_prealerta:
            if st.button("🚨 Simular Desvío Brusco"):
                st.session_state.en_prealerta = True
                st.rerun()
        else:
            st.error("❗ ¿Estás bien?")
            if st.button("✅ SÍ, ESTOY BIEN"):
                st.session_state.en_prealerta = False
                st.rerun()

def vista_reportar_incidencia():
    st.header("🚨 Reportar Incidencia")
    with st.form("f_inc", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Farola fundida", "Zona solitaria/miedo", "Obstáculo", "Punto dificultad"])
        ubic = st.text_input("Ubicación")
        if st.form_submit_button("Enviar"):
            if not ubic:
                st.error("Añade una ubicación.")
            else:
                inc = st.session_state.usuario_actual.reportar_incidencia(tipo, ubic)
                st.session_state.incidencias.append(inc)
                st.success(f"Registrada con éxito: {inc.ticket_id}")

def vista_admin():
    user = st.session_state.usuario_actual
    if user.obtener_rol() == "PTGAS" and getattr(user, 'administrador', False):
        st.header("🛠️ Panel de Administraciones")
        df = pd.DataFrame([vars(i) for i in st.session_state.incidencias])

        # Corrección: Comprobar si está vacío correctamente
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay incidencias reportadas en el sistema en este momento.")
    else:
        st.error("Acceso restringido.")


# ==========================================
# 4. MAIN Y LOGUEO
# ==========================================

def main():
    st.set_page_config(page_title="Senda URJC", page_icon="🛡️", layout="wide")
    inicializar_datos()

    if 'usuario_actual' not in st.session_state:
        st.title("Senda URJC - Acceso")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Entrar"):
            u = st.session_state.db_usuarios.get(e)
            if u and u.password == p:
                st.session_state.usuario_actual = u
                st.rerun()
            else:
                st.error("Acceso denegado")
    else:
        # --- DENTRO DE main() ---
        user = st.session_state.usuario_actual
        with st.sidebar:
            st.title("Senda URJC")
            st.write(f"👤 {user.nombre} ({user.obtener_rol()})")

            # Construimos el menú dinámicamente según el rol
            opciones_menu = ["🏠 Inicio", "🚨 Reportar Incidencia", "🗺️ Mapa LumenSmart", "🛡️ Voy Contigo"]

            # El panel de admin SOLO aparece si eres PTGAS administrador
            if user.obtener_rol() == "PTGAS" and getattr(user, 'administrador', False):
                opciones_menu.append("🛠️ Panel Admin")

            opcion = st.radio("Menú", opciones_menu)

            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                del st.session_state.usuario_actual
                st.rerun()

        # Enrutador
        if opcion == "🏠 Inicio":
            st.title(f"Bienvenido/a, {user.nombre}")
        elif opcion == "🚨 Reportar Incidencia":
            vista_reportar_incidencia()
        elif opcion == "🗺️ Mapa LumenSmart":
            vista_mapa_seguridad()
        elif opcion == "🛡️ Voy Contigo":
            vista_voy_contigo()
        elif opcion == "🛠️ Panel Admin":
            vista_admin()


if __name__ == "__main__":
    main()
