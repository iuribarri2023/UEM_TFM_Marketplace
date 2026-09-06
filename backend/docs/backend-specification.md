> **Implementation amendment (v0.2 / corrected backend).** The original specification below is retained as project context. Two later decisions supersede specific early-PoC statements: (1) `GenericSolutionSlot` is now a first-class relational child of `GenericSolution` from the initial catalogue model, with variable properties/metrics in JSONB; (2) administrative JSON + IFC bundle import is now supported for both generic solutions and manufacturer/commercial DRAFT solutions. Asset persistence uses `generic_solution_assets` and `commercial_solution_assets` association tables as described in the file-management sections below. See `AGENTS.md`, `ARCHITECTURE.md`, `docs/import-data.md` and `schemas/import/` for the current implementation contract.

# AVRA VIVA Marketplace

## Especificación inicial para la implementación del backend con Flask

## 1. Contexto y objetivo

Quiero desarrollar el backend de **AVRA VIVA Marketplace**, una plataforma web para consultar, gestionar y publicar soluciones constructivas asociadas a modelos BIM/IFC.

La primera implementación debe realizarse en:

- Python.
- Flask.
- PostgreSQL.
- SQLAlchemy.
- Alembic.
- Almacenamiento de archivos en filesystem.

La arquitectura debe diseñarse de forma que una futura implementación equivalente en **Java + Spring Boot** sea relativamente sencilla.

Por ello, Flask debe utilizarse principalmente como **capa HTTP/API**, evitando introducir lógica de negocio directamente en los endpoints.

La aplicación debe empezar como un **monolito modular**, no como microservicios.

---

# 2. Tipos de producto del Marketplace

La plataforma contiene dos familias principales de soluciones.

## 2.1. Soluciones genéricas

Las soluciones genéricas son productos de referencia o de “marca blanca”.

No representan productos comerciales concretos ni pertenecen a un fabricante.

Representan soluciones constructivas genéricas y se organizan mediante la taxonomía AVRA:

```
System
   ↓
Subsystem
   ↓
Archetype
   ↓
Generic Solution
```

Ejemplo conceptual:

```
Envelope
   ↓
Façades
   ↓
Ventilated façade
   ↓
Generic ventilated façade solution 01
```

Cada solución genérica puede contener:

- código AVRA;
- nombre;
- descripción;
- propiedades técnicas;
- prestaciones;
- métricas;
- slots o componentes cuando sea necesario;
- referencias externas;
- coste;
- GWP A1-A3;
- propiedades energéticas;
- nivel de industrialización;
- archivos asociados;
- al menos un modelo IFC/BIM cuando corresponda.

Las soluciones genéricas sólo pueden ser creadas o modificadas por administradores.

---

# 3. Soluciones comerciales

Las soluciones comerciales son productos reales aportados por fabricantes.

Cada solución comercial:

- pertenece a un fabricante;
- está relacionada con una solución genérica;
- contiene información introducida mediante formularios;
- tiene obligatoriamente un modelo IFC;
- puede incluir documentación técnica adicional;
- tiene un proceso de revisión;
- debe ser aprobada antes de formar parte del catálogo público.

La relación inicial debe ser:

```
GenericSolution
       ↑
       |
CommercialSolution
       |
       ↓
Manufacturer
```

Para el PoC se recomienda:

```
commercial_solution.generic_solution_id
```

Es decir, cada producto comercial tiene una clasificación genérica principal.

No implementar inicialmente una relación N salvo que aparezca un requisito real que lo haga necesario.

---

# 4. Roles

La aplicación debe contemplar tres comportamientos principales.

## Usuario público

No necesita autenticación para consultar el marketplace.

Puede:

- consultar sistemas;
- consultar subsistemas;
- consultar arquetipos;
- consultar soluciones genéricas;
- consultar soluciones comerciales aprobadas;
- consultar fabricantes;
- visualizar información técnica;
- acceder a archivos públicos;
- visualizar o descargar IFC públicos.

No puede modificar información.

---

## Fabricante

Un fabricante autenticado puede:

- consultar todo el catálogo público;
- crear soluciones comerciales;
- editar sus propias soluciones;
- completar formularios;
- subir modelos IFC;
- subir documentación;
- guardar soluciones como borrador;
- enviar soluciones para revisión;
- consultar su estado de aprobación.

No puede:

- editar soluciones genéricas;
- editar productos de otros fabricantes;
- aprobar productos;
- modificar la taxonomía AVRA.

---

## Administrador

Puede:

- consultar cualquier contenido;
- crear soluciones genéricas;
- modificar soluciones genéricas;
- gestionar la taxonomía;
- gestionar fabricantes;
- revisar productos comerciales;
- modificar productos si es necesario;
- aprobar productos;
- rechazar productos;
- publicar o archivar contenido;
- consultar información de auditoría.

