import streamlit as st
import datetime
import uuid
import pandas as pd


# ==========================================
# 1. DEFINICIÓN DE CLASES (MODELO DE DOMINIO)
# ==========================================

class Incidencia:
    """Representa un reporte de seguridad o infraestructura en el campus."""

    def __init__(self, tipo: str, ubicacion: str, autor: str):
        self.tipo = tipo
        self.ubicacion = ubicacion
        self.fecha = datetime.date.today().strftime("%d/%m/%Y")
        self.hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.estado = "Pendiente"
        self.autor = autor
        self.ticket_id = None

    def registrar_incidencia(self):
        """Simula la lógica de validación y persistencia en base de datos."""
        # Aquí iría la lógica de guardado real (Ej: ORM.save())
        pass

    def generar_ticket(self) -> str:
        """Genera un identificador único para el seguimiento de la incidencia."""
        self.ticket_id = f"TICKET-{str(uuid.uuid4())[:8].upper()}"
        return self.ticket_id


class Usuario:
    """Clase base para todos los usuarios del sistema Senda URJC."""

    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str):
        self.nombre = nombre
        self.nick = nick
        self.email_corporativo = email_corporativo
        self.password = password

    def obtener_rol(self) -> str:
        return self.__class__.__name__

    def reportar_incidencia(self, tipo: str, ubicacion: str) -> Incidencia:
        """CU-15: Crea, configura y devuelve una nueva incidencia."""
        nueva_incidencia = Incidencia(tipo, ubicacion, self.nick)
        nueva_incidencia.generar_ticket()
        nueva_incidencia.registrar_incidencia()
        return nueva_incidencia


class Estudiante(Usuario):
    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str):
        super().__init__(nombre, nick, email_corporativo, password)


class PDI(Usuario):
    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str):
        super().__init__(nombre, nick, email_corporativo, password)


class PTGAS(Usuario):
    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str, administrador: bool = False):
        super().__init__(nombre, nick, email_corporativo, password)
        self.administrador = administrador


class PanelAdministraciones:
    """Interfaz/Controlador para la gestión de incidencias por parte del PTGAS Administrador."""

    @staticmethod
    def listar_tickets_pendientes(lista_incidencias: list) -> pd.DataFrame:
        """Transforma la lista de objetos Incidencia en un DataFrame para su visualización."""
        if not lista_incidencias:
            return pd.DataFrame(columns=["Ticket", "Fecha", "Hora", "Tipo", "Ubicación", "Autor", "Estado"])

        datos = []
        for inc in lista_incidencias:
            datos.append({
                "Ticket": inc.ticket_id,
                "Fecha": inc.fecha,
                "Hora": inc.hora,
                "Tipo": inc.tipo,
                "Ubicación": inc.ubicacion,
                "Autor": inc.autor,
                "Estado": inc.estado
            })
        return pd.DataFrame(datos)


# ==========================================
# 2. SERVICIOS SIMULADOS
# ==========================================

class SistemaSSO:
    def __init__(self, base_datos_mock: dict):
        self.db = base_datos_mock

    def validar_acceso_corporativo(self, email: str, password: str) -> Usuario | None:
        if not (email.endswith("@urjc.es") or email.endswith("@alumnos.urjc.es")):
            st.error("Error: El dominio del correo no pertenece a la URJC.")
            return None

        usuario = self.db.get(email)
        if usuario and usuario.password == password:
            es_alumno = (usuario.obtener_rol() == "Estudiante")

            if es_alumno and not email.endswith("@alumnos.urjc.es"):
                st.error("Error: Los estudiantes deben usar el dominio @alumnos.urjc.es")
                return None
            if not es_alumno and not email.endswith("@urjc.es"):
                st.error("Error: El personal PDI/PTGAS debe usar el dominio @urjc.es")
                return None
            return usuario
        return None


# ==========================================
# 3. CONFIGURACIÓN DEL ENTORNO Y ESTADO
# ==========================================

def inicializar_datos():
    """Inicializa la base de datos simulada y el gestor de incidencias en memoria."""
    if 'db_usuarios' not in st.session_state:
        st.session_state.db_usuarios = {
            "e.martinez@alumnos.urjc.es": Estudiante("Elena Martínez", "elenam", "e.martinez@alumnos.urjc.es", "123"),
            "juan.perez@urjc.es": PDI("Juan Pérez", "jperez", "juan.perez@urjc.es", "123"),
            "admin.sistemas@urjc.es": PTGAS("Ana Gómez", "anag", "admin.sistemas@urjc.es", "123", administrador=True)
        }

    # Inicializar la lista global de incidencias simulando una tabla en BBDD
    if 'incidencias' not in st.session_state:
        st.session_state.incidencias = []


