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

# Al inicio del archivo, después de los imports
COLORS = {
    'bg_primary': '#1E272E',      # Gris muy oscuro para el fondo principal
    'bg_secondary': '#2C3A47',    # Gris oscuro para elementos secundarios
    'text_primary': '#FFFFFF',    # Blanco puro para mejor contraste
    'accent_green': '#2ECC71',    # Verde brillante
    'accent_yellow': '#F1C40F',   # Amarillo brillante
    'accent_red': '#E74C3C',      # Rojo brillante
    'button_bg': '#34495E',       # Cambiar el color de fondo del botón a más oscuro
    'button_hover': '#2C3E50',    # Color hover más oscuro
    'entry_bg': '#34495E',        # Fondo para campos de entrada
    'button_text': '#FFFFFF',     # Texto blanco para botones
    'border_color': '#5D6D7E'     # Color para bordes
}

# --- Funciones principales ---
def start_timer():
    global running, remaining_time, current_team, current_subject, total_duration, etapa_actual
    if running:
        return

    subject = subject_var.get()
    team_name = team_name_var.get().strip()

    if not team_name:
        messagebox.showwarning("Advertencia", "Por favor, ingresa el nombre del equipo.")
        return

    if subject == "Taller Inv 2":
        total_seconds = 20 * 60  # 20 minutos
    elif subject == "Taller Inv 1":
        total_seconds = 15 * 60  # 15 minutos
    else:
        messagebox.showwarning("Advertencia", "Selecciona una materia válida.")
        return

    # Deshabilitar el menú de selección y la entrada de equipo
    subject_menu.config(state='disabled')
    team_entry.config(state='disabled')

    total_duration = total_seconds
    subject_label.config(text=f"Materia: {subject}")
    team_label.config(text=f"Equipo: {team_name}")
    remaining_time = total_seconds
    current_team = team_name
    current_subject = subject
    etapa_actual = "exposicion"
    
    abrir_ventana_visual()
    running = True
    countdown()

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
        font=('Helvetica', 14, 'bold'),
        bg=COLORS['button_bg'],
        fg=COLORS['text_primary'],
        activebackground=COLORS['button_hover'],
        activeforeground=COLORS['text_primary'],
        relief='solid',
        bd=1,
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
    global ventana_visual, semaforo_canvas, barra_canvas, luz_verde, luz_amarilla, luz_roja, barra_rect, etapa_label
    ventana_visual = Toplevel(root)
    ventana_visual.title("Visualizador de Tiempo")
    ventana_visual.attributes('-fullscreen', True)
    ventana_visual.configure(bg=COLORS['bg_primary'])

    # Frame superior con gradiente
    frame_superior = tk.Frame(ventana_visual, bg=COLORS['bg_primary'])
    frame_superior.pack(fill=tk.BOTH, expand=True)

    # Mostrar el equipo y materia en la ventana visual
    equipo_label = tk.Label(frame_superior, 
                           text=f"Equipo: {current_team}",
                           font=("Helvetica", 24, "bold"),
                           bg=COLORS['bg_primary'],
                           fg=COLORS['text_primary'])
    equipo_label.pack(pady=10)

    # Nueva etiqueta para mostrar la etapa actual
    etapa_label = tk.Label(frame_superior,
                          text="EXPOSICIÓN",
                          font=("Helvetica", 36, "bold"),
                          bg=COLORS['bg_primary'],
                          fg=COLORS['accent_green'])
    etapa_label.pack(pady=10)

    semaforo_canvas = tk.Canvas(frame_superior, 
                              bg=COLORS['bg_primary'], 
                              highlightthickness=0)
    semaforo_canvas.pack(fill=tk.BOTH, expand=True)

    # Barra de progreso moderna
    barra_canvas = tk.Canvas(ventana_visual, 
                           height=10,  # Más delgada
                           bg=COLORS['bg_secondary'],
                           highlightthickness=0)
    barra_canvas.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
    barra_rect = barra_canvas.create_rectangle(0, 0, 0, 10, 
                                             fill=COLORS['accent_green'],
                                             width=0)  # Sin borde

    try:
        logo_image = PhotoImage(file="logo.png")
    except Exception:
        logo_image = None

    def dibujar_semaforo(event=None):
        global luces_verdes, luces_amarillas, luces_rojas
        semaforo_canvas.delete("all")
        w = semaforo_canvas.winfo_width()
        h = semaforo_canvas.winfo_height()
        radio = int(min(w, h) * 0.08)
        offset_y = int(h * 0.15)
        espacio = int(radio * 2.2)

        # Calcular posiciones para tres semáforos
        separacion_semaforos = radio * 6
        posiciones_x = [
            w // 2 - separacion_semaforos,
            w // 2,
            w // 2 + separacion_semaforos
        ]
        
        # Limpiar las listas antes de crear nuevas luces
        luces_verdes = []
        luces_amarillas = []
        luces_rojas = []
        
        # Dibujar los tres semáforos
        for cx in posiciones_x:
            # Carcasa del semáforo
            carcasa_width = radio * 3
            carcasa_height = espacio * 3 + radio * 2
            
            # Agregar soporte metálico
            soporte_width = radio * 0.5
            semaforo_canvas.create_rectangle(
                cx - soporte_width//2,
                offset_y - radio - 20,
                cx + soporte_width//2,
                offset_y - radio,
                fill='#95a5a6',
                width=1,
                outline='#7f8c8d'
            )
            
            # Carcasa principal
            semaforo_canvas.create_rectangle(
                cx - carcasa_width//2,
                offset_y - radio,
                cx + carcasa_width//2,
                offset_y + carcasa_height,
                fill=COLORS['bg_secondary'],
                width=2,
                outline=COLORS['text_primary']
            )
            
            # Agregar detalles metálicos
            for i in range(3):
                y_pos = offset_y + i * espacio + radio
                semaforo_canvas.create_line(
                    cx - carcasa_width//2,
                    y_pos - radio - 5,
                    cx + carcasa_width//2,
                    y_pos - radio - 5,
                    fill='#95a5a6',
                    width=1
                )
            
            # Crear luces para cada semáforo
            luz_verde = LuzSemaforo(
                semaforo_canvas,
                cx,
                offset_y + radio,
                radio,
                "#333333",
                COLORS['accent_green']
            )
            luces_verdes.append(luz_verde)
            
            luz_amarilla = LuzSemaforo(
                semaforo_canvas,
                cx,
                offset_y + espacio + radio,
                radio,
                "#333333",
                COLORS['accent_yellow']
            )
            luces_amarillas.append(luz_amarilla)
            
            luz_roja = LuzSemaforo(
                semaforo_canvas,
                cx,
                offset_y + 2*espacio + radio,
                radio,
                "#333333",
                COLORS['accent_red']
            )
            luces_rojas.append(luz_roja)

    ventana_visual.bind("<Configure>", dibujar_semaforo)
    dibujar_semaforo()
    ventana_visual.bind("<Escape>", lambda e: ventana_visual.destroy())