Los permisos deben comprobarse siempre en el backend.

Nunca deben depender exclusivamente del frontend.

---

# 5. Arquitectura general

Utilizar:

**Modular Monolith + REST API + PostgreSQL + Filesystem**

Arquitectura conceptual:

```
                  WEB FRONTEND
                       |
                       |
                    REST API
                       |
                       v
                +-------------+
                |    FLASK    |
                | HTTP Layer  |
                +-------------+
                       |
                       v
              Application Services
                       |
                       v
                 Domain Model
                       |
              +--------+--------+
              |                 |
              v                 v
         Repositories       FileStorage
              |                 |
              v                 v
         PostgreSQL         Filesystem
                                  |
                            +-----+-----+
                            |     |     |
                           IFC   PDF   Images
```

La aplicación debe mantener una separación explícita entre:

```
HTTP / API
     ↓
Application Services
     ↓
Domain
     ↓
Repositories
     ↓
Infrastructure
```

---

# 6. Principio fundamental de arquitectura

Flask NO debe contener la lógica de negocio.

Evitar:

```
@blueprint.route("/solutions/<id>/approve", methods=["POST"])
def approve_solution(id):
    # cargar datos
    # verificar permisos
    # modificar estados
    # gestionar archivos
    # guardar auditoría
    # enviar respuesta
```

Preferir:

```
Flask endpoint
       ↓
ApprovalService
       ↓
CommercialSolutionRepository
       ↓
PostgreSQL
```

Conceptualmente:

```
def approve_solution(solution_id):
    current_user = get_current_user()

    result = approval_service.approve(
        solution_id=solution_id,
        user=current_user
    )

    return result
```

Toda la lógica importante debe vivir fuera del Blueprint.

---

# 7. Stack recomendado

Utilizar inicialmente:

```
Python 3.12+
Flask
SQLAlchemy 2.x
Pydantic 2.x
Alembic
PostgreSQL
psycopg
```

Autenticación:

```
JWT access tokens
JWT refresh tokens
Argon2 o bcrypt
```

Testing:

```
pytest
Flask test client
```

BIM:

```
IfcOpenShell
```

Servidor producción:

```
Gunicorn
```

Reverse proxy:

```
Nginx
```

---

# 8. ¿Por qué Pydantic aunque utilicemos Flask?

Utilizar Pydantic para los DTO y la validación de entrada/salida.

Por ejemplo:

```
class CommercialSolutionCreate(BaseModel):
    generic_solution_id: UUID
    name: str
    description: str | None = None
    technical_data: dict = {}
```

El flujo debe ser:

```
HTTP JSON
   ↓
Pydantic DTO
   ↓
Application Service
   ↓
Domain / Repository
```

Esto proporciona una separación clara entre:

```
API payload
Database model
Domain logic
```

y conceptualmente se traduce muy fácilmente posteriormente a Java:

```
Pydantic Model
      ↓
Java DTO / Record
```

---

# 9. No utilizar Flask-SQLAlchemy como núcleo de arquitectura

Es posible utilizar Flask-SQLAlchemy, pero para este proyecto recomiendo utilizar principalmente **SQLAlchemy 2 directamente**.

El objetivo es evitar:

```
Domain
   ↓
Flask-SQLAlchemy
   ↓
Flask
```

y mantener:

```
Domain
   ↓
Repository
   ↓
SQLAlchemy
```

Flask debe desconocer los detalles de persistencia.

Esto facilita:

- testing;
- scripts independientes;
- importadores;
- procesos CLI;
- futura migración a Java;
- mantenimiento.

---

# 10. Equivalencia futura con Java

La arquitectura Python debe poder mapearse aproximadamente así:

```
Python                         Java

Flask Blueprint               @RestController

Pydantic DTO                  DTO / Java Record

Application Service           @Service

Repository                    Repository

SQLAlchemy                     JPA / Hibernate

Alembic                        Flyway / Liquibase

JWT authentication            Spring Security

FileStorage interface         StorageService interface

IfcOpenShell adapter          BIM adapter

Dependency injection          Spring Dependency Injection
```

La lógica debe seguir siendo:

```
Controller
    ↓
Service
    ↓
Repository
    ↓
Database
```

tanto en Python como en Java.

---

# 11. Application Factory

La aplicación Flask debe construirse utilizando el patrón:

```
create_app()
```

Conceptualmente:

```
def create_app(config=None):

    app = Flask(__name__)

    configure_app(app)
    configure_database(app)
    configure_security(app)

    register_blueprints(app)
    register_error_handlers(app)

    return app
```

No crear una aplicación monolítica en:

```
app.py
```

con todos los endpoints y dependencias.

---

# 12. Blueprints