# ==========================================
# 4. VISTAS DE INTERFAZ (STREAMLIT)
# ==========================================

def mostrar_pantalla_login(sso: SistemaSSO):
    st.title("Senda URJC - Acceso Seguro")

    with st.form("login_form"):
        email_input = st.text_input("Correo Corporativo (@urjc.es o @alumnos.urjc.es)")
        password_input = st.text_input("Contraseña", type="password")
        submit_btn = st.form_submit_button("Iniciar Sesión")

        if submit_btn:
            if not email_input or not password_input:
                st.warning("Por favor, rellena todos los campos.")
            else:
                usuario_validado = sso.validar_acceso_corporativo(email_input, password_input)
                if usuario_validado:
                    st.session_state.usuario_actual = usuario_validado
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Inténtalo de nuevo.")


def vista_reportar_incidencia():
    st.header("🚨 Reportar Nueva Incidencia")
    st.markdown("Ayúdanos a mantener un campus seguro. Rellena los datos de la incidencia.")

    usuario: Usuario = st.session_state.usuario_actual

    with st.form("form_incidencia", clear_on_submit=True):
        tipo_opciones = ["Farola fundida", "Zona solitaria/miedo", "Obstáculo en la vía", "Punto con dificultad"]
        tipo_seleccionado = st.selectbox("Tipo de Incidencia", options=tipo_opciones)

        ubicacion = st.text_input("Ubicación exacta (Ej: Parking Edificio Ampliación, Aulario 2...)")

        # Mostramos fecha y hora actual como referencia visual (readonly)
        ahora = datetime.datetime.now()
        col1, col2 = st.columns(2)
        col1.text_input("Fecha", value=ahora.strftime("%d/%m/%Y"), disabled=True)
        col2.text_input("Hora", value=ahora.strftime("%H:%M"), disabled=True)

        submit_incidencia = st.form_submit_button("Enviar Reporte")

        if submit_incidencia:
            if not ubicacion.strip():
                st.error("Por favor, especifica la ubicación de la incidencia.")
            else:
                # El usuario actúa como creador de la incidencia
                nueva_incidencia = usuario.reportar_incidencia(tipo=tipo_seleccionado, ubicacion=ubicacion)

                # Guardamos en la base de datos simulada
                st.session_state.incidencias.append(nueva_incidencia)

                st.success(
                    f"¡Incidencia reportada con éxito! Se ha generado el ticket: **{nueva_incidencia.ticket_id}**")


def vista_panel_administraciones():
    st.header("🛠️ Panel de Administraciones")
    st.markdown("Gestión y monitorización de tickets activos en el campus.")

    # Extraemos las incidencias y usamos el método de la interfaz
    df_tickets = PanelAdministraciones.listar_tickets_pendientes(st.session_state.incidencias)

    if df_tickets.empty:
        st.info("No hay incidencias reportadas en el sistema en este momento.")
    else:
        # Mostramos el DataFrame de pandas de forma interactiva
        st.dataframe(df_tickets, use_container_width=True, hide_index=True)


def mostrar_interfaz_principal():
    usuario: Usuario = st.session_state.usuario_actual
    rol = usuario.obtener_rol()
    es_admin = (rol == "PTGAS") and getattr(usuario, 'administrador', False)

    # Menú Lateral (Sidebar)
    with st.sidebar:
        st.title("Senda URJC")
        st.write(f"👤 **{usuario.nombre}** ({rol})")
        st.divider()

        # Opciones de navegación base
        opciones_menu = ["🏠 Inicio", "🚨 Reportar Incidencia"]

        # Añadir opción de Admin condicionalmente
        if es_admin:
            opciones_menu.append("🛠️ Panel Administraciones")

        seleccion = st.radio("Menú de Navegación", opciones_menu)

        st.divider()
        if st.button("Cerrar Sesión", use_container_width=True):
            del st.session_state.usuario_actual
            st.rerun()

    # Enrutamiento basado en la selección del Sidebar
    if seleccion == "🏠 Inicio":
        st.title(f"¡Bienvenido/a, {usuario.nombre}!")
        st.write("Utiliza el menú lateral para navegar por las distintas opciones de la aplicación.")

    elif seleccion == "🚨 Reportar Incidencia":
        vista_reportar_incidencia()

    elif seleccion == "🛠️ Panel Administraciones" and es_admin:
        vista_panel_administraciones()


def main():
    st.set_page_config(page_title="Senda URJC", page_icon="🛡️", layout="wide")
    inicializar_datos()
    sso = SistemaSSO(st.session_state.db_usuarios)

    if 'usuario_actual' not in st.session_state:
        mostrar_pantalla_login(sso)
    else:
        mostrar_interfaz_principal()


if __name__ == "__main__":
    main()
