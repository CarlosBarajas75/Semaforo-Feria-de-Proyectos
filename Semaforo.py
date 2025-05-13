import tkinter as tk
from tkinter import messagebox, Toplevel, Text, Scrollbar, PhotoImage
import csv
import os
import winsound
from tkinter import ttk
import math

# Config global
tiempos_color = {}  # verde, amarillo, rojo
running = False
remaining_time = 0
total_duration = 0
current_team = ""
current_subject = ""
parpadeo_activo = False
parpadeo_contador = 0
parpadeo_luz_actual = None  # Nueva variable para controlar qué luz parpadea

# Referencias a widgets en ventana secundaria
ventana_visual = None
semaforo_canvas = None
barra_canvas = None
luz_verde = None
luz_amarilla = None
luz_roja = None
barra_rect = None
logo_image = None

# Agregar estas variables globales al inicio del archivo
luces_verdes = []
luces_amarillas = []
luces_rojas = []
etapa_actual = "exposicion"  # puede ser "exposicion" o "preguntas"

# Agregar en las variables globales
etapa_label = None
boton_iniciar_temporizador = None

# Al inicio del archivo, después de los imports
COLORS = {
    'bg_primary': '#1e1e2f',        # Azul-gris oscuro
    'bg_secondary': '#2b2b3c',      # Para marcos y elementos secundarios
    'text_primary': '#E0E0E0',      # Gris claro (mejor que blanco puro)
    'accent_green': '#00c896',      # Verde menta
    'accent_yellow': '#f1c40f',     # Amarillo vibrante
    'accent_red': '#ff4c4c',        # Rojo brillante
    'button_bg': '#3a3a4f',         # Botón más claro
    'button_hover': '#505065',      # Hover más suave
    'entry_bg': '#3a3a4f',          # Campo de texto
    'button_text': '#FFFFFF',
    'border_color': '#5D6D7E'
}


# --- Funciones principales ---
def start_timer():
    global running, remaining_time, current_team, current_subject, total_duration, etapa_actual, tema_equipo
    if running:
        return

    subject = subject_var.get()
    team_name = team_name_var.get().strip()
    tema_equipo = tema_equipo_var.get().strip()

    if not team_name:
        messagebox.showwarning("Advertencia", "Por favor, ingresa el ID del proyecto.")
        return
    if not tema_equipo:
        messagebox.showwarning("Advertencia", "Por favor, ingresa el título del proyecto.")
        return

    if subject == "Informe de proyectos de investigación":
        total_seconds = 20 * 60  # 20 minutos
    elif subject == "Protocolo de proyectos de investigación":
        total_seconds = 15 * 60  # 15 minutos
    else:
        messagebox.showwarning("Advertencia", "Selecciona un evento válido.")
        return

    confirmar = messagebox.askyesno(
        "Confirmar inicio",
        f"¿Deseas abrir la ventana del semáforo para el proyecto '{team_name}' en el evento '{subject}'?\n\nEl temporizador NO iniciará hasta que presiones el botón INICIAR en la ventana del semáforo."
    )
    if not confirmar:
        return

    # Deshabilitar el menú de selección y la entrada de equipo
    subject_menu.config(state='disabled')
    team_entry.config(state='disabled')
    tema_entry.config(state='disabled')

    total_duration = total_seconds
    subject_label.config(text=f"Evento: {subject}")
    team_label.config(text=f"ID-Proyecto: {team_name}")
    remaining_time = total_seconds
    current_team = team_name
    current_subject = subject
    etapa_actual = "exposicion"
    # No poner running = True ni countdown aquí
    abrir_ventana_visual()

def crear_efecto_brillo(canvas, x, y, radio, color):
    # Crear efecto de resplandor
    for i in range(3):
        offset = i * 2
        canvas.create_oval(
            x - radio - offset,
            y - radio - offset,
            x + radio + offset,
            y + radio + offset,
            fill='',
            outline=color,
            stipple='gray50',
            width=1,
            tags='glow'
        )

