"""
Simulador de reflexión y refracción de la luz (Ley de Snell)
============================================================
Uso:
    pip install matplotlib numpy
    python simulador_luz.py

Controles:
  - ARRASTRA con el mouse la fuente de luz (círculo amarillo) para cambiar el ángulo.
  - Sliders: cambian n1 (medio superior) y n2 (medio inferior).
  - Botones de radio: eligen materiales comunes (aire, agua, vidrio, diamante...).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle
from matplotlib.widgets import Slider, RadioButtons

C = 299_792_458  # velocidad de la luz en el vacío (m/s)

MATERIALES = {
    "Vacío / Aire": 1.00,
    "Agua": 1.33,
    "Vidrio": 1.52,
    "Diamante": 2.42,
}

# ----------------------------------------------------------------- Estado
estado = {"sx": -3.0, "sy": 3.0, "arrastrando": False}
R_MAX = 5.0          # distancia máxima de la fuente al punto de incidencia
LARGO_RAYO = 6.0     # longitud de los rayos reflejado / refractado

# ----------------------------------------------------------------- Figura
fig = plt.figure(figsize=(13, 7.5))
fig.canvas.manager.set_window_title("Simulador de reflexión y refracción de la luz")

ax = fig.add_axes([0.04, 0.30, 0.55, 0.66])
ax.set_xlim(-6, 6)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Arrastra la fuente de luz ☀ para mover el rayo", fontsize=12)

ax_info = fig.add_axes([0.61, 0.30, 0.38, 0.66])
ax_info.axis("off")

# Medios (rectángulos de fondo)
medio1 = Rectangle((-6, 0), 12, 5, color="#4aa3ff", alpha=0.15, zorder=0)
medio2 = Rectangle((-6, -5), 12, 5, color="#4aa3ff", alpha=0.35, zorder=0)
ax.add_patch(medio1)
ax.add_patch(medio2)
ax.axhline(0, color="black", lw=1.5, zorder=1)                       # interfaz
ax.plot([0, 0], [-4.8, 4.8], "k--", lw=1, alpha=0.6, zorder=1)       # normal
ax.text(0.15, 4.5, "Normal", fontsize=9, alpha=0.7)

txt_m1 = ax.text(-5.8, 4.5, "", fontsize=11, weight="bold")
txt_m2 = ax.text(-5.8, -4.7, "", fontsize=11, weight="bold")

# Rayos
(l_inc,) = ax.plot([], [], color="#ffb300", lw=3, zorder=3)
(l_ref,) = ax.plot([], [], color="#e53935", lw=3, zorder=3)
(l_rfr,) = ax.plot([], [], color="#43a047", lw=3, zorder=3)
(fuente,) = ax.plot([], [], "o", ms=18, mfc="#ffeb3b", mec="#f57f17",
                    mew=2, zorder=5)

# Leyenda manual
ax.plot([], [], color="#ffb300", lw=3, label="Incidente")
ax.plot([], [], color="#e53935", lw=3, label="Reflejado")
ax.plot([], [], color="#43a047", lw=3, label="Refractado")
ax.legend(loc="lower right", fontsize=9)

arcos = []
etiquetas_ang = []

# ----------------------------------------------------------------- Controles
ax_s1 = fig.add_axes([0.12, 0.19, 0.40, 0.03])
ax_s2 = fig.add_axes([0.12, 0.12, 0.40, 0.03])
s_n1 = Slider(ax_s1, "n₁ (arriba)", 1.0, 3.0, valinit=1.00, valstep=0.01)
s_n2 = Slider(ax_s2, "n₂ (abajo)", 1.0, 3.0, valinit=1.52, valstep=0.01)

ax_r1 = fig.add_axes([0.62, 0.03, 0.17, 0.20])
ax_r2 = fig.add_axes([0.81, 0.03, 0.17, 0.20])
ax_r1.set_title("Medio 1 (arriba)", fontsize=9)
ax_r2.set_title("Medio 2 (abajo)", fontsize=9)
radio1 = RadioButtons(ax_r1, list(MATERIALES.keys()), active=0)
radio2 = RadioButtons(ax_r2, list(MATERIALES.keys()), active=2)

texto_info = ax_info.text(0.0, 1.0, "", va="top", ha="left",
                          family="monospace", fontsize=9.5)


# ----------------------------------------------------------------- Física
def calcular(n1, n2, theta1):
    """Devuelve un diccionario con todos los resultados físicos."""
    res = {"theta1": theta1}
    sin_t2 = n1 / n2 * np.sin(theta1)
    res["sin_t2"] = sin_t2
    res["tir"] = sin_t2 > 1.0                      # reflexión total interna
    res["theta_c"] = np.arcsin(n2 / n1) if n1 > n2 else None

    c1 = np.cos(theta1)
    if res["tir"]:
        res["theta2"] = None
        res["Rs"] = res["Rp"] = res["R"] = 1.0
        res["T"] = 0.0
    else:
        theta2 = np.arcsin(sin_t2)
        c2 = np.cos(theta2)
        res["theta2"] = theta2
        # Ecuaciones de Fresnel (reflectancia)
        rs = ((n1 * c1 - n2 * c2) / (n1 * c1 + n2 * c2)) ** 2
        rp = ((n1 * c2 - n2 * c1) / (n1 * c2 + n2 * c1)) ** 2
        res["Rs"], res["Rp"] = rs, rp
        res["R"] = 0.5 * (rs + rp)                 # luz no polarizada
        res["T"] = 1.0 - res["R"]
    return res


def deg(x):
    return np.degrees(x)


# ----------------------------------------------------------------- Dibujo
def actualizar(_=None):
    n1, n2 = s_n1.val, s_n2.val
    sx, sy = estado["sx"], estado["sy"]

    theta1 = np.arctan2(abs(sx), sy)               # ángulo con la normal
    lado = np.sign(-sx) if sx != 0 else 1          # lado hacia donde viaja la luz
    r = calcular(n1, n2, theta1)

    # Rayo incidente y fuente
    l_inc.set_data([sx, 0], [sy, 0])
    fuente.set_data([sx], [sy])

    # Rayo reflejado (ángulo de reflexión = ángulo de incidencia)
    rx = lado * np.sin(theta1) * LARGO_RAYO
    ry = np.cos(theta1) * LARGO_RAYO
    l_ref.set_data([0, rx], [0, ry])
    l_ref.set_alpha(max(0.15, r["R"]))
    l_ref.set_linewidth(1 + 3 * r["R"])

    # Rayo refractado
    if r["tir"]:
        l_rfr.set_data([], [])
    else:
        t2 = r["theta2"]
        fx = lado * np.sin(t2) * LARGO_RAYO
        fy = -np.cos(t2) * LARGO_RAYO
        l_rfr.set_data([0, fx], [0, fy])
        l_rfr.set_alpha(max(0.15, r["T"]))
        l_rfr.set_linewidth(1 + 3 * r["T"])

    # Fondos según índice de refracción
    medio1.set_alpha(0.05 + 0.12 * (n1 - 1))
    medio2.set_alpha(0.05 + 0.12 * (n2 - 1))
    txt_m1.set_text(f"Medio 1:  n₁ = {n1:.2f}")
    txt_m2.set_text(f"Medio 2:  n₂ = {n2:.2f}")

    # Arcos de ángulos
    for a in arcos + etiquetas_ang:
        a.remove()
    arcos.clear()
    etiquetas_ang.clear()

    if theta1 > 1e-3:
        t1d = deg(theta1)
        if sx < 0:
            a1 = Arc((0, 0), 2.4, 2.4, theta1=90, theta2=90 + t1d, color="#ffb300", lw=2)
            pos1 = (-1.7 * np.sin(theta1 / 2), 1.7 * np.cos(theta1 / 2))
        else:
            a1 = Arc((0, 0), 2.4, 2.4, theta1=90 - t1d, theta2=90, color="#ffb300", lw=2)
            pos1 = (1.7 * np.sin(theta1 / 2), 1.7 * np.cos(theta1 / 2))
        ax.add_patch(a1)
        arcos.append(a1)
        etiquetas_ang.append(ax.text(*pos1, f"θ₁={t1d:.1f}°", fontsize=9,
                                     ha="center", color="#b27d00"))

        if not r["tir"]:
            t2 = r["theta2"]
            t2d = deg(t2)
            if lado > 0:
                a2 = Arc((0, 0), 2.4, 2.4, theta1=270, theta2=270 + t2d, color="#43a047", lw=2)
                pos2 = (1.7 * np.sin(t2 / 2), -1.7 * np.cos(t2 / 2))
            else:
                a2 = Arc((0, 0), 2.4, 2.4, theta1=270 - t2d, theta2=270, color="#43a047", lw=2)
                pos2 = (-1.7 * np.sin(t2 / 2), -1.7 * np.cos(t2 / 2))
            ax.add_patch(a2)
            arcos.append(a2)
            etiquetas_ang.append(ax.text(*pos2, f"θ₂={t2d:.1f}°", fontsize=9,
                                         ha="center", color="#2e7d32"))

    # ---------------- Panel de cálculos
    v1, v2 = C / n1, C / n2
    L = []
    L.append("═══ CÁLCULOS ═══")
    L.append("")
    L.append("Velocidad de la luz en cada medio (v = c/n):")
    L.append(f"  v₁ = c/{n1:.2f} = {v1:.3e} m/s")
    L.append(f"  v₂ = c/{n2:.2f} = {v2:.3e} m/s")
    L.append("")
    L.append("REFLEXIÓN  (θr = θ₁):")
    L.append(f"  θr = {deg(theta1):.2f}°")
    L.append("")
    L.append("REFRACCIÓN  (Ley de Snell: n₁·sen θ₁ = n₂·sen θ₂):")
    L.append(f"  n₁·sen θ₁ = {n1:.2f} · sen({deg(theta1):.2f}°)")
    L.append(f"            = {n1 * np.sin(theta1):.4f}")
    L.append(f"  sen θ₂ = {n1 * np.sin(theta1):.4f} / {n2:.2f}")
    L.append(f"         = {r['sin_t2']:.4f}")
    if r["tir"]:
        L.append("  sen θ₂ > 1  →  ¡NO hay rayo refractado!")
        L.append("  >>> REFLEXIÓN TOTAL INTERNA <<<")
    else:
        L.append(f"  θ₂ = arcsen({r['sin_t2']:.4f}) = {deg(r['theta2']):.2f}°")
        L.append("  El rayo se " + ("ACERCA a la normal (n₂ > n₁)" if n2 > n1
                                     else "ALEJA de la normal (n₂ < n₁)" if n2 < n1
                                     else "propaga sin desviarse (n₁ = n₂)"))
    L.append("")
    L.append("ÁNGULO CRÍTICO  (θc = arcsen(n₂/n₁), si n₁ > n₂):")
    if r["theta_c"] is not None:
        L.append(f"  θc = arcsen({n2:.2f}/{n1:.2f}) = {deg(r['theta_c']):.2f}°")
        L.append("  " + ("θ₁ ≥ θc → reflexión total" if r["tir"] else "θ₁ < θc → hay refracción"))
    else:
        L.append("  No existe (n₁ ≤ n₂)")
    L.append("")
    L.append("ECUACIONES DE FRESNEL (luz no polarizada):")
    L.append(f"  Rs = {r['Rs'] * 100:6.2f} %   Rp = {r['Rp'] * 100:6.2f} %")
    L.append(f"  Reflejada   R = {r['R'] * 100:6.2f} %")
    L.append(f"  Transmitida T = {r['T'] * 100:6.2f} %")
    if n1 != n2 and not r["tir"]:
        theta_b = np.arctan(n2 / n1)
        L.append(f"  Áng. de Brewster = arctan(n₂/n₁) = {deg(theta_b):.2f}°")

    texto_info.set_text("\n".join(L))
    fig.canvas.draw_idle()


# ----------------------------------------------------------------- Eventos
def on_press(event):
    if event.inaxes is not ax or event.xdata is None:
        return
    if np.hypot(event.xdata - estado["sx"], event.ydata - estado["sy"]) < 0.7:
        estado["arrastrando"] = True


def on_release(_):
    estado["arrastrando"] = False


def on_move(event):
    if not estado["arrastrando"] or event.inaxes is not ax or event.xdata is None:
        return
    x, y = event.xdata, max(event.ydata, 0.3)       # la fuente siempre arriba
    d = np.hypot(x, y)
    if d > R_MAX:                                   # limitar distancia
        x, y = x * R_MAX / d, y * R_MAX / d
    estado["sx"], estado["sy"] = x, y
    actualizar()


def elegir_m1(label):
    s_n1.set_val(MATERIALES[label])


def elegir_m2(label):
    s_n2.set_val(MATERIALES[label])


fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("motion_notify_event", on_move)
s_n1.on_changed(actualizar)
s_n2.on_changed(actualizar)
radio1.on_clicked(elegir_m1)
radio2.on_clicked(elegir_m2)

actualizar()
plt.show()