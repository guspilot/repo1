"""Carga por aprobador con la matriz de la política POL-CO-0031 (7.3) + recurrencia V3.

Escenarios de incertidumbre: costo unitario mediano (USD 100 / 150 / 250) y
volumen (2 o 4 casos por tienda al mes). Reutiliza el generador del simulacro.

Uso:  python3 carga_matriz.py [corridas]
"""
import sys, statistics as st
from collections import Counter
import simulacro_recurrencia as sim

UNIT_N1, UNIT_N2, CASO_MAX = 100, 600, 3000     # política 7.3 + D1 (caso > 3 000 → nivel 3)


def nivel(c, recurrente):
    if c["ubic"] == "CD":
        if recurrente or c["unit"] > UNIT_N1 or c["usd"] > CASO_MAX:
            return "CI (CD > 100/u, recurrencia o caso > 3 000)"
        return "Gerente Logística CD"
    if recurrente or c["unit"] > UNIT_N2 or c["usd"] > CASO_MAX:
        return "CI (tienda N3)"
    if c["unit"] > UNIT_N1:
        return "Operaciones local (N2)"
    return "Gerente de Tienda (N1)"


def main():
    corridas = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    roles = ["Gerente de Tienda (N1)", "Operaciones local (N2)", "CI (tienda N3)",
             "Gerente Logística CD", "CI (CD > 100/u, recurrencia o caso > 3 000)"]
    base = dict(sim.S)
    print("| Escenario | Casos/mes | " + " | ".join(roles) + " | CI total/día hábil | % CI por recurrencia |")
    print("|---|---|" + "---|" * (len(roles) + 2))
    for vol in (2.0, 4.0):
        for med in (100, 150, 250):
            sim.S.update(base, casos_tienda_mes=vol, casos_cd_mes=40 * vol / 2, costo_mediana=med)
            por_rol, meses_tot, ci_rec, ci_tot = Counter(), 0, 0, 0
            for seed in range(corridas):
                mundo = sim.generar(seed)
                res = sim.evaluar(mundo, "V3 α=0.01 R3b=3000")
                for c, m in res:
                    n = nivel(c, bool(m))
                    por_rol[n] += 1
                    if n.startswith("CI"):
                        ci_tot += 1
                        if m and nivel(c, False) != n:
                            ci_rec += 1
                meses_tot += sim.S["dias_eval"] / 30
            mes = {k: v / meses_tot for k, v in por_rol.items()}
            dia = lambda k: mes.get(k, 0) / sim.S["dias_habiles_mes"]
            total = sum(mes.values())
            ci_dia = sum(dia(k) for k in roles if k.startswith("CI"))
            celdas = " | ".join(f"{dia(k):.1f}" for k in roles)
            print(f"| {vol:.0f} casos/tienda/mes · unitario mediano USD {med} | {total:.0f} | {celdas} | {ci_dia:.1f} | {100 * ci_rec / max(1, ci_tot):.0f} % |")
    sim.S.update(base)


if __name__ == "__main__":
    main()