def animar_transicion(widget, **kwargs):
    # Función para crear animaciones suaves
    steps = 10
    ms_delay = 20
    
    initial = {k: float(widget.cget(k)) for k in kwargs.keys()}
    delta = {k: (float(kwargs[k]) - initial[k])/steps for k in kwargs.keys()}
    
    def _animate(step):
        if step < steps:
            for k in kwargs.keys():
                current = initial[k] + delta[k] * step
                widget.configure(**{k: current})
            widget.after(ms_delay, _animate, step + 1)
    
    _animate(0)

def crear_boton_personalizado(parent, texto, comando):
    btn = tk.Button(
        parent,
        text=texto,
        font=('Segoe UI', 14, 'bold'),
        bg=COLORS['button_bg'],
        fg=COLORS['text_primary'],
        activebackground=COLORS['button_hover'],
        activeforeground=COLORS['text_primary'],
        relief='flat',
        bd=0,
        padx=20,
        pady=10,
        command=comando
    )
    
    def on_enter(e):
        btn.config(
            bg=COLORS['button_hover'],
            relief='solid'
        )
        
    def on_leave(e):
        btn.config(
            bg=COLORS['button_bg'],
            relief='solid'
        )
    
    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    
    return btn

class LuzSemaforo:
    def __init__(self, canvas, x, y, radio, color_apagado, color_encendido):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radio = radio
        self.color_apagado = color_apagado
        self.color_encendido = color_encendido
        self.encendido = False
        self.luz_id = None
        self.brillo_ids = []
        self._crear_luz()
    
    def _crear_luz(self):
        # Crear efecto de profundidad
        self.canvas.create_oval(
            self.x - self.radio - 2,
            self.y - self.radio - 2,
            self.x + self.radio + 2,
            self.y + self.radio + 2,
            fill='black',
            width=0
        )
        
        self.luz_id = self.canvas.create_oval(
            self.x - self.radio,
            self.y - self.radio,
            self.x + self.radio,
            self.y + self.radio,
            fill=self.color_apagado,
            width=0
        )
    
    def encender(self):
        if not self.encendido:
            self._animar_encendido()
    
    def apagar(self):
        if self.encendido:
            self._animar_apagado()
    
    def _animar_encendido(self):
        steps = 10
        for i in range(steps):
            def update(step=i):
                factor = step / steps
                color = self._interpolar_color(
                    self.color_apagado,
                    self.color_encendido,
                    factor
                )
                self.canvas.itemconfig(self.luz_id, fill=color)
                if step == steps - 1:
                    self._crear_efecto_brillo()
            self.canvas.after(50 * i, update)
        self.encendido = True
    
    def _animar_apagado(self):
        steps = 10
        for i in range(steps):
            def update(step=i):
                factor = 1 - (step / steps)
                color = self._interpolar_color(
                    self.color_apagado,
                    self.color_encendido,
                    factor
                )
                self.canvas.itemconfig(self.luz_id, fill=color)
                if step == steps - 1:
                    self._eliminar_efecto_brillo()
            self.canvas.after(50 * i, update)
        self.encendido = False
    
    def _interpolar_color(self, color1, color2, factor):
        # Convertir colores hex a RGB
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Interpolar
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _crear_efecto_brillo(self):
        self._eliminar_efecto_brillo()
        for i in range(3):
            offset = (i + 1) * 3
            brillo_id = self.canvas.create_oval(
                self.x - self.radio - offset,
                self.y - self.radio - offset,
                self.x + self.radio + offset,
                self.y + self.radio + offset,
                fill='',
                outline=self.color_encendido,
                stipple='gray50',
                width=1
            )
            self.brillo_ids.append(brillo_id)
    
    def _eliminar_efecto_brillo(self):
        for brillo_id in self.brillo_ids:
            self.canvas.delete(brillo_id)
        self.brillo_ids = []

