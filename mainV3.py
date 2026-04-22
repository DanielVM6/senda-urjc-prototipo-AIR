import streamlit as st
import datetime
import uuid
import pandas as pd
import time


# ==========================================
# 1. DEFINICIÓN DE CLASES (MODELO DE DOMINIO)
# ==========================================

class ContactoConfianza:
    """Representa a una persona que recibirá alertas en caso de emergencia."""

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
    """Núcleo lógico de seguridad (CU-07, CU-10)."""

    def __init__(self, tiempo_espera: int = 15):
        self.tiempo_espera = tiempo_espera  # Reducido para pruebas rápidas

    def detectar_desvio(self):
        """Simula la detección de una anomalía en la ruta GPS."""
        return True

    def emitir_prealerta_vibracion(self):
        """Simula la señal háptica en el dispositivo móvil."""
        st.toast("📳 ¡Vibración de Prealerta emitida!")

    def disparar_alerta_automatica(self, usuario, contacto):
        """Notifica al ServicioSeguridadCampus y al contacto de confianza."""
        mensaje = f"🚨 ALERTA CRÍTICA: El usuario {usuario.nombre} no responde. " \
                  f"Enviando coordenadas al Servicio de Seguridad URJC y a {contacto.nombre} ({contacto.telefono})."
        return mensaje


class Usuario:
    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str):
        self.nombre = nombre
        self.nick = nick
        self.email_corporativo = email_corporativo
        self.password = password
        self.contacto = ContactoConfianza("Familiar Directo", "600000000")

    def obtener_rol(self) -> str:
        return self.__class__.__name__

    def reportar_incidencia(self, tipo: str, ubicacion: str) -> Incidencia:
        return Incidencia(tipo, ubicacion, self.nick)


# Herencia de Usuarios
class Estudiante(Usuario): pass


class PDI(Usuario): pass


class PTGAS(Usuario):
    def __init__(self, nombre, nick, email, pwd, administrador=False):
        super().__init__(nombre, nick, email, pwd)
        self.administrador = administrador


# ==========================================
# 2. SERVICIOS Y LÓGICA DE NEGOCIO
# ==========================================

class SistemaSSO:
    def __init__(self, db):
        self.db = db

    def validar_acceso(self, email, password):
        if not (email.endswith("@urjc.es") or email.endswith("@alumnos.urjc.es")): return None
        u = self.db.get(email)
        if u and u.password == password: return u
        return None


# ==========================================
# 3. CONFIGURACIÓN DEL ENTORNO
# ==========================================

def inicializar_datos():
    if 'db_usuarios' not in st.session_state:
        st.session_state.db_usuarios = {
            "e.martinez@alumnos.urjc.es": Estudiante("Elena Martínez", "elenam", "e.martinez@alumnos.urjc.es", "123"),
            "admin.sistemas@urjc.es": PTGAS("Ana Gómez", "anag", "admin.sistemas@urjc.es", "123", administrador=True)
        }
    if 'incidencias' not in st.session_state: st.session_state.incidencias = []
    if 'voy_contigo_activo' not in st.session_state: st.session_state.voy_contigo_activo = False
    if 'en_prealerta' not in st.session_state: st.session_state.en_prealerta = False


# ==========================================
# 4. VISTAS DE LA APLICACIÓN
# ==========================================

def vista_voy_contigo():
    st.header("🛡️ Modo 'Voy Contigo'")
    controlador = ControladorSeguridad(tiempo_espera=10)  # 10 seg para el test
    usuario = st.session_state.usuario_actual

    if not st.session_state.voy_contigo_activo:
        if st.button("Activar Modo Voy Contigo", type="primary", use_container_width=True):
            st.session_state.voy_contigo_activo = True
            st.rerun()
    else:
        st.success("✅ Compartiendo ubicación en tiempo real con Seguridad Campus.")

        # Simulación de Desvío (Solo si no estamos ya en prealerta)
        if not st.session_state.en_prealerta:
            if st.button("Simular Desvío Brusco (DetectarDesvio)", type="secondary"):
                st.session_state.en_prealerta = True
                controlador.emitir_prealerta_vibracion()
                st.rerun()

            if st.button("Desactivar Modo", use_container_width=True):
                st.session_state.voy_contigo_activo = False
                st.rerun()

        # Protocolo de Prealerta (CU-10)
        if st.session_state.en_prealerta:
            st.warning("### ⚠️ ¿ESTÁS BIEN? \n Se ha detectado un desvío o parada inusual.")

            placeholder_timer = st.empty()
            col1, col2 = st.columns(2)

            btn_bien = col1.button("✅ ESTOY BIEN", use_container_width=True)

            # Lógica de cuenta atrás
            for t in range(controlador.tiempo_espera, -1, -1):
                if btn_bien:
                    st.session_state.en_prealerta = False
                    st.success("Alerta cancelada. Continuando ruta...")
                    time.sleep(1)
                    st.rerun()

                placeholder_timer.metric("Tiempo para Alerta Automática", f"{t}s")
                time.sleep(1)

                if t == 0:
                    st.error(controlador.disparar_alerta_automatica(usuario, usuario.contacto))
                    st.session_state.en_prealerta = False
                    st.session_state.voy_contigo_activo = False
                    break


def vista_reportar_incidencia():
    st.header("🚨 Reportar Incidencia")
    with st.form("f_inc"):
        tipo = st.selectbox("Tipo", ["Farola fundida", "Zona solitaria/miedo", "Obstáculo", "Punto dificultad"])
        ubic = st.text_input("Ubicación")
        if st.form_submit_button("Enviar"):
            inc = st.session_state.usuario_actual.reportar_incidencia(tipo, ubic)
            st.session_state.incidencias.append(inc)
            st.success(f"Registrada: {inc.ticket_id}")


def main():
    st.set_page_config(page_title="Senda URJC", layout="wide")
    inicializar_datos()
    sso = SistemaSSO(st.session_state.db_usuarios)

    if 'usuario_actual' not in st.session_state:
        # Pantalla de Login (simplificada)
        st.title("Senda URJC - Login")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Entrar"):
            user = sso.validar_acceso(e, p)
            if user:
                st.session_state.usuario_actual = user
                st.rerun()
            else:
                st.error("Error de acceso")
    else:
        # Menú Lateral
        user = st.session_state.usuario_actual
        with st.sidebar:
            st.title("Senda URJC")
            st.write(f"👤 {user.nombre} ({user.obtener_rol()})")
            nav = st.radio("Menú", ["🏠 Inicio", "🛡️ Voy Contigo", "🚨 Incidencias", "🛠️ Admin"])

            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                if 'usuario_actual' in st.session_state:
                    del st.session_state.usuario_actual
                st.rerun()

        if nav == "🏠 Inicio":
            st.write(f"Bienvenido/a {user.nombre}")
        elif nav == "🛡️ Voy Contigo":
            vista_voy_contigo()
        elif nav == "🚨 Incidencias":
            vista_reportar_incidencia()
        elif nav == "🛠️ Admin":
            # Usamos obtener_rol() y getattr() para evitar el problema de recarga de Streamlit
            if user.obtener_rol() == "PTGAS" and getattr(user, 'administrador', False):
                df = pd.DataFrame([vars(i) for i in st.session_state.incidencias])
                if not df.empty:
                    st.dataframe(df)
                else:
                    st.info("No hay incidencias reportadas.")
            else:
                st.error("Acceso denegado. Solo para PTGAS Administradores.")


if __name__ == "__main__":
    main()
