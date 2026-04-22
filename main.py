import streamlit as st


# ==========================================
# 1. DEFINICIÓN DE CLASES (MODELO DE DOMINIO)
# ==========================================

class Usuario:
    """Clase base para todos los usuarios del sistema Senda URJC."""

    def __init__(self, nombre: str, nick: str, email_corporativo: str, password: str):
        self.nombre = nombre
        self.nick = nick
        self.email_corporativo = email_corporativo
        self.password = password  # Simulado para el SSO

    def obtener_rol(self) -> str:
        """Devuelve el nombre de la clase hija para identificar el rol."""
        return self.__class__.__name__


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


# ==========================================
# 2. SERVICIOS SIMULADOS
# ==========================================

class SistemaSSO:
    """Simulación del Sistema de Single Sign-On (SSO) de la Universidad."""

    def __init__(self, base_datos_mock: dict):
        self.db = base_datos_mock

    def validar_acceso_corporativo(self, email: str, password: str) -> Usuario | None:
        """
        Valida el dominio del email corporativo y verifica credenciales.
        Retorna el objeto Usuario si es exitoso, o None si falla.
        """
        # 1. Validación estricta de dominio según el rol esperado
        if not (email.endswith("@urjc.es") or email.endswith("@alumnos.urjc.es")):
            st.error("Error: El dominio del correo no pertenece a la URJC.")
            return None

        # 2. Búsqueda en la base de datos simulada y validación de contraseña
        usuario = self.db.get(email)
        if usuario and usuario.password == password:

            # SOLUCIÓN: Usar string matching en lugar de isinstance()
            # para evitar problemas con la recarga de clases de Streamlit
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
# 3. CONFIGURACIÓN DEL ENTORNO Y DATOS MOCK
# ==========================================

def inicializar_datos():
    """Inicializa la base de datos simulada en memoria si no existe."""
    if 'db_usuarios' not in st.session_state:
        # Instanciamos los 3 usuarios "quemados" solicitados
        st.session_state.db_usuarios = {
            "e.martinez@alumnos.urjc.es": Estudiante(
                nombre="Elena Martínez",
                nick="elenam",
                email_corporativo="e.martinez@alumnos.urjc.es",
                password="123"
            ),
            "juan.perez@urjc.es": PDI(
                nombre="Juan Pérez",
                nick="jperez",
                email_corporativo="juan.perez@urjc.es",
                password="123"
            ),
            "admin.sistemas@urjc.es": PTGAS(
                nombre="Ana Gómez",
                nick="anag",
                email_corporativo="admin.sistemas@urjc.es",
                password="123",
                administrador=True
            )
        }


# ==========================================
# 4. INTERFAZ GRÁFICA (STREAMLIT)
# ==========================================

def mostrar_pantalla_login(sso: SistemaSSO):
    st.title("Senda URJC - Acceso Seguro")
    st.markdown("Por favor, identifícate con tu cuenta universitaria.")

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
                    st.rerun()  # Recarga la app para mostrar la pantalla de bienvenida
                else:
                    st.error("Credenciales incorrectas. Inténtalo de nuevo.")


def mostrar_pantalla_bienvenida():
    usuario: Usuario = st.session_state.usuario_actual
    rol = usuario.obtener_rol()

    st.title(f"¡Bienvenido/a a Senda URJC, {usuario.nombre}!")
    st.success("Sesión iniciada correctamente.")

    # Tarjeta de información del usuario
    st.write("### Tu Perfil")
    st.write(f"- **Rol:** {rol}")
    st.write(f"- **Nickname:** {usuario.nick}")
    st.write(f"- **Email:** {usuario.email_corporativo}")

    # Lógica específica si es administrador
    if isinstance(usuario, PTGAS) and getattr(usuario, 'administrador', False):
        st.info(
            "🛠️ **Modo Administrador Activo**: Tienes acceso al Panel de Administraciones y gestión de incidencias.")

    st.divider()

    # CU-02: Cerrar Sesión
    if st.button("Cerrar Sesión"):
        del st.session_state.usuario_actual
        st.rerun()


def main():
    st.set_page_config(page_title="Senda URJC", page_icon="🛡️")

    # 1. Inicializar datos mockeados
    inicializar_datos()

    # 2. Instanciar el servicio SSO
    sso = SistemaSSO(st.session_state.db_usuarios)

    # 3. Lógica de enrutamiento (Routing) basada en la sesión
    if 'usuario_actual' not in st.session_state:
        mostrar_pantalla_login(sso)
    else:
        mostrar_pantalla_bienvenida()


if __name__ == "__main__":
    main()