def abrir_ventana_visual():
    global ventana_visual, semaforo_canvas, barra_canvas, luz_verde, luz_amarilla, luz_roja, barra_rect, etapa_label, tema_equipo, boton_iniciar_temporizador
    ventana_visual = Toplevel(root)
    ventana_visual.title("Visualizador de Tiempo")
    ventana_visual.geometry("900x700")
    ventana_visual.minsize(600, 400)
    ventana_visual.configure(bg=COLORS['bg_primary'])
    ventana_visual.resizable(True, True)

    frame_horizontal = tk.Frame(ventana_visual, bg=COLORS['bg_primary'])
    frame_horizontal.pack(fill=tk.BOTH, expand=True)

    frame_textos = tk.Frame(frame_horizontal, bg=COLORS['bg_primary'])
    frame_textos.pack(side=tk.LEFT, fill='both', expand=True, padx=(40, 0), pady=40)


    evento_label = tk.Label(frame_textos,
                            text=f"Evento: {current_subject}",
                            font=("Segoe UI", 28, "bold"),
                            bg=COLORS['bg_primary'],
                            fg=COLORS['accent_yellow'],
                            anchor='center', justify='center')
    evento_label.pack(anchor='w', pady=(10, 0))

    equipo_label = tk.Label(frame_textos, 
                           text=f"ID-Proyecto: {current_team}",
                           font=("Segoe UI", 24, "bold"),
                           bg=COLORS['bg_primary'],
                           fg=COLORS['text_primary'],
                           anchor='center', justify='center')
    equipo_label.pack(anchor='w', pady=(10, 0))

    tema_equipo_label = tk.Label(frame_textos,
                                 text=f"Título: {tema_equipo}",
                                 font=("Segoe UI", 20),
                                 bg=COLORS['bg_primary'],
                                 fg=COLORS['text_primary'],
                                 anchor='center', justify='center')
    tema_equipo_label.pack(anchor='w', pady=(0, 10))

    etapa_label = tk.Label(frame_textos,
                          text="EXPOSICIÓN",
                          font=("Segoe UI", 36, "bold"),
                          bg=COLORS['bg_primary'],
                          fg=COLORS['accent_green'],
                          anchor='center', justify='center')
    etapa_label.pack(anchor='w', pady=10)

    # Botón para iniciar el temporizador
    def iniciar_temporizador():
        global running
        if not running:
            running = True
            boton_iniciar_temporizador.config(state='disabled')
            countdown()
    boton_iniciar_temporizador = tk.Button(frame_textos, text="INICIAR TEMPORIZADOR", font=("Segoe UI", 18, "bold"),
                                           bg=COLORS['accent_green'], fg=COLORS['bg_primary'],
                                           activebackground=COLORS['accent_yellow'],
                                           relief='raised', bd=3, command=iniciar_temporizador)
    boton_iniciar_temporizador.pack(anchor='w', pady=(30, 0))

    try:
        banner_image = tk.PhotoImage(file="fpi-round-white.png")
        
        original_width = banner_image.width()
        original_height = banner_image.height()
        
        scale_x = original_width / 300
        scale_y = original_height / 300
        
        if scale_x > 1 or scale_y > 1:
            banner_image = banner_image.subsample(int(scale_x), int(scale_y))
        else:
            banner_image = banner_image.zoom(int(1/scale_x), int(1/scale_y))
        
        banner_label = tk.Label(frame_textos, image=banner_image, bg=COLORS['bg_primary'])
        banner_label.image = banner_image
        banner_label.pack(anchor='w', pady=(20, 0))
        
    except Exception as e:
        print(f"Error al cargar la imagen del banner: {e}")


    frame_semaforo = tk.Frame(frame_horizontal, bg=COLORS['bg_primary'])
    frame_semaforo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    semaforo_canvas = tk.Canvas(frame_semaforo, 
                              bg=COLORS['bg_primary'], 
                              highlightthickness=0, borderwidth=0)
    semaforo_canvas.pack(expand=True, fill=tk.BOTH)

    barra_canvas = tk.Canvas(ventana_visual, 
                           height=10,
                           bg=COLORS['bg_secondary'],
                           highlightthickness=0, borderwidth=0)
    barra_canvas.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
    barra_rect = barra_canvas.create_rectangle(0, 0, 0, 10, 
                                             fill=COLORS['accent_green'],
                                             width=0)

    try:
        logo_image = PhotoImage(file="logo.png")
    except Exception:
        logo_image = None

    semaforo_canvas.bind("<Configure>", dibujar_semaforo)
    dibujar_semaforo()
    ventana_visual.bind("<Escape>", lambda e: ventana_visual.destroy())

