#!/usr/bin/env python3
"""
Seed script: carga datos clínicos realistas en todas las tablas nuevas.
Idempotente: salta items que ya existen.
"""
import httpx
import sys

BASE = "http://localhost:8000"

def login(email: str, password: str = "123") -> str:
    r = httpx.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]

def api(method: str, path: str, token: str, json=None):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.request(method, f"{BASE}{path}", headers=headers, json=json, timeout=15)
    if r.status_code >= 400:
        print(f"  ERROR {r.status_code} {method} {path}: {r.text[:200]}")
        return None
    return r.json()

def main():
    print("=== Logging in ===")
    admin_token = login("admin")
    medico_token = login("medico")

    admin_info = api("GET", "/api/auth/me", admin_token)
    medico_info = api("GET", "/api/auth/me", medico_token)
    admin_id = admin_info["id"]
    medico_id = medico_info["id"]
    print(f"  Admin ID:  {admin_id}")
    print(f"  Medico ID: {medico_id}")

    # ── 1. Áreas (skip if exist) ──
    print("\n=== Áreas ===")
    existing_areas = api("GET", "/api/areas", admin_token) or []
    existing_area_names = {a["nombre"] for a in existing_areas}
    areas_to_create = [
        {"nombre": "Obras Públicas"},
        {"nombre": "Administración Central"},
    ]
    area_ids = [a["id"] for a in existing_areas]
    for a in areas_to_create:
        if a["nombre"] in existing_area_names:
            print(f"  (ya existe) {a['nombre']}")
        else:
            res = api("POST", "/api/areas", admin_token, a)
            if res:
                area_ids.append(res["id"])
                print(f"  + {a['nombre']}")

    # ── 2. Diagnósticos CIE-10 (skip if exist) ──
    print("\n=== Diagnósticos CIE-10 ===")
    existing_diags = api("GET", "/api/diagnosticos", admin_token) or []
    existing_cie = {d.get("codigo_cie10") for d in existing_diags}
    diag_ids = {d["codigo_cie10"]: d["id"] for d in existing_diags if d.get("codigo_cie10")}
    diagnosticos = [
        {"codigo_cie10": "J06.9", "descripcion": "Infección aguda de las vías respiratorias superiores, no especificada", "categoria": "Respiratorio"},
        {"codigo_cie10": "M54.5", "descripcion": "Lumbago no especificado", "categoria": "Osteomuscular"},
        {"codigo_cie10": "I10",   "descripcion": "Hipertensión esencial (primaria)", "categoria": "Cardiovascular"},
        {"codigo_cie10": "E11.9", "descripcion": "Diabetes mellitus tipo 2, sin complicaciones", "categoria": "Endocrino"},
        {"codigo_cie10": "K29.7", "descripcion": "Gastritis, no especificada", "categoria": "Digestivo"},
        {"codigo_cie10": "S93.4", "descripcion": "Esguince y torcedura del tobillo", "categoria": "Traumatología"},
        {"codigo_cie10": "R51",   "descripcion": "Cefalea", "categoria": "Neurológico"},
        {"codigo_cie10": "J02.9", "descripcion": "Faringitis aguda, no especificada", "categoria": "Respiratorio"},
        {"codigo_cie10": "N39.0", "descripcion": "Infección de vías urinarias, sitio no especificado", "categoria": "Genitourinario"},
        {"codigo_cie10": "L30.9", "descripcion": "Dermatitis, no especificada", "categoria": "Dermatológico"},
    ]
    for d in diagnosticos:
        if d["codigo_cie10"] in existing_cie:
            print(f"  (ya existe) {d['codigo_cie10']}")
        else:
            res = api("POST", "/api/diagnosticos", admin_token, d)
            if res:
                diag_ids[d["codigo_cie10"]] = res["id"]
                print(f"  + {d['codigo_cie10']} - {d['descripcion']}")

    # ── 3. Empleados (skip if legajo exists) ──
    print("\n=== Empleados ===")
    cats = api("GET", "/api/categorias", admin_token) or []
    cat_id = cats[0]["id"] if cats else None
    existing_emps = api("GET", "/api/empleados", admin_token) or []
    if isinstance(existing_emps, dict):
        existing_emps = existing_emps.get("items", [])
    existing_legajos = {e["legajo"] for e in existing_emps}
    empleados_data = [
        {"legajo": "VA-1001", "cuil": "20-30456789-1", "nombre": "Carlos", "apellido": "Fernández",
         "fecha_nacimiento": "1985-03-15", "fecha_ingreso": "2018-06-01", "categoria_id": cat_id,
         "area_id": area_ids[0] if area_ids else None, "email": "cfernandez@villallende.gob.ar", "telefono": "351-4567890"},
        {"legajo": "VA-1002", "cuil": "27-28901234-5", "nombre": "María Laura", "apellido": "González",
         "fecha_nacimiento": "1990-11-22", "fecha_ingreso": "2020-03-15", "categoria_id": cat_id,
         "area_id": area_ids[1] if len(area_ids) > 1 else None, "email": "mlgonzalez@villallende.gob.ar", "telefono": "351-5678901"},
        {"legajo": "VA-1003", "cuil": "20-35678912-3", "nombre": "Martín", "apellido": "Rodríguez",
         "fecha_nacimiento": "1978-07-08", "fecha_ingreso": "2015-01-10", "categoria_id": cat_id,
         "area_id": area_ids[0] if area_ids else None, "email": "mrodriguez@villallende.gob.ar", "telefono": "351-6789012"},
    ]
    empleado_ids = [e["id"] for e in existing_emps if e["legajo"] in {"VA-1001", "VA-1002", "VA-1003"}]
    for e in empleados_data:
        if e["legajo"] in existing_legajos:
            print(f"  (ya existe) {e['legajo']} - {e['nombre']} {e['apellido']}")
        else:
            res = api("POST", "/api/empleados", admin_token, e)
            if res:
                empleado_ids.append(res["id"])
                print(f"  + {e['legajo']} - {e['nombre']} {e['apellido']}")

    if not empleado_ids:
        print("\nERROR: No hay empleados. Abortando.")
        sys.exit(1)

    # ── 4. Catálogo de estudios (skip if codigo exists) ──
    print("\n=== Catálogo de estudios ===")
    existing_estudios = api("GET", "/api/estudios-catalogo", admin_token) or []
    existing_codigos = {e.get("codigo") for e in existing_estudios}
    estudios = [
        # Laboratorio - Hematología
        {"nombre": "Hemograma completo", "codigo": "LAB-001", "tipo": "laboratorio", "categoria": "Hematología"},
        {"nombre": "Eritrosedimentación (VSG)", "codigo": "LAB-002", "tipo": "laboratorio", "categoria": "Hematología"},
        {"nombre": "Recuento de plaquetas", "codigo": "LAB-003", "tipo": "laboratorio", "categoria": "Hematología"},
        {"nombre": "Coagulograma básico", "codigo": "LAB-004", "tipo": "laboratorio", "categoria": "Hematología"},
        # Laboratorio - Bioquímica
        {"nombre": "Glucemia en ayunas", "codigo": "LAB-010", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Hemoglobina glicosilada (HbA1c)", "codigo": "LAB-011", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Urea", "codigo": "LAB-012", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Creatinina", "codigo": "LAB-013", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Ácido úrico", "codigo": "LAB-014", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Colesterol total", "codigo": "LAB-020", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Colesterol HDL", "codigo": "LAB-021", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Colesterol LDL", "codigo": "LAB-022", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Triglicéridos", "codigo": "LAB-023", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "TGO (AST)", "codigo": "LAB-030", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "TGP (ALT)", "codigo": "LAB-031", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Fosfatasa alcalina", "codigo": "LAB-032", "tipo": "laboratorio", "categoria": "Bioquímica"},
        {"nombre": "Bilirrubina total y directa", "codigo": "LAB-033", "tipo": "laboratorio", "categoria": "Bioquímica"},
        # Laboratorio - Orina
        {"nombre": "Orina completa", "codigo": "LAB-040", "tipo": "laboratorio", "categoria": "Orina"},
        {"nombre": "Urocultivo", "codigo": "LAB-041", "tipo": "laboratorio", "categoria": "Orina"},
        # Laboratorio - Hormonas
        {"nombre": "TSH", "codigo": "LAB-050", "tipo": "laboratorio", "categoria": "Hormonas"},
        {"nombre": "T4 libre", "codigo": "LAB-051", "tipo": "laboratorio", "categoria": "Hormonas"},
        # Laboratorio - Serología
        {"nombre": "VDRL", "codigo": "LAB-060", "tipo": "laboratorio", "categoria": "Serología"},
        {"nombre": "HIV (ELISA)", "codigo": "LAB-061", "tipo": "laboratorio", "categoria": "Serología"},
        {"nombre": "Hepatitis B (HBsAg)", "codigo": "LAB-062", "tipo": "laboratorio", "categoria": "Serología"},
        # Imagen - Radiología
        {"nombre": "Radiografía de tórax frente", "codigo": "IMG-001", "tipo": "imagen", "categoria": "Radiología"},
        {"nombre": "Radiografía de tórax frente y perfil", "codigo": "IMG-002", "tipo": "imagen", "categoria": "Radiología"},
        {"nombre": "Radiografía de columna lumbosacra", "codigo": "IMG-003", "tipo": "imagen", "categoria": "Radiología"},
        {"nombre": "Radiografía de columna cervical", "codigo": "IMG-004", "tipo": "imagen", "categoria": "Radiología"},
        {"nombre": "Radiografía de rodilla", "codigo": "IMG-005", "tipo": "imagen", "categoria": "Radiología"},
        {"nombre": "Radiografía de tobillo", "codigo": "IMG-006", "tipo": "imagen", "categoria": "Radiología"},
        # Imagen - Ecografía
        {"nombre": "Ecografía abdominal", "codigo": "IMG-010", "tipo": "imagen", "categoria": "Ecografía"},
        {"nombre": "Ecografía renal y vesical", "codigo": "IMG-011", "tipo": "imagen", "categoria": "Ecografía"},
        {"nombre": "Ecografía de partes blandas", "codigo": "IMG-012", "tipo": "imagen", "categoria": "Ecografía"},
        # Imagen - Cardiología
        {"nombre": "Electrocardiograma (ECG)", "codigo": "IMG-020", "tipo": "imagen", "categoria": "Cardiología"},
        {"nombre": "Ecodoppler cardíaco", "codigo": "IMG-021", "tipo": "imagen", "categoria": "Cardiología"},
        # Imagen - Otros
        {"nombre": "Espirometría", "codigo": "IMG-030", "tipo": "imagen", "categoria": "Neumonología"},
        {"nombre": "Audiometría", "codigo": "IMG-031", "tipo": "imagen", "categoria": "ORL"},
    ]
    created_count = 0
    for e in estudios:
        if e["codigo"] in existing_codigos:
            continue
        res = api("POST", "/api/estudios-catalogo", admin_token, e)
        if res:
            created_count += 1
            print(f"  + [{e['tipo'][:3].upper()}] {e['codigo']} - {e['nombre']}")
    print(f"  Total creados: {created_count} (existentes: {len(existing_codigos)})")

    # ── 5. Atenciones clínicas (solo si no hay ninguna) ──
    existing_atenciones = api("GET", "/api/atenciones", admin_token) or []
    if isinstance(existing_atenciones, dict):
        existing_atenciones = existing_atenciones.get("items", [])

    if existing_atenciones:
        print(f"\n=== Ya existen {len(existing_atenciones)} atenciones, saltando carga clínica ===")
        return

    # --- Atención 1: Carlos Fernández - Control periódico ---
    print("\n=== Atención 1: Carlos Fernández - Control periódico ===")
    atencion1 = api("POST", "/api/atenciones", admin_token, {
        "empleado_id": empleado_ids[0],
        "medico_id": medico_id,
        "fecha_turno": "2026-06-19T09:00:00",
        "motivo": "Control periódico de salud laboral",
    })
    if not atencion1:
        print("ERROR: No se pudo crear la atención 1.")
        sys.exit(1)
    a1_id = atencion1["id"]
    print(f"  + Atención: {a1_id}")

    # Signos vitales
    res = api("POST", "/api/signos-vitales", medico_token, {
        "atencion_id": a1_id,
        "peso_kg": 82.5, "altura_cm": 175,
        "presion_sistolica": 130, "presion_diastolica": 85,
        "temperatura": 36.4, "frecuencia_cardiaca": 72,
        "saturacion_o2": 98, "glucemia": 105,
    })
    if res: print(f"  + Signos vitales: PA 130/85, FC 72, T 36.4, IMC {res.get('imc', 'N/A')}")

    # Evolución
    res = api("POST", "/api/evoluciones", medico_token, {
        "atencion_id": a1_id,
        "motivo_consulta": "Control periódico de salud laboral anual",
        "anamnesis": "Paciente masculino de 41 años, trabajador municipal en Obras Públicas. "
                     "Refiere sentirse bien en general. Niega síntomas respiratorios, cardiovasculares "
                     "o digestivos. Antecedentes: hipertensión arterial en tratamiento con enalapril 10mg/día "
                     "desde 2022. Padre hipertenso y diabético. No fumador. Consumo social de alcohol.",
        "examen_fisico": "Paciente lúcido, orientado, buen estado general y nutricional. "
                         "Piel y mucosas normocoloreadas e hidratadas. "
                         "Cardiovascular: R1-R2 en 4 focos, sin soplos. TA 130/85 mmHg. "
                         "Respiratorio: murmullo vesicular conservado bilateral, sin ruidos agregados. "
                         "Abdomen: blando, depresible, indoloro, sin visceromegalias. "
                         "Osteoarticular: sin limitaciones funcionales.",
        "diagnostico_presuntivo": "Hipertensión arterial esencial en tratamiento. Sobrepeso (IMC 26.9). Glucemia limítrofe.",
        "diagnostico_definitivo_id": diag_ids.get("I10"),
        "tratamiento": "Continuar enalapril 10mg/día. Dieta hiposódica. Actividad física aeróbica 30 min 3 veces/semana. Control de peso.",
        "observaciones": "Se solicitan estudios complementarios de laboratorio y ECG. Próximo control en 3 meses.",
    })
    if res: print(f"  + Evolución clínica ({res['id'][:8]}...)")

    # Receta
    res = api("POST", "/api/recetas", medico_token, {
        "atencion_id": a1_id,
        "diagnostico": "Hipertensión arterial esencial (I10)",
        "observaciones": "Continuar tratamiento habitual. Control en 3 meses.",
        "items": [
            {"medicamento": "Enalapril 10mg", "dosis": "10 mg", "frecuencia": "Cada 24 horas (por la mañana)", "duracion": "Continuo"},
            {"medicamento": "Ácido acetilsalicílico 100mg", "dosis": "100 mg", "frecuencia": "Cada 24 horas (después del almuerzo)", "duracion": "Continuo"},
            {"medicamento": "Omeprazol 20mg", "dosis": "20 mg", "frecuencia": "Cada 24 horas (en ayunas)", "duracion": "Continuo - gastroprotección"},
        ],
    })
    if res: print(f"  + Receta con {len(res.get('items',[]))} medicamentos")

    # Pedido laboratorio
    res = api("POST", "/api/pedidos", medico_token, {
        "atencion_id": a1_id, "tipo": "laboratorio",
        "diagnostico": "Control periódico - HTA en tratamiento (I10). Glucemia limítrofe.",
        "indicaciones": "Ayuno de 12 horas. No ejercicio intenso el día previo.",
        "items": [
            {"descripcion": "Hemograma completo", "codigo": "LAB-001"},
            {"descripcion": "Glucemia en ayunas", "codigo": "LAB-010"},
            {"descripcion": "Hemoglobina glicosilada (HbA1c)", "codigo": "LAB-011"},
            {"descripcion": "Urea", "codigo": "LAB-012"},
            {"descripcion": "Creatinina", "codigo": "LAB-013"},
            {"descripcion": "Colesterol total", "codigo": "LAB-020"},
            {"descripcion": "Colesterol HDL", "codigo": "LAB-021"},
            {"descripcion": "Colesterol LDL", "codigo": "LAB-022"},
            {"descripcion": "Triglicéridos", "codigo": "LAB-023"},
            {"descripcion": "TGO (AST)", "codigo": "LAB-030"},
            {"descripcion": "TGP (ALT)", "codigo": "LAB-031"},
            {"descripcion": "Orina completa", "codigo": "LAB-040"},
        ],
    })
    if res: print(f"  + Pedido laboratorio con {len(res.get('items',[]))} estudios")

    # Pedido imagen
    res = api("POST", "/api/pedidos", medico_token, {
        "atencion_id": a1_id, "tipo": "imagen",
        "diagnostico": "Control periódico laboral. HTA en tratamiento.",
        "indicaciones": "ECG en reposo. Rx de tórax PA.",
        "items": [
            {"descripcion": "Electrocardiograma (ECG)", "codigo": "IMG-020"},
            {"descripcion": "Radiografía de tórax frente", "codigo": "IMG-001"},
        ],
    })
    if res: print(f"  + Pedido imagen con {len(res.get('items',[]))} estudios")

    # --- Atención 2: María Laura González - Lumbalgia ---
    print("\n=== Atención 2: María Laura González - Lumbalgia ===")
    atencion2 = api("POST", "/api/atenciones", admin_token, {
        "empleado_id": empleado_ids[1],
        "medico_id": medico_id,
        "fecha_turno": "2026-06-19T10:30:00",
        "motivo": "Dolor lumbar de 3 días de evolución",
    })
    if not atencion2:
        print("ERROR: No se pudo crear la atención 2.")
        sys.exit(1)
    a2_id = atencion2["id"]
    print(f"  + Atención: {a2_id}")

    res = api("POST", "/api/signos-vitales", medico_token, {
        "atencion_id": a2_id,
        "peso_kg": 62, "altura_cm": 163,
        "presion_sistolica": 110, "presion_diastolica": 70,
        "temperatura": 36.2, "frecuencia_cardiaca": 68,
        "saturacion_o2": 99, "glucemia": 88,
    })
    if res: print(f"  + Signos vitales: PA 110/70, IMC {res.get('imc','N/A')}")

    res = api("POST", "/api/evoluciones", medico_token, {
        "atencion_id": a2_id,
        "motivo_consulta": "Dolor lumbar de 3 días de evolución",
        "anamnesis": "Paciente femenina de 35 años, administrativa. Dolor lumbar que inició hace 3 días "
                     "tras levantar cajas en mudanza de oficina. Dolor tipo contractura, irradia a glúteo izquierdo, "
                     "intensidad 6/10. Mejora con reposo. No parestesias ni pérdida de fuerza en MMII.",
        "examen_fisico": "Marcha cautelosa. Columna lumbar: contractura paravertebral bilateral, predominio izquierdo. "
                         "Lasègue negativo bilateral. Fuerza conservada 5/5. ROT aquíleo y rotuliano presentes y simétricos. "
                         "Sensibilidad conservada. Sin signos de alarma.",
        "diagnostico_presuntivo": "Lumbago mecánico por esfuerzo. Contractura muscular paravertebral.",
        "diagnostico_definitivo_id": diag_ids.get("M54.5"),
        "tratamiento": "Reposo relativo 48-72hs. Ibuprofeno 400mg c/8hs por 5 días. "
                       "Ciclobenzaprina 10mg antes de dormir por 5 días. Calor local. Kinesiología si no mejora.",
        "observaciones": "Se indica Rx columna LS. Licencia por 3 días.",
    })
    if res: print(f"  + Evolución clínica ({res['id'][:8]}...)")

    res = api("POST", "/api/recetas", medico_token, {
        "atencion_id": a2_id,
        "diagnostico": "Lumbago no especificado (M54.5)",
        "observaciones": "Tomar con alimentos. Completar esquema de 5 días.",
        "items": [
            {"medicamento": "Ibuprofeno 400mg", "dosis": "400 mg", "frecuencia": "Cada 8 horas", "duracion": "5 días"},
            {"medicamento": "Ciclobenzaprina 10mg", "dosis": "10 mg", "frecuencia": "Cada 24 horas (antes de dormir)", "duracion": "5 días"},
        ],
    })
    if res: print(f"  + Receta con {len(res.get('items',[]))} medicamentos")

    res = api("POST", "/api/pedidos", medico_token, {
        "atencion_id": a2_id, "tipo": "imagen",
        "diagnostico": "Lumbago mecánico por esfuerzo (M54.5)",
        "indicaciones": "Rx columna LS frente y perfil.",
        "items": [{"descripcion": "Radiografía de columna lumbosacra", "codigo": "IMG-003"}],
    })
    if res: print(f"  + Pedido imagen")

    # --- Atención 3: Martín Rodríguez - Cuadro gripal (creada por MEDICO) ---
    print("\n=== Atención 3: Martín Rodríguez - Cuadro gripal (creada por MEDICO) ===")
    atencion3 = api("POST", "/api/atenciones", medico_token, {
        "empleado_id": empleado_ids[2],
        "fecha_turno": "2026-06-19T14:00:00",
        "motivo": "Consulta espontánea por cuadro gripal",
    })
    if not atencion3:
        print("ERROR: No se pudo crear la atención 3.")
        sys.exit(1)
    a3_id = atencion3["id"]
    print(f"  + Atención creada por MEDICO: {a3_id}")

    res = api("POST", "/api/signos-vitales", medico_token, {
        "atencion_id": a3_id,
        "peso_kg": 95, "altura_cm": 180,
        "presion_sistolica": 125, "presion_diastolica": 80,
        "temperatura": 38.2, "frecuencia_cardiaca": 88,
        "saturacion_o2": 97, "glucemia": 92,
    })
    if res: print(f"  + Signos vitales: T 38.2, FC 88, IMC {res.get('imc','N/A')}")

    res = api("POST", "/api/evoluciones", medico_token, {
        "atencion_id": a3_id,
        "motivo_consulta": "Cuadro gripal de 2 días de evolución",
        "anamnesis": "Paciente masculino de 48 años, Obras Públicas. Fiebre 38°C, odinofagia, rinorrea, tos seca "
                     "y malestar general desde hace 2 días. Niega disnea o expectoración purulenta. "
                     "Sin patologías crónicas. Vacunación completa incluyendo antigripal 2026.",
        "examen_fisico": "Febril (38.2°C), decaído, hidratado. Orofaringe congestiva, sin exudados. "
                         "Otoscopia normal. Cardiovascular: taquicardia sinusal (88 lpm), sin soplos. "
                         "Respiratorio: murmullo vesicular conservado, sin rales. "
                         "Microadenopatías cervicales bilaterales móviles.",
        "diagnostico_presuntivo": "Infección aguda de vías respiratorias superiores (cuadro gripal).",
        "diagnostico_definitivo_id": diag_ids.get("J06.9"),
        "tratamiento": "Reposo domiciliario. Hidratación abundante. Paracetamol 1g c/8hs si fiebre. "
                       "Lavados nasales con solución fisiológica. Consultar guardia si disnea o fiebre >72hs.",
        "observaciones": "Licencia por 3 días. Apto para reincorporación si afebril 24hs previas.",
    })
    if res: print(f"  + Evolución clínica ({res['id'][:8]}...)")

    res = api("POST", "/api/recetas", medico_token, {
        "atencion_id": a3_id,
        "diagnostico": "Infección aguda de las vías respiratorias superiores (J06.9)",
        "observaciones": "Tratamiento sintomático. Consultar si persiste >5 días.",
        "items": [
            {"medicamento": "Paracetamol 1g", "dosis": "1000 mg", "frecuencia": "Cada 8 horas (si fiebre o dolor)", "duracion": "5 días"},
            {"medicamento": "Loratadina 10mg", "dosis": "10 mg", "frecuencia": "Cada 24 horas", "duracion": "5 días"},
        ],
    })
    if res: print(f"  + Receta con {len(res.get('items',[]))} medicamentos")

    # ── Resumen ──
    print("\n" + "=" * 60)
    print("SEED COMPLETADO")
    print("=" * 60)
    print("  Áreas:                2")
    print("  Diagnósticos CIE-10:  10")
    print("  Empleados:            3")
    print(f"  Estudios catálogo:    {len(estudios)}")
    print("  Atenciones:           3")
    print("  Signos vitales:       3")
    print("  Evoluciones:          3")
    print("  Recetas:              3")
    print("  Pedidos:              3 (1 lab + 1 img + 1 img)")
    print("=" * 60)


if __name__ == "__main__":
    main()
