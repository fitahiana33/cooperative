"""Printable paginated tables, with wrapped cells and French text preserved."""
import textwrap


def table_pdf(title: str, rows: list[dict]) -> bytes:
    def literal(value):
        raw = str(value).replace("→", " vers ").replace("\u202f", " ").encode("cp1252", errors="replace")
        return "".join(chr(c) if 32 <= c < 127 and c not in (40, 41, 92) else f"\\{c:03o}" for c in raw)

    keys = list(rows[0]) if rows else ["Résultat"]
    width = 762 / len(keys)
    columns = max(5, int((width - 12) / 4.4))
    pages = []
    commands = []
    y = 0

    def text(x, baseline, value, size=8):
        commands.append(f"BT /F1 {size} Tf {x:.2f} {baseline:.2f} Td ({literal(value)}) Tj ET")

    def cell_row(values, header=False):
        nonlocal y
        cells = [textwrap.wrap(str(value), width=columns, replace_whitespace=True) or [""] for value in values]
        height = max(map(len, cells)) * 12 + 12
        if y - height < 35:
            next_page()
        if header:
            commands.append(f"0.94 g 40 {y-height:.2f} 762 {height} re f 0 g")
        for index, lines in enumerate(cells):
            for offset, line in enumerate(lines):
                text(46 + index * width, y - 13 - offset * 12, line)
            commands.append(f"0.8 G {40+index*width:.2f} {y-height:.2f} {width:.2f} {height} re S 0 G")
        y -= height

    def next_page():
        nonlocal commands, y
        if commands:
            pages.append("\n".join(commands).encode("ascii"))
        commands = []
        for index, line in enumerate(textwrap.wrap(title, width=105)):
            text(40, 565 - index * 16, line, 11)
        text(755, 20, f"Page {len(pages)+1}")
        y = 530
        cell_row([key.replace("_", " ").capitalize() for key in keys], header=True)

    next_page()
    for row in rows or [{"Résultat": "Aucune donnée pour cette période."}]:
        # Split unusually long rows across pages without losing cell contents.
        wrapped = [textwrap.wrap(str(row.get(key, "")), width=columns) or [""] for key in keys]
        for offset in range(0, max(map(len, wrapped)), 30):
            cell_row(["\n".join(cell[offset:offset+30]) for cell in wrapped])
    pages.append("\n".join(commands).encode("ascii"))
    page_ids = [4 + index * 2 for index in range(len(pages))]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               f"<< /Type /Pages /Kids [{' '.join(f'{n} 0 R' for n in page_ids)}] /Count {len(pages)} >>".encode(),
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    for number, stream in zip(page_ids, pages):
        objects.extend([
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R >> >> /Contents {number+1} 0 R >>".encode(),
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
        ])
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)
