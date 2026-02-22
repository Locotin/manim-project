# Proyecto inicial de Manim

## 1) Activar entorno virtual

```bash
source .venv/bin/activate
```

## 2) Instalar Manim

```bash
pip install -r requirements.txt
```

## 3) Renderizar animación de prueba

```bash
manim -pqh scene.py AnimacionBasica
```

Notas:
- El video se genera dentro de `media/`.
- Puedes cambiar `-pqh` por `-pql` para render más rápido en baja calidad.
