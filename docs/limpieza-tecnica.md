# Limpieza de datos

El proceso de limpieza implementado en `scripts/setup_db.py`

## Entrada

`data/PRUEBA_TECNICA.xlsx`, dos hojas: SECOP y CC2026. Se leen con `pandas.read_excel(..., sheet_name=...)`.

## Filtro de columnas por porcentaje

Funcion: `drop_empty_columns(df, min_fill_ratio)`.

Para cada columna se calcula `df[col].notna().sum() / total_filas`. Si el resultado es menor a 5%, la columna se descarta. Se aplica antes de cualquier otra transformacion, sobre el DataFrame crudo tal como lo entrega `pandas.read_excel`.

Este filtro es cuantitativo, no distingue si una columna con pocos datos es importante o no, solo mide presencia de valores no nulos, sirve para descartar columnas de metadata de exportacion.

## Normalizacion de nombres de columna

Funcion: `normalize_column_name(name)`.

Transforma un encabezado de Excel a snake_case ASCII, en codigo esta asi:

```python
name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
name = re.sub(r"_+", "_", name).strip("_").lower()
```

Por ejemplo: `"Fecha de Publicación"` -> `"fecha_de_publicacion"`, esto se hace despues del filtro de columnas para no tener que normalizar nombres que de todas formas se van a descartar.

## Filtro de filas por llave de negocio

Se aplica sobre la columna llave ya normalizada (`referencia` en SECOP, `radicacion` en CC2026):

```python
df = df.dropna(subset=[key_col])
df[key_col] = df[key_col].astype(str).str.strip()
df = df[df[key_col] != ""]
```

Elimina filas sin valor en la llave, y normaliza el valor a string sin espacios sobrantes

## Deteccion de filas de paginacion

En la revision de datos, se pueden ver numeros que contienen una llave generica, sin embargo las demas columnas contienen informacion inconstante, estas son representadas con un numero entre el 1 y el 3, para detectar estos casos utilizamos el filtro:

```python
es_contador_paginacion = df[key_col].str.match(r"^\d{1,3}$") & df["column_8_url"].isna()
df = df[~es_contador_paginacion]
```

Se valido manualmente contra el archivo original, donde 32 filas cumplen este patron, todas con Referencia, Descripción y Fase actual repitiendo el mismo numero (ej. fila con Referencia=7, Descripción=7, Fase actual=7)

## Eliminacion de duplicados

Se conserva el primer valor de la llave encontrado en el orden del archivo original, en el archivo no se detectaron duplicados reales en el archivo de la prueba tras el paso anterior, pero la regla queda activa por robustez ante nuevas cargas del mismo Excel.

```python
df = df.drop_duplicates(subset=[key_col], keep="first")
```

## Persistencia de evidencia

El resultado de cada hoja se guarda como CSV en `data/secop_clean.csv` y `data/cc2026_clean.csv` antes de cargarse a la base de datos, como evidencia del resultado de la limpieza.

## Carga a PostgreSQL

Antes de instanciar los modelos SQLAlchemy, se fuerza el tipo de cada celda a string:

```python
for _, fila in df.fillna("").astype(str).iterrows():
    db.add(Secop(**fila.to_dict()))
```

Esto es necesario porque pandas puede inferir tipos por celda, sin esta conversion explicita, SQLAlchemy genera una sola sentencia INSERT por lotes con tipos de parametro inferidos por columna, y una celda con tipo distinto al resto de la columna produce un error de tipo en PostgreSQL (`invalid input syntax for type integer`) porque el driver asume que toda la columna es del mismo tipo Python en ese lote.
