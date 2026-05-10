# Breach Lookup

Herramienta web interna DFIR/OSINT para verificar si un dato de identidad (cédula, email, móvil, nombre o usuario) aparece en el dataset de breach Terpel. Importa `Breach.csv` a SQLite en el primer arranque, expone una API REST con búsqueda paginada y estadísticas, y sirve un frontend HTML con modo oscuro/claro, resaltado de coincidencias y panel de estadísticas en tiempo real. Cada consulta queda registrada en `audit_log`.

---

## Requisitos

- **Local:** Python 3.12 + pip
- **Docker:** Docker Engine + Docker Compose v2

---

## Instalación y arranque

### Modo local

```bash
cd breach-lookup

# Instalar dependencias
pip install -r requirements.txt

# Crear .env a partir del ejemplo y ajustar valores
cp .env.example .env

# Arrancar (importa el CSV automáticamente en el primer inicio)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Abrir `http://localhost:8000` en el navegador.

### Modo Docker

```bash
# Colocar Breach.csv dentro de data/ (se monta como volumen)
cp /ruta/a/Breach.csv ./data/

# Copiar .env y ajustar valores
cp .env.example .env

# Construir imagen y levantar contenedor
docker compose up -d

# Ver logs de arranque
docker compose logs -f
```

El contenedor queda disponible en `http://localhost:8000`.  
Los datos persisten en `./data/breach.db` entre reinicios.

---

## Endpoints

### `GET /health`
Estado del servidor y total de registros cargados.
```bash
curl http://localhost:8000/health
```

### `GET /api/search`
Buscar registros. Parámetros: `q` (requerido), `field` (default `__all__`), `limit` (default 50, máx 200), `offset`.
```bash
# Por cédula
curl "http://localhost:8000/api/search?q=8-742-2183&field=documento"

# Búsqueda global (OR sobre 11 columnas)
curl "http://localhost:8000/api/search?q=juan.perez@gmail.com&field=__all__&limit=10"
```

### `GET /api/stats`
Totales, top 10 países, top 10 dominios de email y conteo de nulos por campo.
```bash
curl http://localhost:8000/api/stats
```

---

## Nota de seguridad

Esta herramienta contiene datos personales sensibles y está diseñada **exclusivamente para uso en red interna controlada**. No exponer el puerto 8000 a internet ni a redes no autorizadas. El archivo `Breach.csv` y la base de datos `breach.db` están excluidos del repositorio vía `.gitignore`.
