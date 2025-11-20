import tkinter as tk
from tkinter import ttk, colorchooser
import math




def rgb_to_cmyk(r, g, b):
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 1
    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255
    k = min(c, m, y)
    c = (c - k) / (1 - k)
    m = (m - k) / (1 - k)
    y = (y - k) / (1 - k)
    return c, m, y, k


def cmyk_to_rgb(c, m, y, k):
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return int(round(r)), int(round(g)), int(round(b))


# sRGB D65 формулы RGB ↔ LAB через XYZ

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return int(round(max(0, min(1, v)) * 255))


M_RGB_to_XYZ = [
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
]
M_XYZ_to_RGB = [
    [3.2404542, -1.5371385, -0.4985314],
    [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252],
]
Xn, Yn, Zn = 0.95047, 1.00000, 1.08883


def rgb_to_xyz(r, g, b):
    lr, lg, lb = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    X = M_RGB_to_XYZ[0][0] * lr + M_RGB_to_XYZ[0][1] * lg + M_RGB_to_XYZ[0][2] * lb
    Y = M_RGB_to_XYZ[1][0] * lr + M_RGB_to_XYZ[1][1] * lg + M_RGB_to_XYZ[1][2] * lb
    Z = M_RGB_to_XYZ[2][0] * lr + M_RGB_to_XYZ[2][1] * lg + M_RGB_to_XYZ[2][2] * lb
    return X, Y, Z


def xyz_to_rgb(X, Y, Z):
    lr = M_XYZ_to_RGB[0][0] * X + M_XYZ_to_RGB[0][1] * Y + M_XYZ_to_RGB[0][2] * Z
    lg = M_XYZ_to_RGB[1][0] * X + M_XYZ_to_RGB[1][1] * Y + M_XYZ_to_RGB[1][2] * Z
    lb = M_XYZ_to_RGB[2][0] * X + M_XYZ_to_RGB[2][1] * Y + M_XYZ_to_RGB[2][2] * Z
    return linear_to_srgb(lr), linear_to_srgb(lg), linear_to_srgb(lb)


def f_lab(t):
    d = 6 / 29
    return t ** (1 / 3) if t > d ** 3 else t / (3 * d ** 2) + 4 / 29


def f_lab_inv(ft):
    d = 6 / 29
    return ft ** 3 if ft > d else 3 * d ** 2 * (ft - 4 / 29)