def parpadear_luz(luz, color_original):
    global parpadeo_contador
    if parpadeo_contador < 20:  # 10 segundos (20 cambios de 0.5s)
        if parpadeo_contador % 2 == 0:
            luz.canvas.itemconfig(luz.luz_id, fill="#333333")  # Apagar
        else:
            luz.canvas.itemconfig(luz.luz_id, fill=color_original)  # Encender
        parpadeo_contador += 1
        ventana_visual.after(500, lambda: parpadear_luz(luz, color_original))

def actualizar_semaforo_y_barra(tiempo_restante):
    global parpadeo_activo, parpadeo_contador, etapa_actual, luces_verdes, luces_amarillas, luces_rojas
    if not ventana_visual or not luces_verdes:
        return

    transcurrido = total_duration - tiempo_restante
    barra_color = COLORS['accent_green']
    TIEMPO_ROJO = 20  # 20 segundos para el rojo en cada etapa

    # Para Taller Inv 1 (15 minutos: 5 exposición + 5 preguntas + 5 cambio)
    if current_subject == "Taller Inv 1":
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                
            elif transcurrido < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = transcurrido / tiempo_exposicion

        # Etapa de preguntas (5 minutos)
        elif transcurrido <= tiempo_total_exp_preg:
            if etapa_actual != "preguntas":
                etapa_actual = "preguntas"
                etapa_label.config(text="PREGUNTAS", fg=COLORS['accent_yellow'])
            
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                            
            elif tiempo_transcurrido_preguntas < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                            
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = tiempo_transcurrido_preguntas / tiempo_preguntas

        # Etapa de cambio (5 minutos)
        else:
            if etapa_actual != "cambio":
                etapa_actual = "cambio"
                etapa_label.config(text="CAMBIO DE EQUIPO", fg=COLORS['accent_red'])
            
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                            
            elif tiempo_transcurrido_cambio < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = tiempo_transcurrido_cambio / tiempo_cambio

    # Para Taller Inv 2 (20 minutos: 10 exposición + 7 preguntas + 3 cambio)
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                
            elif transcurrido < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = transcurrido / tiempo_exposicion

        # Etapa de preguntas (7 minutos)
        elif transcurrido <= tiempo_total_exp_preg:
            if etapa_actual != "preguntas":
                etapa_actual = "preguntas"
                etapa_label.config(text="PREGUNTAS", fg=COLORS['accent_yellow'])
            
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                
            elif tiempo_transcurrido_preguntas < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = tiempo_transcurrido_preguntas / tiempo_preguntas

        # Etapa de cambio (3 minutos)
        else:
            if etapa_actual != "cambio":
                etapa_actual = "cambio"
                etapa_label.config(text="CAMBIO DE EQUIPO", fg=COLORS['accent_red'])
            
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
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_verdes:
                            parpadear_luz(luz, COLORS['accent_green'])
                
            elif tiempo_transcurrido_cambio < (tiempo_verde + tiempo_amarillo):  # Amarillo
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.encender()
                for luz in luces_rojas:
                    luz.apagar()
                barra_color = COLORS['accent_yellow']
                
                # Parpadeo 10 segundos antes
                if tiempo_restante_etapa <= (TIEMPO_ROJO + 10) and tiempo_restante_etapa > TIEMPO_ROJO:
                    if not parpadeo_activo:
                        parpadeo_activo = True
                        parpadeo_contador = 0
                        for luz in luces_amarillas:
                            parpadear_luz(luz, COLORS['accent_yellow'])
                
            else:  # Rojo (últimos 20 segundos)
                for luz in luces_verdes:
                    luz.apagar()
                for luz in luces_amarillas:
                    luz.apagar()
                for luz in luces_rojas:
                    luz.encender()
                barra_color = COLORS['accent_red']
            
            progreso = tiempo_transcurrido_cambio / tiempo_cambio

    # Actualizar barra de progreso
    ancho_total = barra_canvas.winfo_width()
    nuevo_ancho = progreso * ancho_total
    barra_canvas.coords(barra_rect, 0, 0, nuevo_ancho, 10)
    barra_canvas.itemconfig(barra_rect, fill=barra_color)

    # Resetear parpadeo cuando termine
    if parpadeo_contador >= 20:
        parpadeo_activo = False
        parpadeo_contador = 0

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
            writer.writerow(["Equipo", "Modalidad", "Minutos asignados"])
        minutos = 20 if modalidad == "Taller Inv 2" else 15
        writer.writerow([equipo, modalidad, minutos])