Utilizar Blueprints para dividir funcionalmente la API.

Por ejemplo:

```
/api/v1/auth
/api/v1/catalog
/api/v1/manufacturer
/api/v1/admin
```

Blueprints:

```
auth_blueprint
catalog_blueprint
manufacturer_blueprint
admin_blueprint
assets_blueprint
```

Los Blueprints representan únicamente la capa HTTP.

No representan necesariamente módulos de dominio.

---

# 13. Modelo principal PostgreSQL

## Systems

```
systems
-------
id
code
name
description
created_at
updated_at
```

---

## Subsystems

```
subsystems
----------
id
system_id
code
name
description
created_at
updated_at
```

---

## Archetypes

```
archetypes
----------
id
subsystem_id
code
name
description
created_at
updated_at
```

---

## Generic Solutions

```
generic_solutions
-----------------
id
archetype_id

code
name
description

technical_data JSONB

status

created_at
updated_at
created_by
updated_by
```

Relación:

```
System
  |
  +-- Subsystem
        |
        +-- Archetype
              |
              +-- GenericSolution
```

---

# 14. IDs y códigos AVRA

Separar siempre:

```
Database ID
```

de:

```
AVRA functional code
```

Por ejemplo:

```
id
=
UUID("...")

code
=
FAC-VEN-001
```

La primary key debería ser preferentemente:

```
UUID
```

El código AVRA debe ser:

```
UNIQUE
```

pero no debe actuar como clave primaria.

Esto permitirá cambiar la nomenclatura funcional en el futuro sin romper relaciones de base de datos.

---

# 15. Fabricantes

```
manufacturers
-------------
id
name
tax_id
website
description
status

created_at
updated_at
```

Un fabricante es una organización.

No debe confundirse con un usuario.

---

# 16. Usuarios

```
users
-----
id
manufacturer_id NULL

email
password_hash

role
is_active

created_at
updated_at
```

Roles iniciales:

```
ADMIN
MANUFACTURER
```

No es necesario crear inicialmente:

```
PUBLIC_USER
```

porque el contenido público puede consultarse sin autenticación.

---

# 17. Relación User / Manufacturer

Un usuario administrador tendrá:

```
manufacturer_id = NULL
```

Un usuario de fabricante tendrá:

```
manufacturer_id = UUID(...)
```

La arquitectura debe soportar desde el principio:

```
Manufacturer
     |
     +-- User A
     +-- User B
     +-- User C
```

aunque inicialmente cada fabricante sólo tenga un usuario.

---

# 18. CommercialSolution

Tabla principal:

```
commercial_solutions
--------------------

id

manufacturer_id
generic_solution_id

code
name
description

technical_data JSONB

workflow_status

created_by
created_at

updated_by
updated_at

submitted_at

approved_at
approved_by
```

Estados:

```
DRAFT
SUBMITTED
APPROVED
REJECTED
ARCHIVED
```

---

# 19. Workflow de publicación

El proceso inicial debe ser:

```
                  Manufacturer
                       |
                       v
                     DRAFT
                       |
                    submit
                       |
                       v
                   SUBMITTED
                       |
                  Admin review
                   /       \
                  /         \
                 v           v
           APPROVED       REJECTED
```

Sólo:

```
APPROVED
```

es visible públicamente.

Un producto:

```
DRAFT
SUBMITTED
REJECTED
```

sólo debe ser visible para:

- el fabricante propietario;
- administradores.

---

# 20. Edición posterior a aprobación

Una decisión importante:

Si un fabricante modifica información relevante de una solución previamente aprobada, la aplicación no debería modificar silenciosamente el producto público aprobado.

Para el PoC puede utilizarse una estrategia sencilla:

```
APPROVED
   |
 manufacturer edits
   ↓
DRAFT
   |
 submit
   ↓
SUBMITTED
   |
 admin
   ↓
APPROVED
```

Más adelante puede implementarse versionado completo.

No implementar todavía un sistema complejo de versiones.

---

# 21. Atributos técnicos

Las propiedades técnicas pueden variar significativamente entre arquetipos.

Por ejemplo:

```
Window
Façade
Roof
Heat pump
Ventilation system
PV panel
```

no requieren los mismos atributos.

No crear una tabla distinta por cada tipo de producto.

Utilizar inicialmente:

```
technical_data JSONB
```

Ejemplo:

```
{
  "thermal_transmittance": 0.8,
  "thermal_transmittance_unit": "W/m2K",
  "gwp_a1_a3": 32.4,
  "gwp_unit": "kgCO2e/m2",
  "fire_rating": "EI60"
}
```

---

# 22. Qué debe ser relacional y qué debe ser JSONB

Mantener como columnas SQL:

