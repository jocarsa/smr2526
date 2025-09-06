# 📚 Ciclo Formativo SMR 25/26

Este repositorio contiene la **estructura completa de contenidos** del ciclo formativo de **Sistemas Microinformáticos y Redes (SMR)** para el curso **2025/2026**, construida automáticamente a partir de la documentación oficial.

Los documentos originales en formato `.docx` han sido procesados para generar una **jerarquía clara de carpetas**:
- **Nivel 1:** Curso → `Primer curso` / `Segundo curso`
- **Nivel 2:** Módulo profesional (p. ej. `Montaje y mantenimiento de equipos`)
- **Nivel 3:** Secciones principales (extraídas de encabezados H1 de los documentos)
- **Nivel 4:** Sub-secciones específicas (extraídas de encabezados H2), cada una con:
  - `001-Contenidos básicos/Contenidos básicos.md`
  - `002-Ejercicios/README.md`
  - `003-Criterios de evaluación/Criterios de evaluación.md`

Esto permite mantener **alineación directa con los resultados de aprendizaje y criterios oficiales**, pero en un formato más navegable y apto para trabajo colaborativo.

---

## 🎯 Objetivos del repositorio
- Servir de **base documental y pedagógica** para docentes y alumnado.  
- Ofrecer una estructura modular lista para ser **rellenada con contenidos, ejemplos, ejercicios y rúbricas**.  
- Permitir un **seguimiento progresivo** del curso mediante versionado en GitHub.  
- Facilitar la **colaboración abierta** en la preparación de materiales educativos.

---

## 🏗️ Estructura del repositorio

### Primer curso
Algunos módulos del primer curso:
- [`Caracterización de sistemas operativos`](./Primer%20curso/Caracterizacion%20de%20sistemas%20operativos)
- [`Despliegue del cableado`](./Primer%20curso/Despliegue%20del%20cableado)
- [`Instalación de aplicaciones`](./Primer%20curso/Instalacion%20de%20aplicaciones)
- [`Selección de componentes de equipos microinformáticos estándar`](./Primer%20curso/Seleccion%20de%20componentes%20de%20equipos%20microinformaticos%20estandar)
- [`Instalación de sistemas operativos libres y propietarios`](./Primer%20curso/Instalacion%20de%20sistemas%20operativos%20libres%20y%20propietarios)
- [`Interconexión de equipos en redes locales`](./Primer%20curso/Interconexion%20de%20equipos%20en%20redes%20locales)

### Segundo curso
(Ejemplos análogos, si los `.docx` incluyen SMR2)

---

## 📂 Cómo navegar
Cada subcarpeta de nivel 4 contiene:
- **Contenidos básicos** → apuntes y explicaciones generales.  
- **Ejercicios** → actividades prácticas propuestas.  
- **Criterios de evaluación** → rúbricas, descriptores y evidencias para cada apartado.  

---

## 🔧 Cómo generar la estructura desde cero
Este repositorio se apoya en un script en Python que:
1. Lee los `.docx` originales de cada módulo.
2. Detecta encabezados de nivel 1 (H1) y nivel 2 (H2).
3. Genera automáticamente la jerarquía de carpetas y archivos Markdown.

```bash
python3 docx_headings_to_structure.py
🤝 Contribución
Si eres docente: añade tus propios materiales en los apartados correspondientes.

Si eres estudiante: utiliza las carpetas de ejercicios para practicar y guardar tus soluciones.

Si detectas un error en la estructura o nomenclatura: abre un issue o envía un pull request.

📜 Licencia
Este proyecto está disponible bajo la licencia MIT.
Puedes usar, modificar y compartir estos materiales libremente, siempre citando la fuente.

🚀 Créditos
Estructura generada automáticamente a partir de los documentos oficiales del currículo de Sistemas Microinformáticos y Redes (SMR) por Jose Vicente Carratalá Sanchis.
