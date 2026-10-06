#!/usr/bin/env python3
"""Проверки схемы v1.2: ERC, лимиты напряжений, логика положений 0/I/II × ключ."""
import sys
from design import *

errors, warns = [], []

# ---- 1. ERC ----
pin_net = {}
for net, pins in NETS.items():
    for p in pins:
        if p in pin_net and pin_net[p] != net:
            errors.append(f"пин {p} в двух цепях: {pin_net[p]} и {net}")
        pin_net[p] = net
for p in pin_net:
    ref, pin = p.split(".")
    if ref not in PARTS:
        errors.append(f"неизвестный компонент {ref} в цепи {pin_net[p]}")
        continue
    if ref in IC_PINS and pin not in IC_PINS[ref]:
        errors.append(f"у {ref} нет пина {pin} ({pin_net[p]})")
    if ref not in IC_PINS and pin not in ("1", "2"):
        errors.append(f"{p}: у пассивного/площадки только пины 1,2")
for ref in STRICT:
    for pin in IC_PINS[ref]:
        if f"{ref}.{pin}" not in pin_net and (ref, pin) not in NC_PINS:
            errors.append(f"{ref}.{pin} не подключён (и не помечен NC)")
for ref, d in PARTS.items():
    if "pad" in d["flags"]:
        if f"{ref}.1" not in pin_net:
            errors.append(f"площадка {ref} не подключена")
        continue
    if ref in IC_PINS:
        continue
    for pin in ("1", "2"):
        if f"{ref}.{pin}" not in pin_net:
            errors.append(f"{ref}.{pin} не подключён")
for net, pins in NETS.items():
    if len(pins) < 2 and not net.startswith("NRF_SPARE"):
        warns.append(f"цепь {net} с одним пином: {pins}")

# ---- 2. лимиты напряжений ----
for p, net in pin_net.items():
    ref, pin = p.split(".")
    lim = PIN_ABSMAX.get((ref, pin))
    v = NET_VMAX.get(net)
    if lim and v and v > lim:
        errors.append(f"{p}: цепь {net} до {v} В > abs max {lim} В")

R_UP, R_DN, VCC = 100e3, 47e3, 12.0
vgs_on = -(VCC * R_UP / (R_UP + R_DN))
print(f"Vgs(Q3) при открытом Q4: {vgs_on:.2f} В (предел ±12 В, порог ≈ -0.5…-1.3 В)")
if not (-11 < vgs_on < -2.5):
    errors.append("Vgs Q3 вне допустимого окна")

# ---- 3. модель логики ----
R_KS, R_BLEED, R_ADC, R10 = 100e3, 220e3, 2e6, 1e6
def par(*r): return 1 / sum(1 / x for x in r)
Q4_VTH_MAX = 1.2  # SI2302, худший случай

def state(pos, key, vbat=3.2, v_drop=0.3):
    A, B, C = pos in ("I", "II"), pos == "I", pos == "II"
    vbsw = vbat - v_drop if A else 0.0
    vcc_in = 11.8 if A else 0.0
    vcc555 = vbsw if B else 0.0
    if C:
        v2 = vbsw
    else:  # фантом: TSG (контакт замкнут) -> R10 -> клампы МК на VDD
        i_ph = max(0.0, vbsw - 0.6) / R10 if B else 0.0
        load = par(R_BLEED, R_ADC, *([R_KS] if key else []))
        v2 = min(vbsw - 0.6 if B else 0.0, i_ph * load)
    sense = v2 if key else 0.0
    q3_on = sense > Q4_VTH_MAX and vcc_in > 0
    return dict(vcc_in=vcc_in, vcc555=vcc555, v2pwr=v2, q3_on=q3_on)

def state_v11(pos, key, vbat=3.2, v_drop=0.3):
    """v1.1: затвор Q3 -> узел N (COM+SENSE1+SENSE2 замкнуты ключом),
    N: R100k к 12 В и pull-down 10k на GND."""
    s = state(pos, key, vbat, v_drop)
    if key and s["vcc_in"] > 0:
        if pos == "II":
            n = s["v2pwr"]
        else:
            n = s["vcc_in"] * par(10e3, 2e6) / (par(10e3, 2e6) + 100e3)
        s["q3_on"] = (n - s["vcc_in"]) < -1.3
    else:
        s["q3_on"] = False
    return s

print("\nЛогика: switched-домен (BLE/датчики) ВКЛ только в положении II с ключом")
print(f"{'поз':<4}{'ключ':<6}{'Vbat':>5}{'VCC_IN':>8}{'VCC555':>8}{'V2PWR':>8}{'Q3 v1.2':>9}{'Q3 v1.1':>9}")
for pos in ("0", "I", "II"):
    for key in (False, True):
        for vbat in (3.2, 1.9):
            s, s11 = state(pos, key, vbat), state_v11(pos, key, vbat)
            want = (pos == "II" and key)
            t12 = "" if s["q3_on"] == want else " <-- ОШИБКА v1.2"
            t11 = "" if s11["q3_on"] == want else " <-- ОШИБКА v1.1"
            print(f"{pos:<4}{'да' if key else 'нет':<6}{vbat:>5}{s['vcc_in']:>8.1f}{s['vcc555']:>8.2f}"
                  f"{s['v2pwr']:>8.2f}{'ВКЛ' if s['q3_on'] else 'выкл':>9}{'ВКЛ' if s11['q3_on'] else 'выкл':>9}{t12}{t11}")
            if s["q3_on"] != want:
                errors.append(f"логика: pos={pos} key={key} vbat={vbat}: Q3={s['q3_on']}, ожидалось {want}")
            if pos != "II" and s["v2pwr"] > 0.5:
                errors.append(f"фантомное V2PWR {s['v2pwr']:.2f} В в положении {pos}")
            if pos == "II" and s["v2pwr"] < 1.7:
                warns.append(f"V2PWR={s['v2pwr']:.2f} В < 1.8 В (BOD МК)")

print("\n[регрессия v1.1] ME6211C33 на VIN=12 В: abs max 6.5 В -> ОШИБКА (в v1.2 заменён на buck U3)")
print(f"TBD-позиции: {sum('tbd' in d['flags'] for d in PARTS.values())}")
for w in warns: print("WARN ", w)
for e in errors: print("ERROR", e)
print(f"\nИТОГО: ошибок {len(errors)}, предупреждений {len(warns)}")
sys.exit(1 if errors else 0)