```
id
code
name
description

manufacturer_id
generic_solution_id
archetype_id

status
workflow_status

created_at
updated_at
approved_at
```

Mantener inicialmente en JSONB:

```
prestaciones específicas
atributos técnicos
métricas variables
propiedades dependientes del arquetipo
```

No utilizar JSONB para todo.

PostgreSQL debe seguir siendo una base de datos relacional.

---

# 23. Formularios dinámicos

En una fase posterior puede implementarse:

```
AttributeDefinition
FormSchema
```

Conceptualmente:

```
Archetype
    |
    +-- FormSchema
            |
            +-- AttributeDefinition
            +-- AttributeDefinition
            +-- AttributeDefinition
```

Esto permitirá que el frontend genere automáticamente formularios distintos para:

```
ventanas
fachadas
cubiertas
HVAC
etc.
```

No es imprescindible implementarlo en la primera iteración.

---

# 24. Slots

Las soluciones genéricas pueden posteriormente contener slots.

Ejemplo:

```
GenericSolution
     |
     +-- Slot
     +-- Slot
     +-- Slot
```

Los slots pueden representar componentes o posiciones funcionales dentro de una solución.

La arquitectura debe dejar espacio para añadir:

```
slots
slot_attributes
```

pero no es necesario convertirlos inicialmente en el núcleo del marketplace.

Primero debe funcionar correctamente:

```
GenericSolution
        ↕
CommercialSolution
```

---

# 25. Gestión de archivos

Los archivos no deben almacenarse dentro de PostgreSQL.

No utilizar:

```
BYTEA
BLOB
```

para IFC, PDF o imágenes salvo una razón futura muy específica.

PostgreSQL almacena únicamente:

```
metadata
path
checksum
```

Los archivos viven en filesystem.

---

# 26. Asset

Crear una entidad general:

```
assets
------
id

filename
original_filename

mime_type
file_type

relative_path

size_bytes
sha256

uploaded_by
created_at
```

Tipos iniciales:

```
IFC
PDF
IMAGE
TECHNICAL_DOCUMENT
OTHER
```

---

# 27. Relación de assets

Permitir asociar archivos tanto a:

```
GenericSolution
```

como a:

```
CommercialSolution
```

Mediante:

```
generic_solution_assets
commercial_solution_assets
```

Esto evita acoplar la tabla `assets` a un único tipo de producto.

---

# 28. IFC obligatorio

Toda solución comercial publicada debe disponer como mínimo de:

```
1 IFC
```

La regla debe comprobarse cuando se realiza:

```
SUBMIT
```

No necesariamente durante:

```
DRAFT
```

Es decir, un fabricante puede crear:

```
DRAFT
```

sin IFC.

Pero:

```
DRAFT
    ↓
submit()
```

debe fallar si no existe un IFC válido.

---

# 29. Almacenamiento físico

En desarrollo:

```
/storage
```

Ejemplo:

```
storage/

├── generic-solutions/
│   └── {generic_solution_uuid}/
│       ├── model.ifc
│       └── preview.png
│
└── manufacturers/
    └── {manufacturer_uuid}/
        └── solutions/
            └── {commercial_solution_uuid}/
                ├── model.ifc
                ├── datasheet.pdf
                └── image.jpg
```

No utilizar nombres proporcionados directamente por el usuario como rutas físicas.

Generar identificadores seguros.

---

# 30. Rutas relativas

La base de datos guarda:

```
manufacturers/UUID/solutions/UUID/model.ifc
```

No:

```
/home/developer/viva/backend/storage/...
```

ni:

```
C:\Users\...
```

ni:

```
/opt/viva/storage/...
```

La raíz se configura mediante:

```
STORAGE_ROOT
```

Esto permitirá mover el backend de local a la VM sin modificar los registros.

---

# 31. Abstracción FileStorage

Definir:

```
class FileStorage(Protocol):

    def save(...):
        ...

    def delete(...):
        ...

    def exists(...):
        ...

    def open(...):
        ...
```

Primera implementación:

```
LocalFileStorage
```

Futuro:

```
S3FileStorage
AzureBlobStorage
MinIOFileStorage
```

El dominio no debe saber dónde está físicamente almacenado el fichero.

---

# 32. Servicio BIM

IfcOpenShell debe quedar encapsulado.

No utilizar llamadas a IfcOpenShell directamente dentro de Blueprints.

Crear:

```
BimService
```

o:

```
IfcService
```

Interfaz conceptual:

```
class BimService:

    def validate(self, path):
        ...

    def extract_metadata(self, path):
        ...
```

---

# 33. Metadatos IFC iniciales

No intentar construir inicialmente una plataforma BIM completa.

Extraer como máximo:

```
IFC schema
project name
number of entities
main GlobalIds
file size
checksum
upload date
```

Posteriormente puede evolucionar hacia:

