import json
import os
from datetime import date, datetime
import matplotlib
matplotlib.use('Agg')  # Fuerza un backend compatible con Kivy
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg as FCK
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.lang import Builder
import io
from PIL import Image as PILImage
from kivy.core.image import Image as CoreImage
import base64



DATA_FILE = "user_profiles.json"
RUTINAS_FILE = "rutinas.json"
PROGRESO_FILE = "progreso.json"
DIETAS_FILE = "dietas.json"
CHATS_FILE = "chats.json"
INGREDIENTES_FILE = "ingredientes.json"

# Opciones predeterminadas
OBJETIVOS_OPTIONS = [
    "Ganar masa muscular",
    "Perder peso",
    "Mantener peso"
]
ACTIVIDAD_OPTIONS = [
    "Sedentario",
    "Activo",
    "Muy activo"
]
RESTRICCIONES_OPTIONS = [
    "Ninguna",
    "Sin gluten",
    "Vegetariano",
    "Vegano"
]
DIAS_SEMANA = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]

# Carga estilos globales y configura color de fondo
Builder.load_file("style.kv")
Window.clearcolor = (0.98, 0.98, 0.98, 1)
Window.size = (400, 700)



def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_progreso():
    return load_json(PROGRESO_FILE)


def save_progreso(data):
    save_json(PROGRESO_FILE, data)


def load_chats():
    return load_json(CHATS_FILE)


def save_chats(data):
    save_json(CHATS_FILE, data)


def load_users():
    users = load_json(DATA_FILE)
    for u in users.values():
        u.setdefault("rutinas_publicadas", [])
        u.setdefault("dietas_publicadas", [])
        u.setdefault("progreso", [])
        u.setdefault("seguidores", [])
        u.setdefault("seguidos", [])
        u.setdefault("dietas_suscritas", [])
        u.setdefault("rutinas_suscritas", [])
    return users


def save_users(data):
    save_json(DATA_FILE, data)


def load_dietas():
    return load_json(DIETAS_FILE)


def save_dietas(data):
    save_json(DIETAS_FILE, data)


def load_rutinas():
    return load_json(RUTINAS_FILE)


def save_rutinas(data):
    save_json(RUTINAS_FILE, data)

def load_ingredientes():
    return load_json(INGREDIENTES_FILE)

def save_ingredientes(data):
    save_json(INGREDIENTES_FILE, data)

def agregar_notificacion(usuario, texto, tipo="general"):
    users = load_users()
    if usuario in users:
        users[usuario].setdefault("notificaciones", [])
        users[usuario]["notificaciones"].append({
            "tipo": tipo,
            "texto": texto,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        save_users(users)



class ListaChatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Tus conversaciones"))

        chats = load_chats()
        actual = self.manager.current_user
        encontrados = set()

        for clave in chats:
            if actual in clave:
                otro = clave.replace(actual, "").replace("|", "")
                encontrados.add(otro)

        if not encontrados:
            self.layout.add_widget(Label(text="Aún no tienes conversaciones."))

        for otro in encontrados:
            btn = Button(text=otro)
            btn.bind(on_press=lambda x, u=otro: self.abrir_chat(u))
            self.layout.add_widget(btn)

        users = load_users()
        seguidos = users.get(actual, {}).get("seguidos", [])
        if seguidos:
            self.layout.add_widget(Label(text="Iniciar chat con seguidor:"))
            sp = Spinner(text="Elegir", values=seguidos)
            sp.bind(text=self.nuevo_chat)
            self.layout.add_widget(sp)
        else:
            self.layout.add_widget(Label(text="No sigues a nadie para chatear."))

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def abrir_chat(self, destinatario):
        self.manager.chat_destino = destinatario
        self.manager.current = "chat"

    def nuevo_chat(self, spinner, texto):
        if texto:
            self.abrir_chat(texto)
            spinner.text = "Elegir"



class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mensajes_label = Label(text="", size_hint_y=None)
        self.input = TextInput(hint_text="Escribe tu mensaje", multiline=False)
        btn_enviar = Button(text="Enviar")
        btn_enviar.bind(on_press=self.enviar_mensaje)

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(self.mensajes_label)
        layout.add_widget(self.input)
        layout.add_widget(btn_enviar)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "lista_chats"))
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def get_clave_chat(self):
        u1 = self.manager.current_user
        u2 = self.manager.chat_destino
        return "|".join(sorted([u1, u2]))

    def on_enter(self):
        self.input.text = ""
        clave = self.get_clave_chat()
        chats = load_chats()
        mensajes = chats.get(clave, [])
        texto = f"Chat con {self.manager.chat_destino}:\n\n"
        for m in mensajes:
            texto += f"{m['emisor']}: {m['texto']}\n"
        self.mensajes_label.text = texto

    def enviar_mensaje(self, instance):
        texto = self.input.text.strip()
        if not texto:
            return

        chats = load_chats()
        clave = self.get_clave_chat()

        if clave not in chats:
            chats[clave] = []

        nuevo = {
            "emisor": self.manager.current_user,
            "texto": texto,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        chats[clave].append(nuevo)
        save_chats(chats)
        self.input.text = ""
        self.on_enter()  # refresca
        if self.manager.chat_destino != self.manager.current_user:
            agregar_notificacion(self.manager.chat_destino, f"{self.manager.current_user} te envió un mensaje", tipo="mensaje")



class NotificacionesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        user = self.manager.current_user
        perfil = load_users().get(user, {})
        notis = perfil.get("notificaciones", [])

        self.layout.add_widget(Label(text="Tus notificaciones:"))

        if not notis:
            self.layout.add_widget(Label(text="No tienes notificaciones."))
        else:
            for n in reversed(notis[-30:]):  # muestra las últimas 30
                texto = f"[{n['fecha']}] {n['texto']}"
                self.layout.add_widget(Label(text=texto, size_hint_y=None))

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)



class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Iniciar Sesión", font_size=22))
        self.username = TextInput(hint_text="Usuario", multiline=False)
        self.password = TextInput(hint_text="Contraseña", multiline=False, password=True)
        layout.add_widget(self.username)
        layout.add_widget(self.password)

        self.msg = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.msg)

        btn_login = Button(text="Entrar")
        btn_login.bind(on_press=self.login)
        layout.add_widget(btn_login)

        btn_register = Button(text="Registrarse")
        btn_register.bind(on_press=lambda x: setattr(self.manager, "current", "registro"))
        layout.add_widget(btn_register)

        self.add_widget(layout)

    def login(self, instance):
        users = load_users()
        u = self.username.text
        p = self.password.text
        if u in users and users[u]["password"] == p:
            self.manager.current_user = u
            self.manager.current = "inicio"
        else:
            self.msg.text = "Usuario o contraseña incorrectos"

class EntrenamientoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Tu entrenamiento actual aparecerá aquí."))
        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class DietaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="")
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Tu Dieta Personalizada"))
        layout.add_widget(self.label)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def on_enter(self):
        perfil = load_users().get(self.manager.current_user, {})
        objetivo = perfil.get("objetivo", "").lower()
        actividad = perfil.get("actividad", "").lower()
        restric = perfil.get("restricciones", "").lower()

        # Dieta base según objetivo
        if "ganar" in objetivo:
            dieta = [
                "Desayuno: Avena con plátano y mantequilla de maní",
                "Almuerzo: Arroz, pollo y palta",
                "Cena: Pasta con atún y ensalada"
            ]
        elif "bajar" in objetivo or "perder" in objetivo:
            dieta = [
                "Desayuno: Yogur descremado con frutas",
                "Almuerzo: Ensalada con pollo y quinoa",
                "Cena: Sopa de verduras y huevo duro"
            ]
        else:
            dieta = [
                "Desayuno: Huevos y pan integral",
                "Almuerzo: Carne magra y arroz integral",
                "Cena: Verduras salteadas con tofu o pollo"
            ]

        # Ajuste por restricciones
        if "vegetarian" in restric:
            dieta = [d.replace("pollo", "tofu").replace("carne", "legumbres").replace("atún", "soya") for d in dieta]
        elif "sin gluten" in restric:
            dieta = [d.replace("pan", "pan sin gluten").replace("pasta", "pasta sin gluten") for d in dieta]

        self.label.text = "\n".join(dieta)


class ProgresoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_peso = TextInput(hint_text="Ingresa tu peso actual (kg)", multiline=False, input_filter="float")
        self.msg = Label(text="")

        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Registrar Progreso"))
        layout.add_widget(self.input_peso)

        btn_guardar = Button(text="Guardar peso")
        btn_guardar.bind(on_press=self.guardar_peso)
        layout.add_widget(btn_guardar)

        layout.add_widget(self.msg)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        layout.add_widget(btn_back)

        self.add_widget(layout)
        self.comentario = TextInput(hint_text="Comentario opcional", multiline=False)
        layout.add_widget(self.comentario)


    def guardar_peso(self, instance):
        peso = self.input_peso.text.strip()
        comentario = self.comentario.text.strip()
        if not peso:
            self.msg.text = "Ingresa un peso válido"
            return

        data = load_users()
        user = self.manager.current_user
        perfil = data.get(user, {})

        fecha = date.today().isoformat()
        nuevo_registro = {
            "fecha": fecha,
            "peso": float(peso),
            "comentario": comentario,
            "likes": []
        }

        perfil["progreso"].append(nuevo_registro)
        perfil["peso"] = float(peso)
        data[user] = perfil
        save_users(data)
        self.msg.text = "Progreso guardado correctamente"

        for seg in perfil.get("seguidores", []):
            agregar_notificacion(seg, f"{user} registró nuevo progreso", tipo="progreso")


        data = load_progreso()
        user = self.manager.current_user
        if user not in data:
            data[user] = []

        fecha = date.today().isoformat()
        data[user].append({"fecha": fecha, "peso": float(peso)})
        save_progreso(data)
        self.msg.text = "Peso guardado correctamente"

class FeedProgresoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Progreso de usuarios que sigues:"))
        data = load_users()
        yo = self.manager.current_user
        seguidos = data[yo].get("seguidos", [])

        posts = []
        for seguido in seguidos:
            for prog in data.get(seguido, {}).get("progreso", []):
                posts.append((seguido, prog))

        if not posts:
            self.layout.add_widget(Label(text="Aún no hay progreso disponible."))

        # ordena por fecha descendente
        posts.sort(key=lambda x: x[1]["fecha"], reverse=True)

        for seguido, prog in posts:
            texto = (
                f"{seguido} - {prog['fecha']}\n"
                f"Peso: {prog['peso']} kg\n"
                f"{prog.get('comentario', '')}\n"
                f"💪 {len(prog.get('likes', []))} reacciones"
            )
            btn = Button(text=texto)
            btn.bind(on_press=lambda x, u=seguido, p=prog["fecha"]: self.dar_like(u, p))
            self.layout.add_widget(btn)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def dar_like(self, username, fecha):
        data = load_users()
        yo = self.manager.current_user

        for prog in data[username]["progreso"]:
            if prog["fecha"] == fecha:
                if yo not in prog["likes"]:
                    prog["likes"].append(yo)
                else:
                    prog["likes"].remove(yo)
                break

        save_users(data)
        self.on_enter()  # refresca la pantalla



class HistorialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Historial de Peso"))

        data = load_progreso()
        user = self.manager.current_user
        pesos = data.get(user, [])

        if not pesos:
            self.layout.add_widget(Label(text="No hay registros aún."))
        else:
            fechas = [p["fecha"] for p in pesos]
            valores = [p["peso"] for p in pesos]

            # Crear figura matplotlib y guardarla como imagen temporal en memoria
            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
            ax.plot(fechas, valores, marker='o')
            ax.set_title("Progreso de peso")
            ax.set_ylabel("Peso (kg)")
            ax.set_xlabel("Fecha")
            ax.grid(True)

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            img = PILImage.open(buf)
            img_data = io.BytesIO()
            img.save(img_data, format='png')
            img_data.seek(0)

            im = CoreImage(img_data, ext='png')
            self.layout.add_widget(Image(texture=im.texture, size_hint_y=None, height=400))

            plt.close(fig)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)


class FeedSocialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Actividad reciente de usuarios que sigues:"))

        users = load_users()
        rutinas = load_rutinas()
        dietas = load_dietas()
        yo = self.manager.current_user
        seguidos = users[yo].get("seguidos", [])

        posts = []

        # Rutinas publicadas por seguidos
        for rid, rutina in rutinas.items():
            if rutina["creador"] in seguidos:
                posts.append({
                    "tipo": "rutina",
                    "usuario": rutina["creador"],
                    "titulo": rutina["titulo"],
                    "descripcion": rutina["descripcion"],
                    "fecha": rid  # como no hay fecha real, usamos el id como aproximación
                })

        # Dietas publicadas por seguidos
        for did, dieta in dietas.items():
            if dieta["creador"] in seguidos:
                posts.append({
                    "tipo": "dieta",
                    "usuario": dieta["creador"],
                    "titulo": dieta["titulo"],
                    "descripcion": dieta["descripcion"],
                    "fecha": did
                })

        # Progreso
        for seguido in seguidos:
            for prog in users[seguido]["progreso"]:
                posts.append({
                    "tipo": "progreso",
                    "usuario": seguido,
                    "peso": prog["peso"],
                    "comentario": prog.get("comentario", ""),
                    "fecha": prog["fecha"]
                })

        if not posts:
            self.layout.add_widget(Label(text="No hay publicaciones todavía."))

        # Ordenar por fecha (simplificado)
        posts.sort(key=lambda x: x["fecha"], reverse=True)

        for post in posts:
            if post["tipo"] == "progreso":
                texto = (
                    f"🟢 {post['usuario']} registró progreso\n"
                    f"Peso: {post['peso']} kg\n"
                    f"{post['comentario']}\n"
                    f"Fecha: {post['fecha']}"
                )
            elif post["tipo"] == "rutina":
                texto = (
                    f"💪 {post['usuario']} publicó una rutina\n"
                    f"{post['titulo']}: {post['descripcion']}"
                )
            elif post["tipo"] == "dieta":
                texto = (
                    f"🥗 {post['usuario']} publicó una dieta\n"
                    f"{post['titulo']}: {post['descripcion']}"
                )
            else:
                texto = "Publicación desconocida"

            self.layout.add_widget(Button(text=texto, size_hint_y=None, height=100))

        btn_back = Button(text="Volver", size_hint_y=None, height=50)
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)


class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = {}
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Crear Usuario", font_size=22))

        campos = [
            ("Usuario", "usuario"),
            ("Contraseña", "password"),
            ("Nombre completo", "nombre"),
            ("Edad", "edad"),
            ("Peso (kg)", "peso")
        ]

        for label, key in campos:
            ti = TextInput(hint_text=label, multiline=False, password=(key == "password"))
            self.inputs[key] = ti
            layout.add_widget(ti)

        self.objetivo = Spinner(text="Objetivo", values=OBJETIVOS_OPTIONS)
        self.actividad = Spinner(text="Nivel de actividad", values=ACTIVIDAD_OPTIONS)
        self.restricciones = Spinner(text="Restricciones alimenticias", values=RESTRICCIONES_OPTIONS)
        layout.add_widget(self.objetivo)
        layout.add_widget(self.actividad)
        layout.add_widget(self.restricciones)

        self.msg = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.msg)

        btn_save = Button(text="Registrar")
        btn_save.bind(on_press=self.registrar)
        layout.add_widget(btn_save)

        btn_back = Button(text="Volver al login")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "login"))
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def registrar(self, instance):
        data = {k: v.text for k, v in self.inputs.items()}
        data["objetivo"] = self.objetivo.text
        data["actividad"] = self.actividad.text
        data["restricciones"] = self.restricciones.text
        usuario = data["usuario"]
        clave = data["password"]

        if (
            not usuario
            or not clave
            or self.objetivo.text == "Objetivo"
            or self.actividad.text == "Nivel de actividad"
            or self.restricciones.text == "Restricciones alimenticias"
        ):
            self.msg.text = "Completa todos los campos"
            return

        users = load_users()
        if usuario in users:
            self.msg.text = "El usuario ya existe"
            return
        
        data["rutinas_publicadas"] = []
        data["dietas_publicadas"] = []
        data["progreso"] = []
        data["seguidores"] = []
        data["seguidos"] = []
        data["notificaciones"] = []
        data["dietas_suscritas"] = []
        data["rutinas_suscritas"] = []


        users[usuario] = data
        save_users(users)
        self.manager.current_user = usuario
        self.manager.current = "inicio"


class VerPerfilAjenoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.info = Label(text="")
        self.msg = Label(text="", color=(0, 1, 0, 1))
        self.btn_follow = Button(text="Seguir")
        self.btn_msg = Button(text="Enviar mensaje")
        self.btn_msg.bind(on_press=self.enviar_mensaje)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(self.btn_msg)


        
        layout.add_widget(self.info)
        layout.add_widget(self.btn_follow)
        layout.add_widget(self.msg)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "buscar_usuarios"))
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def enviar_mensaje(self, instance):
        self.manager.chat_destino = self.manager.perfil_visto
        self.manager.current = "chat"


    def on_enter(self):
        users = load_users()
        rutinas = load_rutinas()
        dietas = load_dietas()
        perfil = users.get(self.manager.perfil_visto, {})
        yo = self.manager.current_user
        otro = self.manager.perfil_visto

        info = [
            f"Usuario: {otro}",
            f"Nombre: {perfil.get('nombre', '')}",
            f"Objetivo: {perfil.get('objetivo', '')}",
            f"Seguidores: {len(perfil.get('seguidores', []))}",
            f"Seguidos: {len(perfil.get('seguidos', []))}",
            "",
            "🔹 Rutinas Publicadas:"
        ]

        for rid in perfil.get("rutinas_publicadas", []):
            r = rutinas.get(rid)
            if r:
                info.append(f"- {r['titulo']}: {r['descripcion']}")

        info.append("\n🔹 Dietas Publicadas:")
        for did in perfil.get("dietas_publicadas", []):
            d = dietas.get(did)
            if d:
                info.append(f"- {d['titulo']}: {d['descripcion']}")

        info.append("\n🔹 Progreso:")
        for p in perfil.get("progreso", []):
            linea = f"{p['fecha']} - {p['peso']} kg"
            if p.get("comentario"):
                linea += f" ({p['comentario']})"
            info.append(linea)

        self.info.text = "\n".join(info)

        if yo in perfil.get("seguidores", []):
            self.btn_follow.text = "Dejar de seguir"
        else:
            self.btn_follow.text = "Seguir"

        self.btn_follow.unbind(on_press=self.toggle_follow)
        self.btn_follow.bind(on_press=self.toggle_follow)


    def toggle_follow(self, instance):
        users = load_users()
        yo = self.manager.current_user
        otro = self.manager.perfil_visto

        if yo == otro:
            self.msg.text = "No puedes seguirte a ti mismo"
            return

        perfil_yo = users[yo]
        perfil_otro = users[otro]

        if yo in perfil_otro["seguidores"]:
            perfil_otro["seguidores"].remove(yo)
            perfil_yo["seguidos"].remove(otro)
            self.msg.text = f"Dejaste de seguir a {otro}"
        else:
            perfil_otro["seguidores"].append(yo)
            agregar_notificacion(otro, f"{yo} comenzó a seguirte", tipo="seguimiento")
            perfil_yo["seguidos"].append(otro)
            self.msg.text = f"Ahora sigues a {otro}"

        save_users(users)
        self.on_enter()  # refresca los datos


class BuscarUsuariosScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.search = TextInput(hint_text="Buscar usuario")
        btn_search = Button(text="Buscar")
        btn_search.bind(on_press=self.do_search)
        self.result_area = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.result_area.bind(minimum_height=self.result_area.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.result_area)
        self.layout.add_widget(self.search)
        self.layout.add_widget(btn_search)
        self.layout.add_widget(scroll)
        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def on_enter(self):
        self.do_search()

    def do_search(self, *args):
        query = self.search.text.lower() if hasattr(self, 'search') else ''
        self.result_area.clear_widgets()
        users = load_users()
        current = self.manager.current_user
        for username, data in users.items():
            if username == current or query not in username.lower():
                continue
            row = BoxLayout(size_hint_y=None, height=40)
            row.add_widget(Label(text=username))
            btn_chat = Button(text="Chat", size_hint_x=None, width=60)
            btn_chat.bind(on_press=lambda x, u=username: self.abrir_chat(u))
            row.add_widget(btn_chat)
            btn_perfil = Button(text="Perfil", size_hint_x=None, width=70)
            btn_perfil.bind(on_press=lambda x, u=username: self.ver_perfil_ajeno(u))
            row.add_widget(btn_perfil)
            follow_text = "Seguir" if current not in data.get('seguidores', []) else "Dejar de seguir"
            btn_follow = Button(text=follow_text, size_hint_x=None, width=120)
            btn_follow.bind(on_press=lambda x, u=username: self.toggle_follow(u))
            row.add_widget(btn_follow)
            self.result_area.add_widget(row)

    def toggle_follow(self, username):
        users = load_users()
        yo = self.manager.current_user
        perfil_yo = users.get(yo, {})
        perfil_otro = users.get(username, {})
        if yo in perfil_otro.get('seguidores', []):
            perfil_otro['seguidores'].remove(yo)
            perfil_yo.get('seguidos', []).remove(username)
        else:
            perfil_otro.setdefault('seguidores', []).append(yo)
            perfil_yo.setdefault('seguidos', []).append(username)
            agregar_notificacion(username, f"{yo} comenzó a seguirte", tipo="seguimiento")
        users[yo] = perfil_yo
        users[username] = perfil_otro
        save_users(users)
        self.do_search()

    def abrir_chat(self, username):
        self.manager.chat_destino = username
        self.manager.current = "chat"

    def ver_perfil_ajeno(self, username):
        self.manager.perfil_visto = username
        self.manager.current = "ver_perfil_ajeno"


class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="", font_size=18)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        top_bar = BoxLayout(size_hint_y=None, height=40)
        top_bar.add_widget(self.label)
        btn_notif = Button(text="🛎️", size_hint_x=None, width=40)
        btn_notif.bind(on_press=lambda x: setattr(self.manager, "current", "notificaciones"))
        btn_msg = Button(text="💬", size_hint_x=None, width=40)
        btn_msg.bind(on_press=lambda x: setattr(self.manager, "current", "lista_chats"))
        top_bar.add_widget(btn_notif)
        top_bar.add_widget(btn_msg)
        layout.add_widget(top_bar)

        self.menu = BoxLayout(orientation="vertical", spacing=5)
        layout.add_widget(self.menu)
        self.submenus = {}

        self.add_menu_item("👥 Comunidad", [("Feed", "feed_social"), ("📊 Progreso", "feed_progreso"), ("Perfil", "perfil")])
        self.add_menu_item("💬 Chats", [("Chats", "lista_chats"), ("Buscar", "buscar_usuarios")])
        self.add_menu_item("🔔 Notificaciones", [("Ver", "notificaciones")])
        self.add_menu_item("🍽️ Dietas", [("Ver", "ver_dietas"), ("Suscritas", "dietas_suscritas"), ("Publicar", "publicar_dieta"), ("Ingredientes", "libreria_ingredientes")])
        self.add_menu_item("🏋️ Rutinas", [("Ver", "ver_rutinas"), ("Suscritas", "rutinas_suscritas"), ("Publicar", "publicar_rutina")])

        btn_logout = Button(text="Cerrar sesión", size_hint_y=None, height=40)
        btn_logout.bind(on_press=self.logout)
        layout.add_widget(btn_logout)

        self.add_widget(layout)

    def add_menu_item(self, text, subitems):
        header = Button(text=text, size_hint_y=None, height=40)
        header.bind(on_press=lambda x, k=text: self.toggle_submenu(k))
        self.menu.add_widget(header)
        submenu = BoxLayout(orientation="vertical", size_hint_y=None, height=0, opacity=0)
        for label, dest in subitems:
            btn = Button(text=label, size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, d=dest: setattr(self.manager, "current", d))
            submenu.add_widget(btn)
        submenu.cached_height = 40 * len(subitems)
        self.submenus[text] = submenu
        self.menu.add_widget(submenu)

    def toggle_submenu(self, key):
        sub = self.submenus.get(key)
        if sub.height == 0:
            sub.height = sub.cached_height
            sub.opacity = 1
        else:
            sub.height = 0
            sub.opacity = 0

    def on_enter(self):
        perfil = load_users().get(self.manager.current_user, {})
        self.label.text = f"Hola, {perfil.get('nombre', '')}!\nObjetivo: {perfil.get('objetivo', '')}"

    def logout(self, instance):
        self.manager.current_user = None
        self.manager.current = "login"

class PublicarDietaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.titulo = TextInput(hint_text="Título de la dieta", multiline=False)
        self.descripcion = TextInput(hint_text="Descripción", multiline=False)
        self.ingredientes = TextInput(hint_text="Ingredientes (uno por línea)", multiline=True)
        self.pasos = TextInput(hint_text="Pasos de preparación (uno por línea)", multiline=True)
        self.objetivo = Spinner(text="Objetivo", values=OBJETIVOS_OPTIONS)
        self.restricciones = Spinner(text="Restricciones", values=RESTRICCIONES_OPTIONS)
        self.msg = Label(text="")

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Publicar Dieta"))
        layout.add_widget(self.titulo)
        layout.add_widget(self.descripcion)
        layout.add_widget(self.ingredientes)
        layout.add_widget(self.pasos)
        layout.add_widget(self.objetivo)
        layout.add_widget(self.restricciones)
        layout.add_widget(self.msg)

        btn_publicar = Button(text="Publicar")
        btn_publicar.bind(on_press=self.publicar)
        layout.add_widget(btn_publicar)

        btn_volver = Button(text="Volver")
        btn_volver.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        layout.add_widget(btn_volver)

        self.add_widget(layout)

    def publicar(self, instance):
        if (
            not self.titulo.text
            or not self.descripcion.text
            or self.objetivo.text == "Objetivo"
            or self.restricciones.text == "Restricciones"
        ):
            self.msg.text = "Completa todos los campos"
            return

        dietas = load_dietas()
        nueva_id = f"dieta_{len(dietas)+1}"
        ingr = [i.strip().lower() for i in self.ingredientes.text.strip().split("\n") if i.strip()]
        pasos = [p.strip() for p in self.pasos.text.strip().split("\n") if p.strip()]
        ing_data = load_ingredientes()
        total_nutri = {
            "calorias": 0,
            "proteinas": 0,
            "carbohidratos": 0,
            "grasas": 0
        }
        for i in ingr:
            info = ing_data.get(i, {})
            for k in total_nutri:
                total_nutri[k] += info.get(k, 0)
        dieta = {
            "creador": self.manager.current_user,
            "titulo": self.titulo.text,
            "descripcion": self.descripcion.text,
            "ingredientes": ingr,
            "pasos": pasos,
            "objetivo": self.objetivo.text,
            "restricciones": self.restricciones.text,
            "valor_nutricional": total_nutri,
            "calificaciones": [],
            "suscripciones": [],
            "reacciones": {},
            "comentarios": []
        }

        dietas[nueva_id] = dieta
        save_dietas(dietas)

        # agregar al perfil del usuario
        users = load_users()
        perfil = users[self.manager.current_user]
        perfil["dietas_publicadas"].append(nueva_id)
        save_users(users)

        for seg in perfil.get("seguidores", []):
            agregar_notificacion(seg, f"{self.manager.current_user} publicó una dieta", tipo="dieta")

        self.msg.text = "Dieta publicada con éxito."

class VerDietasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Dietas Disponibles"))
        dietas = load_dietas()
        user = load_users().get(self.manager.current_user, {})
        obj = user.get("objetivo")
        restric = user.get("restricciones")

        for did, dieta in dietas.items():
            if dieta.get("objetivo") and obj and dieta.get("objetivo") != obj:
                continue
            if dieta.get("restricciones") and restric and dieta.get("restricciones") not in ("Ninguna", restric):
                continue
            promedio = round(sum(dieta['calificaciones'])/len(dieta['calificaciones']), 1) if dieta['calificaciones'] else 0
            nutri = dieta.get('valor_nutricional', {})
            kcal = nutri.get('calorias', 0)
            p = nutri.get('proteinas', 0)
            c = nutri.get('carbohidratos', 0)
            g = nutri.get('grasas', 0)
            info = (
                f"{dieta['titulo']} - {dieta['descripcion']}\n"
                f"Kcal: {kcal}, P: {p}g C: {c}g G: {g}g, "
                f"Suscriptores: {len(dieta['suscripciones'])}, Calificación: {promedio}/5"
            )
            btn = Button(text=info)
            btn.bind(on_press=lambda x, id=did: self.ver_dieta(id))
            self.layout.add_widget(btn)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def ver_dieta(self, id_dieta):
        self.manager.current_dieta = id_dieta
        self.manager.current = "detalle_dieta"

class DietasSuscritasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Dietas Suscritas"))
        users = load_users()
        dietas = load_dietas()
        perfil = users.get(self.manager.current_user, {})
        for did in perfil.get("dietas_suscritas", []):
            dieta = dietas.get(did)
            if not dieta:
                continue
            promedio = round(sum(dieta['calificaciones'])/len(dieta['calificaciones']),1) if dieta['calificaciones'] else 0
            nutri = dieta.get('valor_nutricional', {})
            kcal = nutri.get('calorias', 0)
            p = nutri.get('proteinas', 0)
            c = nutri.get('carbohidratos', 0)
            g = nutri.get('grasas', 0)
            info = (
                f"{dieta['titulo']} - {dieta['descripcion']}\n"
                f"Kcal: {kcal}, P: {p}g C: {c}g G: {g}g, "
                f"Suscriptores: {len(dieta['suscripciones'])}, Calificación: {promedio}/5"
            )
            btn = Button(text=info)
            btn.bind(on_press=lambda x, id=did: self.ver_dieta(id))
            self.layout.add_widget(btn)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def ver_dieta(self, id_dieta):
        self.manager.current_dieta = id_dieta
        self.manager.current = "detalle_dieta"

class LibreriaIngredientesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Librería de Ingredientes"))

        datos = load_ingredientes()
        for nombre, val in datos.items():
            texto = (
                f"{nombre}: {val.get('calorias',0)} kcal, "
                f"P: {val.get('proteinas',0)}g C: {val.get('carbohidratos',0)}g "
                f"G: {val.get('grasas',0)}g"
            )
            self.layout.add_widget(Label(text=texto))

        self.nombre = TextInput(hint_text="Nombre", multiline=False)
        self.calorias = TextInput(hint_text="Calorías", multiline=False, input_filter='float')
        self.proteinas = TextInput(hint_text="Proteínas", multiline=False, input_filter='float')
        self.carbs = TextInput(hint_text="Carbohidratos", multiline=False, input_filter='float')
        self.grasas = TextInput(hint_text="Grasas", multiline=False, input_filter='float')

        btn_add = Button(text="Agregar/Actualizar")
        btn_add.bind(on_press=self.agregar)

        self.layout.add_widget(self.nombre)
        self.layout.add_widget(self.calorias)
        self.layout.add_widget(self.proteinas)
        self.layout.add_widget(self.carbs)
        self.layout.add_widget(self.grasas)
        self.layout.add_widget(btn_add)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'inicio'))
        self.layout.add_widget(btn_back)

    def agregar(self, instance):
        nombre = self.nombre.text.strip().lower()
        cal = self.calorias.text.strip()
        pro = self.proteinas.text.strip()
        carb = self.carbs.text.strip()
        gra = self.grasas.text.strip()
        if not nombre or not cal:
            return
        data = load_ingredientes()
        data[nombre] = {
            "calorias": float(cal),
            "proteinas": float(pro) if pro else 0,
            "carbohidratos": float(carb) if carb else 0,
            "grasas": float(gra) if gra else 0
        }
        save_ingredientes(data)
        self.nombre.text = ""
        self.calorias.text = ""
        self.proteinas.text = ""
        self.carbs.text = ""
        self.grasas.text = ""
        self.on_enter()

class DetalleDietaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="")
        self.spinner = Spinner(text="Califica (1-5)", values=("1", "2", "3", "4", "5"))
        self.msg = Label(text="")

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(self.label)
        layout.add_widget(self.spinner)

        layout.add_widget(Label(text="Reacciona:"))
        emoji_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
        for emoji in ["💪", "🔥", "🙌"]:
            btn = Button(text=emoji)
            btn.bind(on_press=self.reaccionar)
            emoji_bar.add_widget(btn)
        layout.add_widget(emoji_bar)


        

        btn_subs = Button(text="Suscribirse a esta dieta")
        btn_subs.bind(on_press=self.suscribirse)
        layout.add_widget(btn_subs)

        btn_rate = Button(text="Enviar Calificación")
        btn_rate.bind(on_press=self.calificar)
        layout.add_widget(btn_rate)

        layout.add_widget(self.msg)

        layout.add_widget(Label(text="Comentarios:"))
        self.comments_label = Label(text="", size_hint_y=None)
        layout.add_widget(self.comments_label)

        self.input_comentario = TextInput(hint_text="Escribe un comentario", multiline=False)
        layout.add_widget(self.input_comentario)

        btn_comentar = Button(text="Comentar")
        btn_comentar.bind(on_press=self.comentar)
        layout.add_widget(btn_comentar)


        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "ver_dietas"))
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def reaccionar(self, instance):
        emoji = instance.text
        dietas = load_dietas()
        dieta = dietas[self.manager.current_dieta]
        user = self.manager.current_user
        dieta["reacciones"][user] = emoji
        save_dietas(dietas)
        self.msg.text = f"Reaccionaste con {emoji}"
        self.on_enter()  # refresca
        creador = dieta["creador"]
        if creador != self.manager.current_user:
            agregar_notificacion(creador, f"{self.manager.current_user} reaccionó a tu dieta con {emoji}", tipo="reaccion")



    def on_enter(self):
        dieta = load_dietas().get(self.manager.current_dieta, {})
        info = [dieta.get('titulo', ''), dieta.get('descripcion', '')]
        if dieta.get('ingredientes'):
            info.append("\nIngredientes:")
            info.extend(dieta.get('ingredientes', []))
        if 'valor_nutricional' in dieta:
            vn = dieta['valor_nutricional']
            info.append(
                f"Valor nutricional: {vn.get('calorias',0)} kcal, "
                f"P: {vn.get('proteinas',0)}g C: {vn.get('carbohidratos',0)}g "
                f"G: {vn.get('grasas',0)}g"
            )
        if dieta.get('pasos'):
            info.append("\nPasos:")
            info.extend(dieta.get('pasos', []))
        if dieta.get('comidas'):
            info.append("\nComidas:")
            info.extend(dieta.get('comidas', []))
        self.label.text = "\n".join(info)
        self.msg.text = ""

        reacciones = load_dietas()[self.manager.current_dieta].get("reacciones", {})
        cont = {}
        for e in reacciones.values():
            cont[e] = cont.get(e, 0) + 1
        resumen = "Reacciones: " + "  ".join(f"{e} {c}" for e, c in cont.items())
        self.msg.text = resumen if cont else "Sin reacciones aún"

        dieta = load_dietas().get(self.manager.current_dieta, {})
        comentarios = dieta.get("comentarios", [])
        txt = ""
        for c in comentarios:
            txt += f"{c['usuario']}: {c['texto']}\n"
        self.comments_label.text = txt or "Sin comentarios aún"



    def suscribirse(self, instance):
        dietas = load_dietas()
        dieta = dietas[self.manager.current_dieta]
        user = self.manager.current_user
        users = load_users()
        perfil = users[user]
        perfil.setdefault("dietas_suscritas", [])
        if user not in dieta['suscripciones']:
            dieta['suscripciones'].append(user)
            if self.manager.current_dieta not in perfil["dietas_suscritas"]:
                perfil["dietas_suscritas"].append(self.manager.current_dieta)
            self.msg.text = "Te has suscrito a esta dieta."
        else:
            dieta['suscripciones'].remove(user)
            if self.manager.current_dieta in perfil["dietas_suscritas"]:
                perfil["dietas_suscritas"].remove(self.manager.current_dieta)
            self.msg.text = "Se canceló la suscripción."
        save_dietas(dietas)
        save_users(users)

    def calificar(self, instance):
        nota = int(self.spinner.text) if self.spinner.text.isdigit() else 0
        if nota in range(1, 6):
            dietas = load_dietas()
            dieta = dietas[self.manager.current_dieta]
            dieta['calificaciones'].append(nota)
            save_dietas(dietas)
            self.msg.text = "Calificación enviada."
        else:
            self.msg.text = "Selecciona una calificación válida."
    
    def comentar(self, instance):
        texto = self.input_comentario.text.strip()
        if not texto:
            return

        dietas = load_dietas()
        dieta = dietas[self.manager.current_dieta]
        dieta["comentarios"].append({
            "usuario": self.manager.current_user,
            "texto": texto,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        })
        save_dietas(dietas)
        self.input_comentario.text = ""
        self.on_enter()  # refresca comentarios



class PublicarRutinaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.titulo = TextInput(hint_text="Título de la rutina", multiline=False)
        self.descripcion = TextInput(hint_text="Descripción", multiline=False)
        self.ejercicios = TextInput(hint_text="Ejercicios (separados por coma)", multiline=False)
        self.dia = Spinner(text="Día de la semana", values=DIAS_SEMANA)
        self.objetivo = Spinner(text="Objetivo", values=OBJETIVOS_OPTIONS)
        self.grupos = TextInput(hint_text="Grupos musculares", multiline=False)
        self.msg = Label(text="")

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Publicar Rutina"))
        layout.add_widget(self.titulo)
        layout.add_widget(self.descripcion)
        layout.add_widget(self.ejercicios)
        layout.add_widget(self.dia)
        layout.add_widget(self.objetivo)
        layout.add_widget(self.grupos)
        layout.add_widget(self.msg)

        btn_publicar = Button(text="Publicar")
        btn_publicar.bind(on_press=self.publicar)
        layout.add_widget(btn_publicar)

        btn_volver = Button(text="Volver")
        btn_volver.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        layout.add_widget(btn_volver)

        self.add_widget(layout)

    def publicar(self, instance):
        if (
            not self.titulo.text
            or not self.descripcion.text
            or self.dia.text == "Día de la semana"
            or self.objetivo.text == "Objetivo"
        ):
            self.msg.text = "Completa todos los campos"
            return

        rutinas = load_rutinas()
        nueva_id = f"rutina_{len(rutinas)+1}"
        rutina = {
            "creador": self.manager.current_user,
            "titulo": self.titulo.text,
            "descripcion": self.descripcion.text,
            "ejercicios": [e.strip() for e in self.ejercicios.text.split(",") if e.strip()],
            "dia": self.dia.text,
            "objetivo": self.objetivo.text,
            "grupos": [g.strip() for g in self.grupos.text.split(",") if g.strip()],
            "calificaciones": [],
            "suscripciones": [],
            "reacciones": {},
            "comentarios": []
        }

        rutinas[nueva_id] = rutina
        save_rutinas(rutinas)
        users = load_users()
        perfil = users[self.manager.current_user]
        perfil["rutinas_publicadas"].append(nueva_id)
        save_users(users)

        for seg in perfil.get("seguidores", []):
            agregar_notificacion(seg, f"{self.manager.current_user} publicó una rutina", tipo="rutina")

        self.msg.text = "Rutina publicada con éxito."
        
        

class VerRutinasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Rutinas Disponibles"))
        rutinas = load_rutinas()
        user = load_users().get(self.manager.current_user, {})
        obj = user.get("objetivo")
        for rid, rutina in rutinas.items():
            if rutina.get("objetivo") and obj and rutina.get("objetivo") != obj:
                continue
            promedio = round(sum(rutina['calificaciones'])/len(rutina['calificaciones']),1) if rutina['calificaciones'] else 0
            info = f"{rutina['titulo']} - {rutina['descripcion']}\nSuscriptores: {len(rutina['suscripciones'])}, Calificación: {promedio}/5"
            btn = Button(text=info)
            btn.bind(on_press=lambda x, id=rid: self.mostrar_rutina(id))
            self.layout.add_widget(btn)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def mostrar_rutina(self, rutina_id):
        self.manager.current_rutina = rutina_id
        self.manager.current = "detalle_rutina"

class RutinasSuscritasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Rutinas Suscritas"))
        users = load_users()
        rutinas = load_rutinas()
        perfil = users.get(self.manager.current_user, {})
        for rid in perfil.get("rutinas_suscritas", []):
            rutina = rutinas.get(rid)
            if not rutina:
                continue
            promedio = round(sum(rutina['calificaciones'])/len(rutina['calificaciones']),1) if rutina['calificaciones'] else 0
            info = f"{rutina['titulo']} - {rutina['descripcion']}\nSuscriptores: {len(rutina['suscripciones'])}, Calificación: {promedio}/5"
            row = BoxLayout(size_hint_y=None, height=80)
            btn = Button(text=info)
            btn.bind(on_press=lambda x, id=rid: self.mostrar_rutina(id))
            row.add_widget(btn)
            btn_del = Button(text="Cancelar")
            btn_del.bind(on_press=lambda x, id=rid: self.cancelar(id))
            row.add_widget(btn_del)
            self.layout.add_widget(row)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

    def mostrar_rutina(self, rid):
        self.manager.current_rutina = rid
        self.manager.current = "detalle_rutina"

    def cancelar(self, rid):
        users = load_users()
        rutinas = load_rutinas()
        perfil = users.get(self.manager.current_user, {})
        if rid in perfil.get("rutinas_suscritas", []):
            perfil["rutinas_suscritas"].remove(rid)
            rutina = rutinas.get(rid)
            if rutina and self.manager.current_user in rutina.get("suscripciones", []):
                rutina["suscripciones"].remove(self.manager.current_user)
            save_rutinas(rutinas)
            save_users(users)
            self.on_enter()

class PerfilScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="")
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.layout.add_widget(Label(text="Tu Perfil"))
        self.layout.add_widget(self.label)

        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "inicio"))
        self.layout.add_widget(btn_back)

        self.add_widget(self.layout)

    def on_enter(self):
        perfil = load_users().get(self.manager.current_user, {})
        info = [
            f"Nombre: {perfil.get('nombre', '')}",
            f"Edad: {perfil.get('edad', '')}",
            f"Peso actual: {perfil.get('peso', '')} kg",
            f"Objetivo: {perfil.get('objetivo', '')}",
            f"Actividad física: {perfil.get('actividad', '')}",
            f"Restricciones: {perfil.get('restricciones', '')}",
            f"Rutinas publicadas: {len(perfil.get('rutinas_publicadas', []))}",
            f"Dietas publicadas: {len(perfil.get('dietas_publicadas', []))}",
            f"Rutinas suscritas: {len(perfil.get('rutinas_suscritas', []))}",
            f"Dietas suscritas: {len(perfil.get('dietas_suscritas', []))}",
            f"Seguidores: {len(perfil.get('seguidores', []))}",
            f"Seguidos: {len(perfil.get('seguidos', []))}"
        ]
        self.label.text = "\n".join(info)


class DetalleRutinaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="")
        self.spinner = Spinner(text="Califica (1-5)", values=("1", "2", "3", "4", "5"))
        self.msg = Label(text="")

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(self.label)
        layout.add_widget(self.spinner)

        layout.add_widget(Label(text="Reacciona:"))
        emoji_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
        for emoji in ["💪", "🔥", "🙌"]:
            btn = Button(text=emoji)
            btn.bind(on_press=self.reaccionar)
            emoji_bar.add_widget(btn)
        layout.add_widget(emoji_bar)


        

        btn_subs = Button(text="Suscribirse a esta rutina")
        btn_subs.bind(on_press=self.suscribirse)
        layout.add_widget(btn_subs)

        btn_rate = Button(text="Enviar Calificación")
        btn_rate.bind(on_press=self.calificar)
        layout.add_widget(btn_rate)

        layout.add_widget(self.msg)

        layout.add_widget(Label(text="Comentarios:"))

        self.comments_label = Label(text="", size_hint_y=None)
        layout.add_widget(self.comments_label)

        self.input_comentario = TextInput(hint_text="Escribe un comentario", multiline=False)
        layout.add_widget(self.input_comentario)

        btn_comentar = Button(text="Comentar")
        btn_comentar.bind(on_press=self.comentar)
        layout.add_widget(btn_comentar)


        btn_back = Button(text="Volver")
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "ver_rutinas"))
        layout.add_widget(btn_back)
        self.add_widget(layout)
    
    def comentar(self, instance):
        texto = self.input_comentario.text.strip()
        if not texto:
            self.msg.text = "Comentario vacío"
            return

        rutinas = load_rutinas()
        rutina = rutinas[self.manager.current_rutina]
        rutina.setdefault("comentarios", [])
        rutina["comentarios"].append({
            "usuario": self.manager.current_user,
            "texto": texto,
            "fecha": date.today().isoformat()
        })
        save_rutinas(rutinas)

        creador = rutina["creador"]
        if creador != self.manager.current_user:
            agregar_notificacion(creador, f"{self.manager.current_user} comentó en tu rutina: {texto}", tipo="comentario")

        self.msg.text = "Comentario enviado"
        self.input_comentario.text = ""
        self.on_enter()  # refresca los comentarios


    def reaccionar(self, instance):
        emoji = instance.text
        rutinas = load_rutinas()
        rutina = rutinas[self.manager.current_rutina]
        user = self.manager.current_user
        rutina["reacciones"][user] = emoji
        save_rutinas(rutinas)
        self.msg.text = f"Reaccionaste con {emoji}"
        creador = rutina["creador"]
        if creador != self.manager.current_user:
            agregar_notificacion(creador, f"{self.manager.current_user} reaccionó a tu rutina con {emoji}", tipo="reaccion")



    def on_enter(self):
        rutina = load_rutinas().get(self.manager.current_rutina, {})
        ejercicios = "\n".join(rutina.get("ejercicios", []))
        self.label.text = f"{rutina.get('titulo', '')}\n{rutina.get('descripcion', '')}\n\nEjercicios:\n{ejercicios}"
        self.msg.text = ""
        # Mostrar resumen de reacciones
        reacciones = load_rutinas()[self.manager.current_rutina].get("reacciones", {})
        cont = {}
        for e in reacciones.values():
            cont[e] = cont.get(e, 0) + 1
        resumen = " ".join(f"{e} {c}" for e, c in cont.items())
        self.msg.text = resumen or "Sin reacciones aún"

        rutina = load_rutinas().get(self.manager.current_rutina, {})
        comentarios = rutina.get("comentarios", [])
        txt = ""
        for c in comentarios:
            txt += f"{c['usuario']}: {c['texto']}\n"
        self.comments_label.text = txt or "Sin comentarios aún"



    def suscribirse(self, instance):
        rutinas = load_rutinas()
        rutina = rutinas[self.manager.current_rutina]
        user = self.manager.current_user
        users = load_users()
        perfil = users[user]
        perfil.setdefault("rutinas_suscritas", [])
        if user not in rutina['suscripciones']:
            rutina['suscripciones'].append(user)
            if self.manager.current_rutina not in perfil["rutinas_suscritas"]:
                perfil["rutinas_suscritas"].append(self.manager.current_rutina)
            self.msg.text = "Te has suscrito a esta rutina."
        else:
            rutina['suscripciones'].remove(user)
            if self.manager.current_rutina in perfil["rutinas_suscritas"]:
                perfil["rutinas_suscritas"].remove(self.manager.current_rutina)
            self.msg.text = "Se canceló la suscripción."
        save_rutinas(rutinas)
        save_users(users)

    def calificar(self, instance):
        nota = int(self.spinner.text) if self.spinner.text.isdigit() else 0
        if nota in range(1,6):
            rutinas = load_rutinas()
            rutina = rutinas[self.manager.current_rutina]
            rutina['calificaciones'].append(nota)
            save_rutinas(rutinas)
            self.msg.text = "Calificación enviada."
        else:
            self.msg.text = "Selecciona una calificación válida."

class FitnessApp(App):
    def build(self):
        sm = ScreenManager()
        sm.current_user = None
        sm.current_rutina = None

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="registro"))
        sm.add_widget(InicioScreen(name="inicio"))
        sm.add_widget(PublicarRutinaScreen(name="publicar_rutina"))
        sm.add_widget(VerRutinasScreen(name="ver_rutinas"))
        sm.add_widget(DetalleRutinaScreen(name="detalle_rutina"))
        sm.add_widget(RutinasSuscritasScreen(name="rutinas_suscritas"))
        
        # Pantallas agregadas
        sm.add_widget(EntrenamientoScreen(name="entrenamiento"))
        sm.add_widget(DietaScreen(name="dieta"))
        sm.add_widget(ProgresoScreen(name="progreso"))
        sm.add_widget(HistorialScreen(name="historial"))
        sm.add_widget(PerfilScreen(name="perfil"))
        sm.perfil_visto = None  # para ver otros perfiles
        sm.add_widget(BuscarUsuariosScreen(name="buscar_usuarios"))
        sm.add_widget(VerPerfilAjenoScreen(name="ver_perfil_ajeno"))
        sm.current_dieta = None
        sm.add_widget(PublicarDietaScreen(name="publicar_dieta"))
        sm.add_widget(VerDietasScreen(name="ver_dietas"))
        sm.add_widget(DetalleDietaScreen(name="detalle_dieta"))
        sm.add_widget(DietasSuscritasScreen(name="dietas_suscritas"))
        sm.add_widget(LibreriaIngredientesScreen(name="libreria_ingredientes"))
        sm.add_widget(FeedProgresoScreen(name="feed_progreso"))
        sm.add_widget(FeedSocialScreen(name="feed_social"))
        sm.chat_destino = None
        sm.add_widget(ListaChatsScreen(name="lista_chats"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(NotificacionesScreen(name="notificaciones"))








        return sm



if __name__ == "__main__":
    FitnessApp().run()
