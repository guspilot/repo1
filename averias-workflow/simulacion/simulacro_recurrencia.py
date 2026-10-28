"""Simulacro de la regla de recurrencia (D2) sobre un país sintético.

Genera 600 días de averías (240 de historia previa + 360 evaluados) para 1 país:
100 tiendas de distinto tamaño, 1 CD, 3 000 SKUs, 80 proveedores. Planta anomalías
conocidas y mide, para cada variante de regla, cuánta carga manda a Control de
Inventarios (CI), si detecta las anomalías y en cuántos días, y cuántos falsos
positivos genera. Todos los supuestos están en SUPUESTOS y son editables.

Uso:  python3 simulacro_recurrencia.py [corridas]
"""
import math, random, sys, statistics as st
from collections import defaultdict, deque

SUPUESTOS = dict(
    tiendas=100, casos_tienda_mes=2.0, sigma_tamano=0.45,      # tamaño lognormal, media 1
    casos_cd_mes=40, skus=3000, zipf_sku=0.7, proveedores=80, zipf_prov=1.1,
    tiendas_problema=5, mult_tienda_problema=2.5, inicio_tienda_problema=330,
    tiendas_monto=2, mult_costo_tienda_monto=3.0,               # frecuencia normal, averías 3x más caras
    skus_defectuosos=3, casos_extra_sku_mes=5, inicio_sku=360, dur_sku=120,
    casos_extra_prov_mes=6, inicio_prov=390, dur_prov=150,
    costo_mediana=150, costo_sigma=1.0,
    dias_historia=240, dias_eval=360, dias_habiles_mes=22,
)
S = SUPUESTOS
RESP_TIENDA = [("Tienda", .40), ("Transporte", .20), ("Proveedor", .25), ("Entrega cliente", .10), ("Otro", .05)]
RESP_TIENDA_PROB = [("Tienda", .70), ("Transporte", .10), ("Proveedor", .12), ("Entrega cliente", .05), ("Otro", .03)]
RESP_CD = [("CD", .45), ("Proveedor", .40), ("Transporte", .15)]


def pick(r, pares):
    x, acc = r.random(), 0
    for v, p in pares:
        acc += p
        if x <= acc:
            return v
    return pares[-1][0]


def k_poisson(lam, alfa=0.025, piso=1):
    """Menor k con P(X >= k) <= alfa para X ~ Poisson(lam)."""
    if lam <= 0:
        return piso
    cdf, k, term = 0.0, 0, math.exp(-lam)
    while True:
        if 1 - cdf <= alfa and k >= piso:
            return k
        cdf += term
        k += 1
        term *= lam / k


def poisson(r, lam):
    # Knuth; lam pequeño por día
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= r.random()
        if p <= L:
            return k
        k += 1