```
property extraction
geometry
classification
automatic validation
IFC viewer integration
```

---

# 34. Visualización IFC

La visualización 3D no debe formar parte de la responsabilidad principal del backend Flask.

El backend proporciona:

```
IFC file
metadata
permissions
download URL
```

El frontend podrá posteriormente utilizar:

```
IFC.js
That Open Engine
xeokit
u otro visor WebGL/WebAssembly
```

La elección del visor debe tratarse como una decisión independiente.

---

# 35. API REST

Utilizar:

```
/api/v1
```

como prefijo general.

---

# 36. Catálogo público

```
GET /api/v1/systems

GET /api/v1/subsystems

GET /api/v1/archetypes

GET /api/v1/generic-solutions

GET /api/v1/generic-solutions/{id}

GET /api/v1/commercial-solutions

GET /api/v1/commercial-solutions/{id}

GET /api/v1/manufacturers

GET /api/v1/manufacturers/{id}
```

---

# 37. Filtros de catálogo

Preparar:

```
GET /api/v1/generic-solutions
    ?system=
    ?subsystem=
    ?archetype=
    ?search=
```

Y:

```
GET /api/v1/commercial-solutions
    ?system=
    ?subsystem=
    ?archetype=
    ?generic_solution=
    ?manufacturer=
    ?search=
```

Los resultados deben estar paginados.

Por ejemplo:

```
?page=1
?page_size=20
```

---

# 38. Authentication API

Inicialmente:

```
POST /api/v1/auth/login

POST /api/v1/auth/refresh

GET /api/v1/auth/me
```

El login devuelve:

```
access_token
refresh_token
```

---

# 39. API del fabricante

```
GET
/api/v1/manufacturer/solutions
```

```
POST
/api/v1/manufacturer/solutions
```

```
GET
/api/v1/manufacturer/solutions/{id}
```

```
PATCH
/api/v1/manufacturer/solutions/{id}
```

```
DELETE
/api/v1/manufacturer/solutions/{id}
```

```
POST
/api/v1/manufacturer/solutions/{id}/submit
```

---

# 40. Gestión de archivos

```
POST
/api/v1/manufacturer/solutions/{id}/assets
```

```
GET
/api/v1/assets/{id}
```

```
DELETE
/api/v1/manufacturer/solutions/{id}/assets/{asset_id}
```

---

# 41. API administrativa

```
POST
/api/v1/admin/generic-solutions
```

```
PATCH
/api/v1/admin/generic-solutions/{id}
```

```
POST
/api/v1/admin/commercial-solutions/{id}/approve
```

```
POST
/api/v1/admin/commercial-solutions/{id}/reject
```

Posteriormente:

```
POST
/api/v1/admin/catalog/import
```

---

# 42. Autorización por ownership

Una de las reglas fundamentales debe ser:

```
commercial_solution.manufacturer_id
==
current_user.manufacturer_id
```

para cualquier operación realizada por un fabricante.

Nunca aceptar:

```
manufacturer_id
```

proporcionado libremente por el frontend para determinar la propiedad.

El fabricante propietario se obtiene del usuario autenticado.

---

# 43. JWT

Flujo:

```
email + password
       ↓
AuthenticationService
       ↓
access_token
refresh_token
```

El token puede contener:

```
user_id
role
manufacturer_id
```

pero PostgreSQL continúa siendo la fuente de verdad.

No utilizar el contenido del JWT como sustituto permanente de las comprobaciones de autorización.

---

# 44. Auditoría

Crear:

```
audit_log
---------
id

user_id

entity_type
entity_id

action

metadata JSONB

created_at
```

Registrar al menos:

```
CREATE
UPDATE
DELETE

UPLOAD_FILE
DELETE_FILE

SUBMIT
APPROVE
REJECT
ARCHIVE
```

---

# 45. Catálogo AVRA existente

El catálogo de soluciones genéricas procede actualmente de un Excel estructurado que se transforma a JSON.

Mantener este pipeline:

```
Excel
   ↓
Parser
   ↓
Canonical JSON
   ↓
Validator
   ↓
Database Importer
   ↓
PostgreSQL
```

La API Flask NO debe leer el Excel para responder peticiones.

Durante ejecución:

```
Frontend
   ↓
Flask
   ↓
PostgreSQL
```

---

# 46. Importación

Crear un proceso independiente:

```
scripts/import_catalog.py
```

Por ejemplo:

```
python -m scripts.import_catalog catalog.json
```

Debe soportar importación por:

```
system
subsystem
archetype
generic_solution
```

y preferiblemente:

```
UPSERT
```

en lugar de eliminar y reconstruir todo el catálogo.

---

# 47. CLI Flask

También se puede exponer posteriormente como:

```
flask catalog import catalog.json
```