def dibujar_semaforo(event=None):
    global luces_verdes, luces_amarillas, luces_rojas
    semaforo_canvas.delete("all")
    w = semaforo_canvas.winfo_width()
    h = semaforo_canvas.winfo_height()

    # Cálculo responsivo: considerar 3 luces + espacios + márgenes
    # Margen mínimo alrededor
    margen = int(min(w, h) * 0.05)
    area_util_w = w - 2 * margen
    area_util_h = h - 2 * margen

    # Queremos 3 círculos y 2 espacios entre ellos, todo dentro del área útil
    # radio + espacio + radio + espacio + radio = area_util_h
    # Definimos proporción espacio/radio (por ejemplo, espacio = 0.5*radio)
    # 3*radio + 2*espacio = area_util_h
    # espacio = k*radio
    # 3*radio + 2*k*radio = area_util_h => radio = area_util_h / (3 + 2*k)
    k = 0.5  # proporción espacio/radio
    radio_h = area_util_h / (3 + 2 * k) / 2  # /2 porque radio es la mitad del diámetro
    radio_w = area_util_w / 3 / 2  # máximo radio para que quepan 3 círculos horizontalmente
    radio = int(min(radio_h, radio_w))
    espacio = int(k * 2 * radio)

    # Recalcular el alto total ocupado por el semáforo
    alto_semaforo = 3 * 2 * radio + 2 * espacio
    offset_y = (h - alto_semaforo) // 2
    cx = w // 2

    luces_verdes = []
    luces_amarillas = []
    luces_rojas = []

    # Carcasa
    carcasa_width = int(radio * 2.8)
    carcasa_height = alto_semaforo + int(radio * 0.4)
    semaforo_canvas.create_rectangle(
        cx - carcasa_width // 2,
        offset_y - int(radio * 0.2),
        cx + carcasa_width // 2,
        offset_y + carcasa_height,
        fill=COLORS['bg_secondary'],
        width=2,
        outline=COLORS['text_primary']
    )
    # Soporte
    soporte_width = int(radio * 0.5)
    soporte_height = int(radio * 1.2)
    semaforo_canvas.create_rectangle(
        cx - soporte_width // 2,
        offset_y + carcasa_height,
        cx + soporte_width // 2,
        offset_y + carcasa_height + soporte_height,
        fill='#95a5a6',
        width=1,
        outline='#7f8c8d'
    )

    # Líneas divisorias
    for i in range(1, 3):
        y_pos = offset_y + i * (2 * radio + espacio) - espacio // 2
        semaforo_canvas.create_line(
            cx - carcasa_width // 2,
            y_pos,
            cx + carcasa_width // 2,
            y_pos,
            fill='#95a5a6',
            width=1
        )

    # Luces
    for idx, color in enumerate([(COLORS['accent_green'], luces_verdes),
                                 (COLORS['accent_yellow'], luces_amarillas),
                                 (COLORS['accent_red'], luces_rojas)]):
        y = offset_y + radio + idx * (2 * radio + espacio)
        luz = LuzSemaforo(
            semaforo_canvas,
            cx,
            y,
            radio,
            "#333333",
            color[0]
        )
        color[1].append(luz)

def parpadear_luz(luz, color_original):
    global parpadeo_contador, parpadeo_luz_actual, parpadeo_activo
    # Si la luz que está parpadeando ya no es la actual, detener parpadeo
    if parpadeo_luz_actual is not luz:
        luz.canvas.itemconfig(luz.luz_id, fill="#333333")
        return
    if parpadeo_contador < 20:  # 10 segundos (20 cambios de 0.5s)
        if parpadeo_contador % 2 == 0:
            luz.canvas.itemconfig(luz.luz_id, fill="#333333")  # Apagar
        else:
            luz.canvas.itemconfig(luz.luz_id, fill=color_original)  # Encender
            # Sonido intermitente al encender
            try:
                winsound.Beep(1200, 120)
            except Exception:
                pass
        parpadeo_contador += 1
        ventana_visual.after(500, lambda: parpadear_luz(luz, color_original))
    else:
        parpadeo_activo = False
        parpadeo_luz_actual = None
        parpadeo_contador = 0