def generar(seed):
    r = random.Random(seed)
    n = S["tiendas"]
    tam = [math.exp(r.gauss(0, S["sigma_tamano"])) for _ in range(n)]
    m = sum(tam) / n
    tam = [t / m for t in tam]
    w_sku = [(i + 1) ** -S["zipf_sku"] for i in range(S["skus"])]
    w_prov = [(i + 1) ** -S["zipf_prov"] for i in range(S["proveedores"])]
    prov_de_sku = r.choices(range(S["proveedores"]), weights=w_prov, k=S["skus"])
    elegidas = r.sample(range(n), S["tiendas_problema"] + S["tiendas_monto"])
    problema = set(elegidas[:S["tiendas_problema"]])
    monto = set(elegidas[S["tiendas_problema"]:])
    defectuosos = r.sample(range(200, 1000), S["skus_defectuosos"])
    prov_malo = r.randrange(8, 20)
    skus_prov_malo = [s for s in range(S["skus"]) if prov_de_sku[s] == prov_malo] or [0]
    total = S["dias_historia"] + S["dias_eval"]
    casos = []

    def costo(mult=1.0):
        u = mult * S["costo_mediana"] * math.exp(r.gauss(0, S["costo_sigma"]))
        x = r.random()
        q = 1 if x < .80 else (r.randint(2, 5) if x < .95 else r.randint(6, 20))
        return round(u * q, 2)

    def nuevo(d, ubic, sku, resp, origen):
        mult = S["mult_costo_tienda_monto"] if (ubic in monto and d >= S["inicio_tienda_problema"]) else 1.0
        casos.append(dict(dia=d, ubic=ubic, sku=sku, prov=prov_de_sku[sku], resp=resp,
                          usd=costo(mult), origen=origen))

    for d in range(total):
        for i in range(n):
            lam = S["casos_tienda_mes"] / 30 * tam[i]
            es_prob = i in problema and d >= S["inicio_tienda_problema"]
            if es_prob:
                lam *= S["mult_tienda_problema"]
            for _ in range(poisson(r, lam)):
                sku = r.choices(range(S["skus"]), weights=w_sku)[0]
                nuevo(d, i, sku, pick(r, RESP_TIENDA_PROB if es_prob else RESP_TIENDA),
                      "tienda_problema" if es_prob else "normal")
        for _ in range(poisson(r, S["casos_cd_mes"] / 30)):
            sku = r.choices(range(S["skus"]), weights=w_sku)[0]
            nuevo(d, "CD", sku, pick(r, RESP_CD), "normal")
        for sku in defectuosos:
            if S["inicio_sku"] <= d < S["inicio_sku"] + S["dur_sku"]:
                for _ in range(poisson(r, S["casos_extra_sku_mes"] / 30)):
                    nuevo(d, r.choice([r.randrange(n), "CD"]), sku,
                          "Proveedor" if r.random() < .8 else "Transporte", "sku_defectuoso")
        if S["inicio_prov"] <= d < S["inicio_prov"] + S["dur_prov"]:
            for _ in range(poisson(r, S["casos_extra_prov_mes"] / 30)):
                nuevo(d, r.choice([r.randrange(n), "CD"]), r.choice(skus_prov_malo), "Proveedor", "proveedor_malo")
    return dict(casos=casos, tam=tam, problema=problema, monto=monto, defectuosos=set(defectuosos), prov_malo=prov_malo)


# ---------------------------------------------------------------- variantes de regla
class Ventana:
    """Conteo y suma por clave en ventana móvil de días."""
    def __init__(self, dias):
        self.dias, self.q = dias, defaultdict(deque)

    def agregar_y_medir(self, clave, dia, usd, contar=True):
        q = self.q[clave]
        if contar:
            q.append((dia, usd))
        while q and q[0][0] <= dia - self.dias:
            q.popleft()
        return len(q), sum(u for _, u in q)


class Historia:
    """Tasa propia de largo plazo: casos en [dia-240, dia-60) llevada a 60 días."""
    def __init__(self):
        self.d = defaultdict(list)

    def tasa60(self, clave, dia):
        xs = self.d[clave]
        return sum(1 for x in xs if dia - 240 <= x < dia - 60) / 180 * 60

    def agregar(self, clave, dia):
        self.d[clave].append(dia)