pero la lógica de importación debe estar en:

```
CatalogImportService
```

y no dentro del comando Flask.

De este modo:

```
CLI
API
tests
```

pueden reutilizar exactamente el mismo servicio.

---

# 48. Estructura propuesta del backend

```
backend/

├── app/
│
│   ├── __init__.py
│   ├── factory.py
│
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── catalog.py
│   │       ├── manufacturers.py
│   │       ├── commercial_solutions.py
│   │       ├── assets.py
│   │       └── admin.py
│
│   ├── domain/
│   │
│   │   ├── catalog/
│   │   ├── solutions/
│   │   ├── manufacturers/
│   │   ├── users/
│   │   └── assets/
│   │
│   ├── services/
│   │
│   │   ├── auth_service.py
│   │   ├── catalog_service.py
│   │   ├── generic_solution_service.py
│   │   ├── commercial_solution_service.py
│   │   ├── approval_service.py
│   │   ├── asset_service.py
│   │   ├── bim_service.py
│   │   └── catalog_import_service.py
│   │
│   ├── repositories/
│   │
│   │   ├── system_repository.py
│   │   ├── archetype_repository.py
│   │   ├── generic_solution_repository.py
│   │   ├── commercial_solution_repository.py
│   │   ├── manufacturer_repository.py
│   │   ├── user_repository.py
│   │   └── asset_repository.py
│   │
│   ├── db/
│   │
│   │   ├── models/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── transaction.py
│   │
│   ├── schemas/
│   │
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── manufacturer.py
│   │   ├── commercial_solution.py
│   │   └── asset.py
│   │
│   ├── infrastructure/
│   │
│   │   ├── storage/
│   │   │   ├── base.py
│   │   │   └── local_storage.py
│   │   │
│   │   └── bim/
│   │       └── ifcopenshell_adapter.py
│   │
│   └── core/
│       ├── config.py
│       ├── security.py
│       ├── permissions.py
│       ├── exceptions.py
│       └── logging.py
│
├── migrations/
│
├── scripts/
│   └── import_catalog.py
│
├── tests/
│
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── storage/
│
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# 49. Database Session

La sesión SQLAlchemy debe gestionarse explícitamente por request o mediante una unidad de trabajo.

Conceptualmente:

```
HTTP Request
     ↓
SQLAlchemy Session
     ↓
Service
     ↓
Repositories
     ↓
commit / rollback
     ↓
close
```

Evitar commits dispersos dentro de cada repository.

Preferiblemente la transacción se controla desde la capa de servicio o mediante:

```
UnitOfWork
```

---

# 50. Repository Pattern

Ejemplo conceptual:

```
class CommercialSolutionRepository:

    def get_by_id(self, solution_id):
        ...

    def list_by_manufacturer(self, manufacturer_id):
        ...

    def add(self, solution):
        ...

    def delete(self, solution):
        ...
```

El servicio utiliza:

```
CommercialSolutionRepository
```

no consultas SQLAlchemy dispersas.

Esto será especialmente útil para una futura equivalencia:

```
Python Repository
      ↓
Java Repository
```

---

# 51. Application Services

Los casos de uso deben representarse mediante servicios.

Ejemplos:

```
AuthenticationService

CatalogService

GenericSolutionService

CommercialSolutionService

ApprovalService

AssetService

BimService

CatalogImportService
```

Ejemplo:

```
CommercialSolutionService.submit()
```

debe comprobar:

```
ownership

estado actual

datos obligatorios

existencia de IFC

validez del IFC
```

y sólo entonces cambiar:

```
DRAFT → SUBMITTED
```

---

# 52. Excepciones de dominio

Definir excepciones como:

```
EntityNotFound

PermissionDenied

InvalidWorkflowTransition

ValidationError

MissingIfcFile

InvalidIfcFile

DuplicateCode
```

Los Blueprints transforman estas excepciones en HTTP.

Ejemplo:

```
EntityNotFound
      ↓
404

PermissionDenied
      ↓
403

InvalidWorkflowTransition
      ↓
409

ValidationError
      ↓
400 / 422
```

La lógica de dominio no debe generar directamente respuestas Flask.

---

# 53. Respuestas HTTP

Mantener un formato consistente.

Ejemplo de éxito:

```
{
  "data": {
    "id": "...",
    "name": "..."
  }
}
```

Ejemplo de error:

```
{
  "error": {
    "code": "INVALID_WORKFLOW_TRANSITION",
    "message": "Solution cannot be submitted from its current state."
  }
}
```

No devolver trazas Python al cliente.

---

# 54. PostgreSQL

Utilizar adecuadamente:

```
UUID
VARCHAR
TEXT
BOOLEAN
TIMESTAMPTZ
JSONB