def ver_historial():
    archivo = "historial.csv"
    if not os.path.exists(archivo):
        messagebox.showinfo("Historial vacío", "Aún no se ha registrado ningún equipo.")
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
    subject_label.config(text="Materia: ")
    team_label.config(text="Equipo: ")
    team_name_var.set("")
    
    # Habilitar nuevamente el menú de selección y la entrada de equipo
    subject_menu.config(state='normal')
    team_entry.config(state='normal')
    
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
    global start_button, reset_button, historial_button, subject_menu, team_entry

    # Frame superior para materia y equipo
    frame_top = tk.Frame(root, bg=COLORS['bg_primary'])
    frame_top.pack(pady=10)

# Materia y equipo
    tk.Label(frame_top, text="Materia:", font=("Helvetica", 14), 
            bg=COLORS['bg_primary'], fg=COLORS['text_primary']).grid(row=0, column=0, padx=5, pady=5)
    
    subject_menu = tk.OptionMenu(frame_top, subject_var, "Taller Inv 2", "Taller Inv 1")
    subject_menu.config(
        font=("Helvetica", 12),
        width=15,
        bg=COLORS['entry_bg'],
        fg=COLORS['text_primary'],
        activebackground=COLORS['button_hover'],
        activeforeground=COLORS['text_primary'],
        relief='solid',
        bd=1
    )
    subject_menu.grid(row=0, column=1, padx=5)

    tk.Label(frame_top, text="Equipo:", font=("Helvetica", 14), 
            bg=COLORS['bg_primary'], fg=COLORS['text_primary']).grid(row=1, column=0, padx=5, pady=5)
    
    team_entry = tk.Entry(frame_top, textvariable=team_name_var, 
                         font=("Helvetica", 12), width=20)
    team_entry.grid(row=1, column=1, padx=5)
    team_entry.configure(
        bg=COLORS['entry_bg'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['text_primary'],
        relief='solid',
        bd=1
    )

    # Frame para botones
    button_frame = tk.Frame(root, bg=COLORS['bg_primary'])
    button_frame.pack(pady=10)

    start_button = crear_boton_personalizado(button_frame, "Iniciar", start_timer)
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
        remaining_time += 5  # Aumentar 5 segundos
        mins, secs = divmod(remaining_time, 60)
        time_display.config(text=f"{mins:02}:{secs:02}")

# Modificar la parte donde se crea la interfaz principal
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cronómetro de Exposición")
    root.geometry("700x500")
    root.configure(bg=COLORS['bg_primary'])

    subject_var = tk.StringVar(value="Taller Inv 2")
    team_name_var = tk.StringVar()

    crear_interfaz_principal()

# Info
    subject_label = tk.Label(root, text="Materia: ", 
                           font=("Helvetica", 16, "bold"), 
                           bg=COLORS['bg_primary'], 
                           fg=COLORS['text_primary'])
    subject_label.pack()
    
    team_label = tk.Label(root, text="Equipo: ", 
                        font=("Helvetica", 16, "bold"), 
                        bg=COLORS['bg_primary'], 
                        fg=COLORS['text_primary'])
    team_label.pack()

    time_display = tk.Label(root, text="00:00", 
                          font=("Helvetica", 72, "bold"), 
                          fg=COLORS['accent_red'], 
                          bg=COLORS['bg_primary'])
    time_display.pack(pady=10)

    # Vincular la tecla "L" para disminuir el tiempo
    root.bind("<l>", disminuir_tiempo)
    # Vincular la tecla "L" mayúscula para aumentar el tiempo
    root.bind("<L>", aumentar_tiempo)

    root.mainloop()