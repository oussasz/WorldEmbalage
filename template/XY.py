import fitz  # PyMuPDF
from tkinter import Tk, Canvas, Frame, BOTH, Scrollbar, HORIZONTAL, VERTICAL
import PIL.Image as PILImage
from PIL import ImageTk
from pathlib import Path

# افتح PDF وحول الصفحة الأولى إلى صورة مع احترام الحجم وإضافة تكبير/تصغير
pdf_path = Path(__file__).parent / "facture_FACT-20250923-121159_20250923.pdf"
doc = fitz.open(str(pdf_path))
page = doc[0]
page_rect = page.rect  # الأبعاد الأصلية للـ PDF (بوحدة النقاط)

# إعداد نافذة Tkinter
root = Tk()
root.title("PDF Coordinate Picker — MP.pdf")

# احصل على حجم الشاشة لاختيار مقياس مناسب لعرض الصفحة كاملة
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

# أضف هامش بسيط داخل النافذة
margin_w = 80
margin_h = 160

# احسب مقياس البداية (fit-to-screen)
fit_scale_x = (screen_w - margin_w) / page_rect.width
fit_scale_y = (screen_h - margin_h) / page_rect.height
scale = max(0.25, min(fit_scale_x, fit_scale_y))  # لا تقل عن 25%

def render_pixmap(current_scale: float) -> PILImage.Image:
    """ارسم الصفحة بحسب المقياس وأعدها كصورة PIL."""
    matrix = fitz.Matrix(current_scale, current_scale)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    # تأكد من أن الصورة بصيغة RGB متوافقة مع Pillow
    try:
        if pix.colorspace is None or (hasattr(pix.colorspace, "n") and pix.colorspace.n != 3) or pix.alpha:
            pix = fitz.Pixmap(fitz.csRGB, pix)
    except Exception:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)

# إطار يحتوي على Canvas + Scrollbars
frame = Frame(root)
frame.pack(fill=BOTH, expand=True)

vbar = Scrollbar(frame, orient=VERTICAL)
hbar = Scrollbar(frame, orient=HORIZONTAL)
canvas = Canvas(frame, highlightthickness=0, xscrollcommand=hbar.set, yscrollcommand=vbar.set)
hbar.config(command=canvas.xview)
vbar.config(command=canvas.yview)

hbar.pack(side="bottom", fill="x")
vbar.pack(side="right", fill="y")
canvas.pack(side="left", fill=BOTH, expand=True)

# أول رسم
img = render_pixmap(scale)
tk_img = ImageTk.PhotoImage(img)
image_id = canvas.create_image(0, 0, anchor="nw", image=tk_img)
canvas.config(scrollregion=(0, 0, img.width, img.height))
canvas.configure(width=min(img.width, screen_w - margin_w // 2), height=min(img.height, screen_h - margin_h // 2))

def redraw():
    """أعد رسم الصورة بعد تغيير المقياس."""
    global img, tk_img
    img = render_pixmap(scale)
    tk_img = ImageTk.PhotoImage(img)
    canvas.itemconfigure(image_id, image=tk_img)
    canvas.config(scrollregion=(0, 0, img.width, img.height))

# دالة لاستخراج الإحداثيات عند النقر (تعرض إحداثيات Tk/Canvas وإحداثيات PDF)
def click_event(event):
    # استخدم canvasx/canvasy لأخذ التمرير بعين الاعتبار
    x_can = canvas.canvasx(event.x)
    y_can = canvas.canvasy(event.y)
    # إحداثيات PDF (الأصل أسفل-يسار)
    pdf_x = x_can / scale
    pdf_y = (img.height - y_can) / scale
    print(f"Canvas -> X: {x_can:.2f}, Y: {y_can:.2f} | PDF -> X: {pdf_x:.2f}, Y: {pdf_y:.2f} | Scale: {scale:.2f}x")

canvas.bind("<Button-1>", click_event)

# اختصارات للتكبير/التصغير وإعادة الضبط (Ctrl + MouseWheel أو +/-)
def zoom(delta: float):
    global scale
    old_scale = scale
    # غيّر المقياس بنسبة 10%
    scale = max(0.1, min(6.0, scale * (1.0 + delta)))
    if abs(scale - old_scale) > 1e-6:
        redraw()

def on_key(event):
    if event.keysym in ("plus", "equal"):
        zoom(0.10)
    elif event.keysym in ("minus", "underscore"):
        zoom(-0.10)
    elif event.keysym.lower() == "r":  # reset to fit
        global scale
        scale = max(0.25, min(fit_scale_x, fit_scale_y))
        redraw()

def on_mousewheel(event):
    # Ctrl + عجلة الفأرة للتكبير/التصغير
    if (event.state & 0x0004) != 0:  # Control modifier
        if event.delta > 0:
            zoom(0.10)
        else:
            zoom(-0.10)

root.bind("<Key>", on_key)
# دعم Windows/Mac/Linux لاختلاف delta
canvas.bind_all("<MouseWheel>", on_mousewheel)      # Windows / macOS
canvas.bind_all("<Button-4>", lambda e: zoom(0.10))  # Linux scroll up
canvas.bind_all("<Button-5>", lambda e: zoom(-0.10)) # Linux scroll down

# إنهاء المستند بعد إعداد العرض (نحتفظ بالصفحة مفتوحة ضمن سياق البرنامج)
doc.close()

root.mainloop()