FOREIGN KEY
UNIQUE
CHECK
INDEX
```

---

# 55. Índices iniciales

Crear índices al menos sobre:

```
systems.code

subsystems.system_id
subsystems.code

archetypes.subsystem_id
archetypes.code

generic_solutions.archetype_id
generic_solutions.code

commercial_solutions.generic_solution_id
commercial_solutions.manufacturer_id
commercial_solutions.workflow_status

users.email

manufacturers.name
```

Posteriormente evaluar:

```
GIN
```

para consultas sobre JSONB.

No añadir índices GIN indiscriminadamente.

---

# 56. Migraciones

Utilizar Alembic desde el primer día.

Nunca modificar manualmente producción.

Flujo:

```
SQLAlchemy model change
       ↓
Alembic migration
       ↓
review
       ↓
apply migration
```

---

# 57. Seguridad de uploads

Implementar como mínimo:

- límite de tamaño;
- whitelist de tipos;
- validación MIME;
- extensión válida;
- nombre físico generado por servidor;
- checksum SHA-256;
- protección contra path traversal;
- nunca ejecutar archivos subidos;
- almacenamiento fuera de carpetas servidas directamente por Flask.

Para IFC:

```
.ifc
```

pero no confiar exclusivamente en la extensión.

---

# 58. Configuración

Toda configuración dependiente del entorno debe proceder de variables de entorno.

Por ejemplo:

```
APP_ENV

DATABASE_URL

JWT_SECRET_KEY

STORAGE_ROOT

MAX_UPLOAD_SIZE

CORS_ORIGINS
```

No guardar secretos en Git.

---

# 59. Entornos

Soportar:

```
development
testing
production
```

Por ejemplo:

```
DevelopmentConfig
TestingConfig
ProductionConfig
```

sin duplicar la lógica de aplicación.

---

# 60. Desarrollo local

Utilizar Docker Compose para:

```
PostgreSQL
```

y opcionalmente para el backend.

Ejemplo conceptual:

```
docker-compose

├── backend
└── postgres
```

Con volumen:

```
postgres_data
```

y:

```
storage_data
```

---

# 61. Producción inicial

Arquitectura suficiente para la primera máquina virtual:

```
Internet
   |
   v
 Nginx
   |
   v
Gunicorn
   |
   v
 Flask
   |
   +---------- PostgreSQL
   |
   +---------- /storage
```

El filesystem debe estar en almacenamiento persistente.

No guardar datos persistentes únicamente dentro de la capa efímera del contenedor.

---

# 62. Health endpoint

Crear desde el inicio:

```
GET /health
```

Respuesta:

```
{
  "status": "ok"
}
```

Posteriormente:

```
GET /health/ready
GET /health/live
```

si fuese necesario.

---

# 63. Testing

Separar:

```
tests/unit
tests/integration
tests/api
```

## Unit

Probar:

```
Services
Domain rules
Workflow
Permissions
```

sin arrancar servidor HTTP.

## Integration

Probar:

```
Repositories
PostgreSQL
FileStorage
Ifc adapter
```

## API

Probar:

```
Blueprints
HTTP status
authentication
serialization
```

---

# 64. Primeras reglas a testear

Como mínimo:

```
Public user cannot see DRAFT product.

Manufacturer can edit own DRAFT.

Manufacturer cannot edit another manufacturer's product.

Manufacturer cannot approve products.

Manufacturer cannot edit GenericSolution.

Product cannot be submitted without IFC.

SUBMITTED cannot be edited freely by manufacturer.

Only ADMIN can approve.

Only APPROVED products appear in public catalog.
```

---

# 65. OpenAPI

Flask no genera automáticamente un contrato OpenAPI simplemente por definir los endpoints.

La API debe documentarse explícitamente.

Para el PoC se puede:

1. mantener inicialmente un `openapi.yaml`; o
2. añadir posteriormente una extensión de documentación OpenAPI.

La decisión no debe condicionar el dominio ni los servicios.

Es especialmente recomendable disponer de OpenAPI porque permitirá definir claramente el contrato entre:

```
Frontend
    ↕
Backend
```

y facilitar una futura implementación Java.

---

# 66. Principios que debe seguir la implementación

Aplicar:

```
Separation of Concerns

Dependency Inversion

Repository Pattern

Service Layer

DTO separation

Explicit transactions

Framework-independent domain
```

Sin intentar aplicar un DDD excesivamente académico.

El objetivo es mantener el sistema:

```
simple
explicit
modular
testable
portable
```

---

# 67. Qué NO implementar inicialmente

Evitar:

```
Microservices

Kubernetes

Kafka

RabbitMQ

Event sourcing

CQRS

GraphQL

Elasticsearch

Redis salvo necesidad real

S3 inicialmente

BIM processing distribuido