def xyz_to_lab(X, Y, Z):
    fx, fy, fz = f_lab(X / Xn), f_lab(Y / Yn), f_lab(Z / Zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b


def lab_to_xyz(L, a, b):
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    X = Xn * f_lab_inv(fx)
    Y = Yn * f_lab_inv(fy)
    Z = Zn * f_lab_inv(fz)
    return X, Y, Z


# --- GUI ---
class ColorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Лабораторная: CMYK ↔ LAB ↔ RGB (вариант 10)')
        self.resizable(False, False)

        self.rgb = {c: tk.IntVar(value=128) for c in 'RGB'}
        self.cmyk = {c: tk.DoubleVar(value=0.0) for c in 'CMYK'}
        self.lab = {'L': tk.DoubleVar(value=50.0), 'a': tk.DoubleVar(value=0.0), 'b': tk.DoubleVar(value=0.0)}

        # Флаг для предотвращения рекурсивных обновлений
        self.updating = False

        self.build_ui()
        self.update_from_rgb()

    def build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.grid(row=0, column=0)

        # RGB Frame
        rgb_f = ttk.LabelFrame(main, text='RGB (0–255)')
        rgb_f.grid(row=0, column=0, padx=5, sticky='nsew')
        self.rgb_entries = {}
        self.rgb_scales = {}
        for i, c in enumerate('RGB'):
            ttk.Label(rgb_f, text=c).grid(row=i, column=0, padx=2, pady=2)

            scale = ttk.Scale(rgb_f, from_=0, to=255, variable=self.rgb[c])
            scale.grid(row=i, column=1, padx=2, pady=2, sticky='ew')
            scale.bind('<ButtonPress-1>', lambda e, cc=c: self.on_rgb_scale_press(cc))
            scale.bind('<ButtonRelease-1>', lambda e, cc=c: self.on_rgb_scale_release(cc))
            self.rgb_scales[c] = scale

            entry = ttk.Entry(rgb_f, width=6, textvariable=self.rgb[c])
            entry.grid(row=i, column=2, padx=2, pady=2)
            entry.bind('<Return>', lambda e, cc=c: self.on_rgb_entry_change(cc))
            self.rgb_entries[c] = entry

        # LAB Frame
        lab_f = ttk.LabelFrame(main, text='LAB (L 0–100, a/b -128..127)')
        lab_f.grid(row=0, column=1, padx=5, sticky='nsew')
        ranges = {'L': (0, 100), 'a': (-128, 127), 'b': (-128, 127)}
        self.lab_entries = {}
        self.lab_scales = {}
        for i, c in enumerate('Lab'):
            lo, hi = ranges[c]
            ttk.Label(lab_f, text=c).grid(row=i, column=0, padx=2, pady=2)

            scale = ttk.Scale(lab_f, from_=lo, to=hi, variable=self.lab[c])
            scale.grid(row=i, column=1, padx=2, pady=2, sticky='ew')
            scale.bind('<ButtonPress-1>', lambda e, cc=c: self.on_lab_scale_press(cc))
            scale.bind('<ButtonRelease-1>', lambda e, cc=c: self.on_lab_scale_release(cc))
            self.lab_scales[c] = scale

            entry = ttk.Entry(lab_f, width=7, textvariable=self.lab[c])
            entry.grid(row=i, column=2, padx=2, pady=2)
            entry.bind('<Return>', lambda e, cc=c: self.on_lab_entry_change(cc))
            self.lab_entries[c] = entry

        # CMYK Frame
        cmyk_f = ttk.LabelFrame(main, text='CMYK (0–1)')
        cmyk_f.grid(row=0, column=2, padx=5, sticky='nsew')
        self.cmyk_entries = {}
        self.cmyk_scales = {}
        for i, c in enumerate('CMYK'):
            ttk.Label(cmyk_f, text=c).grid(row=i, column=0, padx=2, pady=2)

            scale = ttk.Scale(cmyk_f, from_=0.0, to=1.0, variable=self.cmyk[c])
            scale.grid(row=i, column=1, padx=2, pady=2, sticky='ew')
            scale.bind('<ButtonPress-1>', lambda e, cc=c: self.on_cmyk_scale_press(cc))
            scale.bind('<ButtonRelease-1>', lambda e, cc=c: self.on_cmyk_scale_release(cc))
            self.cmyk_scales[c] = scale

            entry = ttk.Entry(cmyk_f, width=7, textvariable=self.cmyk[c])
            entry.grid(row=i, column=2, padx=2, pady=2)
            entry.bind('<Return>', lambda e, cc=c: self.on_cmyk_entry_change(cc))
            self.cmyk_entries[c] = entry

        # Bottom controls
        bottom = ttk.Frame(main)
        bottom.grid(row=1, column=0, columnspan=3, pady=6, sticky='ew')

        self.swatch = ttk.Label(bottom, text='   ', width=24, relief='sunken', background='#808080')
        self.swatch.grid(row=0, column=0, padx=6, pady=2)

        ttk.Button(bottom, text='Выбрать цвет', command=self.pick_color).grid(row=0, column=1, padx=6, pady=2)

        self.warn = ttk.Label(bottom, text='', foreground='orange')
        self.warn.grid(row=0, column=2, padx=6, pady=2)

    # RGB handlers
    def on_rgb_scale_press(self, c):
        self.rgb_scales[c].bind('<Motion>', lambda e, cc=c: self.on_rgb_scale_drag(cc))

    def on_rgb_scale_release(self, c):
        self.rgb_scales[c].unbind('<Motion>')
        self.update_from_rgb()

    def on_rgb_scale_drag(self, c):
        if not self.updating:
            self.update_from_rgb()

    def on_rgb_entry_change(self, c):
        if not self.updating:
            try:
                value = int(self.rgb[c].get())
                value = max(0, min(255, value))
                self.rgb[c].set(value)
                self.update_from_rgb()
            except ValueError:
                pass

    # LAB handlers
    def on_lab_scale_press(self, c):
        self.lab_scales[c].bind('<Motion>', lambda e, cc=c: self.on_lab_scale_drag(cc))

    def on_lab_scale_release(self, c):
        self.lab_scales[c].unbind('<Motion>')
        self.update_from_lab()

    def on_lab_scale_drag(self, c):
        if not self.updating:
            self.update_from_lab()

    def on_lab_entry_change(self, c):
        if not self.updating:
            try:
                value = float(self.lab[c].get())
                ranges = {'L': (0, 100), 'a': (-128, 127), 'b': (-128, 127)}
                lo, hi = ranges[c]
                value = max(lo, min(hi, value))
                self.lab[c].set(value)
                self.update_from_lab()
            except ValueError:
                pass

    # CMYK handlers
    def on_cmyk_scale_press(self, c):
        self.cmyk_scales[c].bind('<Motion>', lambda e, cc=c: self.on_cmyk_scale_drag(cc))

    def on_cmyk_scale_release(self, c):
        self.cmyk_scales[c].unbind('<Motion>')
        self.update_from_cmyk()

    def on_cmyk_scale_drag(self, c):
        if not self.updating:
            self.update_from_cmyk()

    def on_cmyk_entry_change(self, c):
        if not self.updating:
            try:
                value = float(self.cmyk[c].get())
                value = max(0.0, min(1.0, value))
                self.cmyk[c].set(value)
                self.update_from_cmyk()
            except ValueError:
                pass

    def update_from_rgb(self):
        if self.updating:
            return

        self.updating = True
        r, g, b = [self.rgb[x].get() for x in 'RGB']

        # RGB → LAB
        X, Y, Z = rgb_to_xyz(r, g, b)
        L, a, bb = xyz_to_lab(X, Y, Z)
        self.lab['L'].set(round(L, 3))
        self.lab['a'].set(round(a, 3))
        self.lab['b'].set(round(bb, 3))

        # RGB → CMYK
        c, m, y, k = rgb_to_cmyk(r, g, b)
        self.cmyk['C'].set(round(c, 3))
        self.cmyk['M'].set(round(m, 3))
        self.cmyk['Y'].set(round(y, 3))
        self.cmyk['K'].set(round(k, 3))

        self.set_swatch(r, g, b)
        self.warn.config(text='')
        self.updating = False

    def update_from_lab(self):
        if self.updating:
            return

        self.updating = True
        L = float(self.lab['L'].get())
        a = float(self.lab['a'].get())
        b = float(self.lab['b'].get())

        X, Y, Z = lab_to_xyz(L, a, b)
        r, g, bb = xyz_to_rgb(X, Y, Z)

        clipped = not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= bb <= 255)
        r, g, bb = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, bb))

        self.rgb['R'].set(r)
        self.rgb['G'].set(g)
        self.rgb['B'].set(bb)


        c, m, y, k = rgb_to_cmyk(r, g, bb)
        self.cmyk['C'].set(round(c, 3))
        self.cmyk['M'].set(round(m, 3))
        self.cmyk['Y'].set(round(y, 3))
        self.cmyk['K'].set(round(k, 3))

        self.set_swatch(r, g, bb)
        self.warn.config(text='RGB усечён!' if clipped else '')
        self.updating = False

    def update_from_cmyk(self):
        if self.updating:
            return

        self.updating = True
        c, m, y, k = [float(self.cmyk[x].get()) for x in 'CMYK']

        r, g, b = cmyk_to_rgb(c, m, y, k)
        self.rgb['R'].set(r)
        self.rgb['G'].set(g)
        self.rgb['B'].set(b)


        X, Y, Z = rgb_to_xyz(r, g, b)
        L, a, bb = xyz_to_lab(X, Y, Z)
        self.lab['L'].set(round(L, 3))
        self.lab['a'].set(round(a, 3))
        self.lab['b'].set(round(bb, 3))

        self.set_swatch(r, g, b)
        self.warn.config(text='')
        self.updating = False

    def pick_color(self):
        if self.updating:
            return


        current_rgb = f'#{self.rgb["R"].get():02x}{self.rgb["G"].get():02x}{self.rgb["B"].get():02x}'

        col = colorchooser.askcolor(color=current_rgb, title='Выберите цвет')
        if col and col[0]:
            self.updating = True
            r, g, b = [int(round(x)) for x in col[0]]
            self.rgb['R'].set(r)
            self.rgb['G'].set(g)
            self.rgb['B'].set(b)

            # Обновляем все значения из RGB
            X, Y, Z = rgb_to_xyz(r, g, b)
            L, a, bb = xyz_to_lab(X, Y, Z)
            self.lab['L'].set(round(L, 3))
            self.lab['a'].set(round(a, 3))
            self.lab['b'].set(round(bb, 3))

            c, m, y, k = rgb_to_cmyk(r, g, b)
            self.cmyk['C'].set(round(c, 3))
            self.cmyk['M'].set(round(m, 3))
            self.cmyk['Y'].set(round(y, 3))
            self.cmyk['K'].set(round(k, 3))

            self.set_swatch(r, g, b)
            self.warn.config(text='')
            self.updating = False

    def set_swatch(self, r, g, b):
        color_hex = f'#{int(r):02x}{int(g):02x}{int(b):02x}'
        self.swatch.config(background=color_hex)


if __name__ == '__main__':
    app = ColorApp()
    app.mainloop()