def actualizar_semaforo_y_barra(tiempo_restante):
    global parpadeo_activo, parpadeo_contador, etapa_actual, luces_verdes, luces_amarillas, luces_rojas, remaining_time, parpadeo_luz_actual
    if not ventana_visual or not luces_verdes:
        return

    transcurrido = total_duration - tiempo_restante
    barra_color = COLORS['accent_green']
    TIEMPO_ROJO = 20  # 20 segundos para el rojo en cada etapa

    # Para Protocolo de proyectos de investigación (15 minutos: 5 exposición + 5 preguntas + 5 cambio)
    if current_subject == "Protocolo de proyectos de investigación":
        tiempo_exposicion = 5 * 60   # 5 minutos
        tiempo_preguntas = 5 * 60    # 5 minutos
        tiempo_cambio = 5 * 60       # 5 minutos
        tiempo_total_exp_preg = tiempo_exposicion + tiempo_preguntas
        
        # Etapa de exposición (5 minutos)
        if transcurrido <= tiempo_exposicion:
            if etapa_actual != "exposicion":
                etapa_actual = "exposicion"
                etapa_label.config(text="EXPOSICIÓN", fg=COLORS['accent_green'])
            
            tiempo_restante_etapa = tiempo_exposicion - transcurrido
            tiempo_util = tiempo_exposicion - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6  # ~2:50 minutos
            tiempo_amarillo = tiempo_util * 0.4  # ~1:50 minutos
            
            # Control de luces para exposición
            if transcurrido < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (tiempo_exposicion - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_exposicion - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    # Si ya no debe parpadear, asegurarse de apagar el parpadeo
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            elif transcurrido < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = transcurrido / tiempo_exposicion

        # Etapa de preguntas (5 minutos)
        elif transcurrido <= tiempo_total_exp_preg:
            if etapa_actual != "preguntas":
                # ALERTA para confirmar inicio de preguntas
                if messagebox.askyesno("Sección de preguntas", "¿Están listos para iniciar la sección de preguntas?"):
                    etapa_actual = "preguntas"
                    etapa_label.config(text="PREGUNTAS", fg=COLORS['accent_yellow'])
                else:
                    # Si no están listos, regresar el tiempo 1 segundo para volver a preguntar en el siguiente ciclo
                    remaining_time += 1
                    return
            
            tiempo_transcurrido_preguntas = transcurrido - tiempo_exposicion
            tiempo_util = tiempo_preguntas - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6
            tiempo_amarillo = tiempo_util * 0.4
            tiempo_restante_etapa = tiempo_preguntas - tiempo_transcurrido_preguntas
            
            # Control de luces para preguntas
            if tiempo_transcurrido_preguntas < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                if tiempo_restante_etapa <= (tiempo_preguntas - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_preguntas - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                            
            elif tiempo_transcurrido_preguntas < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                            
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = tiempo_transcurrido_preguntas / tiempo_preguntas

        # Etapa de cambio (5 minutos)
        else:
            if etapa_actual != "cambio":
                # ALERTA para confirmar inicio de cambio de equipo
                if messagebox.askyesno("Cambio de equipo", "¿Están listos para el cambio de equipo?"):
                    etapa_actual = "cambio"
                    etapa_label.config(text="CAMBIO DE EQUIPO", fg=COLORS['accent_red'])
                else:
                    remaining_time += 1
                    return
            
            tiempo_transcurrido_cambio = transcurrido - tiempo_total_exp_preg
            tiempo_util = tiempo_cambio - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6
            tiempo_amarillo = tiempo_util * 0.4
            tiempo_restante_etapa = tiempo_cambio - tiempo_transcurrido_cambio
            
            # Control de luces para cambio
            if tiempo_transcurrido_cambio < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                if tiempo_restante_etapa <= (tiempo_cambio - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_cambio - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                            
            elif tiempo_transcurrido_cambio < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = tiempo_transcurrido_cambio / tiempo_cambio

    # Para Informe de proyectos de investigación (20 minutos: 10 exposición + 7 preguntas + 3 cambio)
    else:
        tiempo_exposicion = 10 * 60  # 10 minutos
        tiempo_preguntas = 7 * 60    # 7 minutos
        tiempo_cambio = 3 * 60       # 3 minutos
        tiempo_total_exp_preg = tiempo_exposicion + tiempo_preguntas
        
        # Etapa de exposición (10 minutos)
        if transcurrido <= tiempo_exposicion:
            if etapa_actual != "exposicion":
                etapa_actual = "exposicion"
                etapa_label.config(text="EXPOSICIÓN", fg=COLORS['accent_green'])
            
            tiempo_restante_etapa = tiempo_exposicion - transcurrido
            tiempo_util = tiempo_exposicion - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6  # 60% del tiempo útil
            tiempo_amarillo = tiempo_util * 0.4  # 40% del tiempo útil
            
            # Control de luces para exposición
            if transcurrido < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (tiempo_exposicion - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_exposicion - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            elif transcurrido < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = transcurrido / tiempo_exposicion

        # Etapa de preguntas (7 minutos)
        elif transcurrido <= tiempo_total_exp_preg:
            if etapa_actual != "preguntas":
                # ALERTA para confirmar inicio de preguntas
                if messagebox.askyesno("Sección de preguntas", "¿Están listos para iniciar la sección de preguntas?"):
                    etapa_actual = "preguntas"
                    etapa_label.config(text="PREGUNTAS", fg=COLORS['accent_yellow'])
                else:
                    remaining_time += 1
                    return
            
            tiempo_transcurrido_preguntas = transcurrido - tiempo_exposicion
            tiempo_util = tiempo_preguntas - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6
            tiempo_amarillo = tiempo_util * 0.4
            tiempo_restante_etapa = tiempo_preguntas - tiempo_transcurrido_preguntas
            
            # Similar lógica para preguntas con los nuevos tiempos
            if tiempo_transcurrido_preguntas < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (tiempo_exposicion - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_exposicion - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            elif tiempo_transcurrido_preguntas < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = tiempo_transcurrido_preguntas / tiempo_preguntas

        # Etapa de cambio (3 minutos)
        else:
            if etapa_actual != "cambio":
                # ALERTA para confirmar inicio de cambio de equipo
                if messagebox.askyesno("Cambio de equipo", "¿Están listos para el cambio de equipo?"):
                    etapa_actual = "cambio"
                    etapa_label.config(text="CAMBIO DE EQUIPO", fg=COLORS['accent_red'])
                else:
                    remaining_time += 1
                    return
            
            tiempo_transcurrido_cambio = transcurrido - tiempo_total_exp_preg
            tiempo_util = tiempo_cambio - TIEMPO_ROJO
            tiempo_verde = tiempo_util * 0.6
            tiempo_amarillo = tiempo_util * 0.4
            tiempo_restante_etapa = tiempo_cambio - tiempo_transcurrido_cambio
            
            # Similar lógica para cambio con los nuevos tiempos
            if tiempo_transcurrido_cambio < tiempo_verde:  # Verde
                for luz in luces_verdes:
                    luz.encender()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_green']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (tiempo_exposicion - tiempo_verde + 10) and \
                   tiempo_restante_etapa > (tiempo_exposicion - tiempo_verde):
                    if not parpadeo_activo or parpadeo_luz_actual != luces_verdes[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_verdes[0]
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_verdes[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            elif tiempo_transcurrido_cambio < (tiempo_verde + tiempo_amarillo):  # Amarillo
                # Apagar verde antes de encender amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo or parpadeo_luz_actual != luces_amarillas[0]:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        parpadeo_luz_actual = luces_amarillas[0]
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                else:
                    if parpadeo_activo and parpadeo_luz_actual == luces_amarillas[0]:
                        parpadeo_activo = False
                        parpadeo_luz_actual = None
                        parpadeo_contador = 0
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
                if parpadeo_activo:
                    parpadeo_activo = False
                    parpadeo_luz_actual = None
                    parpadeo_contador = 0
            
            progreso = tiempo_transcurrido_cambio / tiempo_cambio

    # Actualizar barra de progreso
    ancho_total = barra_canvas.winfo_width()
    nuevo_ancho = progreso * ancho_total
    barra_canvas.coords(barra_rect, 0, 0, nuevo_ancho, 10)
    barra_canvas.itemconfig(barra_rect, fill=barra_color)

def countdown():
    global remaining_time, running
    if remaining_time > 0 and running:
        mins, secs = divmod(remaining_time, 60)
        time_display.config(text=f"{mins:02}:{secs:02}")
        actualizar_semaforo_y_barra(remaining_time)
        remaining_time -= 1
        root.after(1000, countdown)
    else:
        if remaining_time == 0:
            # Sonido más largo y notorio al finalizar el tiempo total
            winsound.Beep(1000, 2000)  # 2 segundos de duración
            messagebox.showinfo("Tiempo terminado", "¡El tiempo ha finalizado!")
            guardar_en_historial(current_team, current_subject)
            if ventana_visual:
                ventana_visual.destroy()
        running = False

def guardar_en_historial(equipo, modalidad):
    archivo = "historial.csv"
    existe = os.path.exists(archivo)

    with open(archivo, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not existe:
            writer.writerow(["ID-Proyecto", "Evento", "Minutos asignados"])
        minutos = 20 if modalidad == "Informe de proyectos de investigación" else 15
        writer.writerow([equipo, modalidad, minutos])

def ver_historial():
    archivo = "historial.csv"
    if not os.path.exists(archivo):
        messagebox.showinfo("Historial vacío", "Aún no se ha registrado ningún proyecto.")
        return

    ventana_historial = Toplevel(root)
    ventana_historial.title("Historial de Exposiciones")
    ventana_historial.geometry("500x300")

    text_area = Text(ventana_historial, font=("Courier", 12))
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = Scrollbar(ventana_historial, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

    with open(archivo, "r", encoding="utf-8") as file:
        contenido = file.read()
        text_area.insert(tk.END, contenido)
        text_area.config(state=tk.DISABLED)

def reset_timer():
    global running, remaining_time
    running = False
    remaining_time = 0
    time_display.config(text="00:00")
    subject_label.config(text="Evento: ")
    team_label.config(text="ID-Proyecto: ")
    team_name_var.set("")
    tema_equipo_var.set("")
    
    # Habilitar nuevamente el menú de selección y la entrada de equipo
    subject_menu.config(state='normal')
    team_entry.config(state='normal')
    tema_entry.config(state='normal')
    
    if ventana_visual:
        ventana_visual.destroy()

# Agregar una función para confirmar el reinicio
def confirmar_reinicio():
    if running:
        if messagebox.askyesno("Confirmar Reinicio", 
                              "¿Estás seguro que deseas reiniciar? \nSe perderá el tiempo actual y se podrá cambiar de modalidad."):
            reset_timer()
    else:
        reset_timer()

# Modificar la creación de los botones en la interfaz principal
def crear_interfaz_principal():
    global start_button, reset_button, historial_button, subject_menu, team_entry, tema_entry

    # Frame superior para evento y equipo
    frame_top = tk.Frame(root, bg=COLORS['bg_primary'], padx=20, pady=10)
    frame_top.pack(pady=10)

    # Cambiar 'Materia' por 'Evento' y actualizar opciones
    tk.Label(frame_top, text="Evento:", font=("Segoe UI", 14), 
            bg=COLORS['bg_primary'], fg=COLORS['text_primary']).grid(row=0, column=0, padx=5, pady=5)
    
    subject_menu = tk.OptionMenu(frame_top, subject_var, "Informe de proyectos de investigación", "Protocolo de proyectos de investigación")
    subject_menu.config(
        font=("Segoe UI", 12),
        width=30,
        bg=COLORS['entry_bg'],
        fg=COLORS['text_primary'],
        activebackground=COLORS['button_hover'],
        activeforeground=COLORS['text_primary'],
        relief='solid',
        bd=1
    )
    subject_menu.grid(row=0, column=1, padx=5)

    # Campo para id-proyecto
    tk.Label(frame_top, text="ID-Proyecto:", font=("Segoe UI", 14), 
            bg=COLORS['bg_primary'], fg=COLORS['text_primary']).grid(row=1, column=0, padx=5, pady=5)
    team_entry = tk.Entry(frame_top, textvariable=team_name_var, 
                         font=("Segoe UI", 12), width=20)
    team_entry.grid(row=1, column=1, padx=5)
    team_entry.configure(
        bg=COLORS['entry_bg'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['text_primary'],
        relief='solid',
        bd=1
    )

    # Campo para título
    tk.Label(frame_top, text="Título:", font=("Segoe UI", 14), 
            bg=COLORS['bg_primary'], fg=COLORS['text_primary']).grid(row=2, column=0, padx=5, pady=5)
    global tema_equipo_var
    tema_equipo_var = tk.StringVar()
    tema_entry = tk.Entry(frame_top, textvariable=tema_equipo_var, 
                         font=("Segoe UI", 12), width=30)
    tema_entry.grid(row=2, column=1, padx=5)
    tema_entry.configure(
        bg=COLORS['entry_bg'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['text_primary'],
        relief='solid',
        bd=1
    )

    # Frame para botones
    button_frame = tk.Frame(root, bg=COLORS['bg_primary'])
    button_frame.pack(pady=10)

    start_button = crear_boton_personalizado(button_frame, "Abrir Semáforo", start_timer)
    start_button.grid(row=0, column=0, padx=10)

    reset_button = crear_boton_personalizado(button_frame, "Reiniciar", confirmar_reinicio)
    reset_button.grid(row=0, column=1, padx=10)

    historial_button = crear_boton_personalizado(root, "Ver Historial", ver_historial)
    historial_button.pack(pady=15)

def disminuir_tiempo(event=None):
    global remaining_time
    if running and remaining_time > 5:
        remaining_time -= 5  # Disminuir 5 segundos
        mins, secs = divmod(remaining_time, 60)
        time_display.config(text=f"{mins:02}:{secs:02}")

def aumentar_tiempo(event=None):
    global remaining_time
    if running:
        remaining_time += 10  # Aumentar 10 segundos
        mins, secs = divmod(remaining_time, 60)
        time_display.config(text=f"{mins:02}:{secs:02}")
        # Actualizar semáforo y barra inmediatamente
        actualizar_semaforo_y_barra(remaining_time)

# Modificar la parte donde se crea la interfaz principal
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cronómetro de Exposición")
    root.geometry("700x500")
    root.configure(bg=COLORS['bg_primary'])

    subject_var = tk.StringVar(value="Informe de proyectos de investigación")
    team_name_var = tk.StringVar()

    crear_interfaz_principal()

    # Info
    subject_label = tk.Label(root, text="Evento: ", 
                           font=("Segoe UI", 16, "bold"), 
                           bg=COLORS['bg_primary'], 
                           fg=COLORS['text_primary'])
    subject_label.pack()
    
    team_label = tk.Label(root, text="ID-Proyecto: ", 
                        font=("Segoe UI", 16, "bold"), 
                        bg=COLORS['bg_primary'], 
                        fg=COLORS['text_primary'])
    team_label.pack()

    time_display = tk.Label(root, text="00:00", 
                          font=("Segoe UI", 72, "bold"), 
                          fg=COLORS['accent_red'], 
                          bg=COLORS['bg_primary'])
    time_display.pack(pady=10)

    # Vincular la tecla "L" para disminuir el tiempo
    root.bind("<l>", disminuir_tiempo)
    # Vincular la tecla "L" mayúscula para aumentar el tiempo
    root.bind("<L>", aumentar_tiempo)

    root.mainloop()