import os
from PIL import Image, ImageDraw, ImageFont


def _linear_gradient(size, start_color, end_color):
    base = Image.new("RGBA", size, start_color)
    top = Image.new("RGBA", size, end_color)
    mask = Image.new("L", size)
    mask_data = []
    for y in range(size[1]):
        for x in range(size[0]):
            mask_data.append(int(255 * (x / size[0])))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


def generate_app_icon():
    size = (256, 256)
    gradient = _linear_gradient(size, (60, 160, 240), (60, 220, 200))
    mask = _rounded_mask(size, 56)
    icon = Image.new("RGBA", size, (0, 0, 0, 0))
    icon.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(icon)
    try:
        font = ImageFont.truetype("arialbd.ttf", 160)
    except OSError:
        font = ImageFont.load_default()

    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size[0] - tw) / 2 - bbox[0]
    y = (size[1] - th) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=(20, 20, 25, 255))

    return icon


def _draw_line_icon(draw, points, width=2, color=(130, 130, 130, 255)):
    draw.line(points, fill=color, width=width, joint="curve")


def _create_icon_set(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    s = 24
    c = (130, 130, 130, 255)
    icons = {}

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_line_icon(d, [(4, 12), (10, 12)], color=c)
    _draw_line_icon(d, [(7, 9), (10, 12), (7, 15)], color=c)
    icons["main"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([7, 4, 17, 14], outline=c, width=2)
    d.line([12, 14, 12, 20], fill=c, width=2)
    d.line([7, 20, 17, 20], fill=c, width=2)
    icons["settings"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 20, 20], outline=c, width=2, radius=3)
    d.line([12, 8, 12, 16], fill=c, width=2)
    d.line([8, 12, 16, 12], fill=c, width=2)
    icons["calculator"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 20, 20], outline=c, width=2, radius=2)
    d.line([8, 9, 16, 9], fill=c, width=2)
    d.line([8, 13, 16, 13], fill=c, width=2)
    d.line([8, 17, 13, 17], fill=c, width=2)
    icons["notes"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([5, 6, 19, 6], fill=c, width=2)
    d.line([5, 12, 19, 12], fill=c, width=2)
    d.line([5, 18, 13, 18], fill=c, width=2)
    icons["commands"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 7, 20, 18], outline=c, width=2, radius=2)
    d.line([10, 7, 10, 5], fill=c, width=2)
    d.line([14, 7, 14, 5], fill=c, width=2)
    icons["clipboard"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc([8, 4, 16, 20], 0, 180, fill=c, width=2)
    d.line([8, 12, 8, 20], fill=c, width=2)
    d.line([16, 12, 16, 20], fill=c, width=2)
    icons["collapse"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([7, 7, 17, 17], fill=c, width=2)
    d.line([17, 7, 7, 17], fill=c, width=2)
    icons["exit"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(12, 16), (6, 10), (18, 10)], fill=c)
    d.line([6, 7, 18, 7], fill=c, width=2)
    icons["pin_on"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(12, 8), (6, 14), (18, 14)], fill=c)
    d.line([6, 17, 18, 17], fill=c, width=2)
    icons["pin_off"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([8, 12, 16, 12], fill=c, width=2)
    icons["minimize"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([7, 7, 17, 17], outline=c, width=2, radius=1)
    icons["maximize"] = img

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([7, 7, 17, 17], fill=c, width=2)
    d.line([17, 7, 7, 17], fill=c, width=2)
    icons["close"] = img

    for name, image in icons.items():
        image.save(os.path.join(output_dir, f"{name}.png"))


def generate_all():
    base = os.path.dirname(__file__)
    app_icon = generate_app_icon()
    app_icon.save(os.path.join(base, "icon.ico"), format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    app_icon.resize((24, 24), Image.LANCZOS).save(os.path.join(base, "app_icon.png"))
    _create_icon_set(os.path.join(base, "icons"))


if __name__ == "__main__":
    generate_all()
    print("Icons generated: icon.ico, app_icon.png, icons/")