def evaluar(mundo, variante):
    tam = mundo["tam"]
    lam_pais_30 = S["casos_tienda_mes"]  # λ país por tienda en 30 días (se calibraría con Power BI)
    w = dict(sku=Ventana(60), skup=Ventana(60), prov=Ventana(60), tienda=Ventana(30))
    hist_sku, hist_prov = Historia(), Historia()
    salida = []
    for c in mundo["casos"]:
        d, motivos = c["dia"], []
        es_prov = c["resp"] == "Proveedor"
        n_sku, _ = w["sku"].agregar_y_medir(c["sku"], d, c["usd"])
        n_skup, _ = w["skup"].agregar_y_medir(c["sku"], d, c["usd"], contar=es_prov)
        n_prov, _ = w["prov"].agregar_y_medir(c["prov"], d, c["usd"], contar=es_prov)
        es_tienda = c["ubic"] != "CD"
        if es_tienda:
            n_t, usd_t = w["tienda"].agregar_y_medir(c["ubic"], d, c["usd"])

        if variante == "V0 Literal":           # la política sin umbral: 2 casos = recurrencia
            if n_sku >= 2: motivos.append("R1")
            if n_prov >= 2 and es_prov: motivos.append("R2")
            if es_tienda and n_t >= 2: motivos.append("R3a")
        elif variante == "V1 Propuesta":
            if n_sku >= 3: motivos.append("R1")
            if es_prov and n_prov >= 5: motivos.append("R2")
            if es_tienda and n_t >= 6: motivos.append("R3a")
            if es_tienda and usd_t >= 3000: motivos.append("R3b")
        elif variante == "V2 Ajustada":
            # R1: solo casos imputables al proveedor, umbral = máx(3, k de la tasa propia del SKU)
            k1 = max(3, k_poisson(hist_sku.tasa60(c["sku"], d)))
            if es_prov and n_skup >= k1: motivos.append("R1")
            # R2: umbral = máx(5, k de la tasa propia del proveedor)
            k2 = max(5, k_poisson(hist_prov.tasa60(c["prov"], d)))
            if es_prov and n_prov >= k2: motivos.append("R2")
            if es_tienda:
                t = tam[c["ubic"]]
                if n_t >= k_poisson(lam_pais_30 * t): motivos.append("R3a")
                if usd_t >= 3000 * max(1.0, t): motivos.append("R3b")
        elif variante.startswith("V3"):
            # V2 + tienda más estricta: alfa menor en R3a y R3b exige acumulación (≥3 casos), no un caso grande
            alfa = float(variante.split("α=")[1].split()[0])
            k1 = max(3, k_poisson(hist_sku.tasa60(c["sku"], d)))
            if es_prov and n_skup >= k1: motivos.append("R1")
            k2 = max(5, k_poisson(hist_prov.tasa60(c["prov"], d)))
            if es_prov and n_prov >= k2: motivos.append("R2")
            if es_tienda:
                t = tam[c["ubic"]]
                if n_t >= k_poisson(lam_pais_30 * t, alfa): motivos.append("R3a")
                umbral_b = float(variante.split("R3b=")[1]) if "R3b=" in variante else 3000
                if umbral_b > 0 and n_t >= 3 and usd_t >= umbral_b * max(1.0, t): motivos.append("R3b")
        if es_prov:
            hist_sku.agregar(c["sku"], d)
            hist_prov.agregar(c["prov"], d)
        if d >= S["dias_historia"]:
            salida.append((c, motivos))
    return salida