motor paramétrico complejo

versionado avanzado

workflow engine

tablas diferentes para cada arquetipo

formularios completamente dinámicos

BLOB de IFC en PostgreSQL
```

---

# 68. Decisiones arquitectónicas principales

Mantener inicialmente:

```
✓ Flask

✓ Application Factory

✓ Flask Blueprints

✓ REST API

✓ Modular Monolith

✓ SQLAlchemy 2

✓ PostgreSQL

✓ Alembic

✓ Pydantic DTOs

✓ JWT

✓ Repository Pattern

✓ Application Services

✓ Files outside PostgreSQL

✓ FileStorage abstraction

✓ IfcOpenShell adapter

✓ JSONB for variable attributes

✓ GenericSolution taxonomy

✓ CommercialSolution → GenericSolution

✓ Manufacturer ownership

✓ Admin approval workflow

✓ Excel → JSON → PostgreSQL importer
```

---

# 69. Fases de implementación

## Fase 1 — Skeleton

Implementar:

```
Flask

create_app()

configuration

Blueprints

SQLAlchemy

PostgreSQL

Alembic

Docker Compose

GET /health
```

La aplicación debe arrancar correctamente antes de implementar negocio.

---

## Fase 2 — Catálogo genérico

Implementar:

```
System

Subsystem

Archetype

GenericSolution
```

Crear:

```
repositories
services
DTOs
API endpoints
```

y endpoints públicos de consulta.

---

## Fase 3 — Importador

Implementar:

```
Canonical JSON
      ↓
CatalogImportService
      ↓
PostgreSQL
```

Debe ser posible importar el catálogo existente generado desde Excel.

---

## Fase 4 — Fabricantes y autenticación

Implementar:

```
Manufacturer

User

AuthenticationService

JWT

roles

permissions
```

---

## Fase 5 — Productos comerciales

Implementar:

```
CommercialSolution
```

con estados:

```
DRAFT
SUBMITTED
APPROVED
REJECTED
ARCHIVED
```

---

## Fase 6 — Assets

Implementar:

```
Asset

FileStorage

LocalFileStorage

upload

download

checksum
```

---

## Fase 7 — BIM

Implementar:

```
IfcOpenShellAdapter

BimService

IFC validation

basic metadata extraction
```

---

## Fase 8 — Approval workflow

Implementar:

```
submit

approve

reject

audit
```

---

# 70. MVP técnico que debe resultar

La primera versión funcional debe permitir:

```
GET /health
```

```
GET /api/v1/generic-solutions
```

```
GET /api/v1/generic-solutions/{id}
```

```
POST /api/v1/auth/login
```

```
POST /api/v1/manufacturer/solutions
```

```
PATCH /api/v1/manufacturer/solutions/{id}
```

```
POST /api/v1/manufacturer/solutions/{id}/assets
```

```
POST /api/v1/manufacturer/solutions/{id}/submit
```

```
POST /api/v1/admin/commercial-solutions/{id}/approve
```

y finalmente:

```
GET /api/v1/commercial-solutions
```

debe devolver únicamente las soluciones aprobadas.

---

# 71. Primera implementación solicitada

Comienza implementando únicamente la **Fase 1 y la estructura necesaria para la Fase 2**.

Genera un proyecto ejecutable que contenga:

```
Flask
Application Factory
Blueprints

PostgreSQL
SQLAlchemy 2
Alembic

Pydantic

Docker Compose

configuration by environment

GET /health
```

y los modelos iniciales:

```
System
Subsystem
Archetype
GenericSolution
```

No implementes todavía toda la plataforma de una sola vez.

Primero crea una base arquitectónica limpia sobre la que podamos iterar.

La implementación debe demostrar claramente el flujo:

```
HTTP Request
      ↓
Flask Blueprint
      ↓
Pydantic DTO
      ↓
Application Service
      ↓
Repository
      ↓
SQLAlchemy
      ↓
PostgreSQL
```

El código debe estar preparado para que posteriormente incorporemos:

```
Manufacturer
User
CommercialSolution
Asset
IFC
Approval workflow
```

sin necesidad de reorganizar toda la aplicación.

---

# 72. Criterio arquitectónico final

El objetivo no es crear la arquitectura más sofisticada posible.

El objetivo es construir una arquitectura suficientemente limpia para que VIVA pueda crecer desde un PoC hacia una plataforma real.

La regla general será:

```
Flask gestiona HTTP.

Pydantic gestiona contratos de datos.

Services gestionan casos de uso.

Domain contiene reglas de negocio.

Repositories abstraen persistencia.

SQLAlchemy habla con PostgreSQL.

FileStorage gestiona archivos.

BimService gestiona IFC.
```

Esta separación debe mantenerse como principio principal durante toda la implementación.