def metricas(mundo, res):
    meses = S["dias_eval"] / 30
    n = len(res)
    a_ci = [x for x in res if x[1]]
    por_regla = defaultdict(int)
    for _, m in a_ci:
        for r_ in set(m):
            por_regla[r_] += 1
    # detección de tiendas problema (R3)
    det_t, lag_t = 0, []
    for i in mundo["problema"]:
        dias = [c["dia"] for c, m in res if c["ubic"] == i and ({"R3a", "R3b"} & set(m)) and c["dia"] >= S["inicio_tienda_problema"]]
        if dias:
            det_t += 1
            lag_t.append(min(dias) - S["inicio_tienda_problema"])
    det_m, lag_m = 0, []
    for i in mundo["monto"]:
        dias_m = [c["dia"] for c, m in res if c["ubic"] == i and ({"R3a", "R3b"} & set(m)) and c["dia"] >= S["inicio_tienda_problema"]]
        if dias_m:
            det_m += 1
            lag_m.append(min(dias_m) - S["inicio_tienda_problema"])
    anom = mundo["problema"] | mundo["monto"]
    # falsos positivos en tiendas normales
    fp_tiendas = {c["ubic"] for c, m in res if c["ubic"] != "CD" and c["ubic"] not in anom and ({"R3a", "R3b"} & set(m))}
    casos_normales_t = [x for x in res if x[0]["ubic"] != "CD" and x[0]["ubic"] not in anom]
    fp_casos_t = sum(1 for c, m in casos_normales_t if {"R3a", "R3b"} & set(m))
    grandes = {i for i, t in enumerate(mundo["tam"]) if t >= 1.5}
    fp_grandes = len(fp_tiendas & grandes) / max(1, len(grandes - anom))
    # SKUs defectuosos (R1)
    det_s, lag_s = 0, []
    for s in mundo["defectuosos"]:
        dias = [c["dia"] for c, m in res if c["sku"] == s and "R1" in m and c["dia"] >= S["inicio_sku"]]
        if dias:
            det_s += 1
            lag_s.append(min(dias) - S["inicio_sku"])
    fp_skus = len({c["sku"] for c, m in res if "R1" in m and c["sku"] not in mundo["defectuosos"]}) / meses
    # proveedor malo (R2)
    dias = [c["dia"] for c, m in res if c["prov"] == mundo["prov_malo"] and "R2" in m and c["dia"] >= S["inicio_prov"]]
    fp_prov = len({c["prov"] for c, m in res if "R2" in m and c["prov"] != mundo["prov_malo"]})
    return {
        "% casos a CI por recurrencia": 100 * len(a_ci) / n,
        "Casos a CI por día hábil": len(a_ci) / meses / S["dias_habiles_mes"],
        "R1 casos/mes": por_regla["R1"] / meses, "R2 casos/mes": por_regla["R2"] / meses,
        "R3a casos/mes": por_regla["R3a"] / meses, "R3b casos/mes": por_regla["R3b"] / meses,
        "Tiendas problema detectadas (de 5)": det_t,
        "Días a detectar tienda problema": st.mean(lag_t) if lag_t else float("nan"),
        "Tiendas caras detectadas (de 2)": det_m,
        "Días a detectar tienda cara": st.mean(lag_m) if lag_m else float("nan"),
        "Tiendas normales marcadas en 12 meses (de 93)": len(fp_tiendas),
        "% tiendas grandes normales marcadas": 100 * fp_grandes,
        "% casos de tiendas normales a CI": 100 * fp_casos_t / max(1, len(casos_normales_t)),
        "SKUs defectuosos detectados (de 3)": det_s,
        "Días a detectar SKU defectuoso": st.mean(lag_s) if lag_s else float("nan"),
        "SKUs normales marcados por mes": fp_skus,
        "Proveedor malo detectado (0/1)": 1 if dias else 0,
        "Días a detectar proveedor malo": (min(dias) - S["inicio_prov"]) if dias else float("nan"),
        "Proveedores normales marcados": fp_prov,
    }


def main():
    corridas = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    variantes = ["V0 Literal", "V1 Propuesta", "V2 Ajustada", "V3 α=0.01 R3b=3000", "V3 α=0.01 R3b=5000", "V3 α=0.01 R3b=0"]
    acum = {v: defaultdict(list) for v in variantes}
    casos_mes = []
    for seed in range(corridas):
        mundo = generar(seed)
        casos_mes.append(sum(1 for c in mundo["casos"] if c["dia"] >= S["dias_historia"]) / (S["dias_eval"] / 30))
        for v in variantes:
            for k, x in metricas(mundo, evaluar(mundo, v)).items():
                if not (isinstance(x, float) and math.isnan(x)):
                    acum[v][k].append(x)
    print(f"Corridas: {corridas} | casos/mes promedio en el país: {st.mean(casos_mes):.0f}\n")
    claves = list(acum[variantes[0]].keys()) + [k for v in variantes for k in acum[v] if k not in acum[variantes[0]]]
    vistas = []
    print("| Métrica | " + " | ".join(variantes) + " |")
    print("|---|" + "---|" * len(variantes))
    for k in claves:
        if k in vistas:
            continue
        vistas.append(k)
        fila = []
        for v in variantes:
            xs = acum[v].get(k, [])
            fila.append(f"{st.mean(xs):.1f}" if xs else "—")
        print(f"| {k} | " + " | ".join(fila) + " |")


if __name__ == "__main__":
    main()
