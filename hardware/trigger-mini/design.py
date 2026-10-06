"""Плата «Мини» v1.2 — единственный источник правды: компоненты + цепи.

Имена пинов у микросхем — функциональные (как в даташите). Номера пинов
подставляются позже из официальных символов (EasyEDA/LCSC), см. TBD.
"""

# ref: (value, footprint, lcsc, note, flags)
# flags: 'pad' — площадка/внешний узел (не в BOM), 'tbd' — значение уточнить
PARTS = {}

def P(ref, val, fp, lcsc="", note="", flags=()):
    PARTS[ref] = dict(val=val, fp=fp, lcsc=lcsc, note=note, flags=set(flags))

# ---------- Z1 вход ----------
P("D1", "SS14", "SMA", "C2480", "защита от переполюсовки")
P("C1", "10uF X7R 10V", "0603")
P("C2", "10uF X7R 10V", "0603")
P("C4", "47uF 10V polymer/tantalum low-profile", "tbd", note="вход boost, буфер на пик соленоида", flags=["tbd"])
# ---------- Z2 boost 3 -> 12 В ----------
P("U1", "MT3608", "SOT-23-6", "C84817")
P("L1", "4.7uH shielded Isat>2A", "4x4", note="между VBAT_SW и SW (ИСПРАВЛЕНО: в v1.1 стоял последовательно с D3)", flags=["tbd"])
P("D3", "SS14", "SMA", "C2480")
P("R3", "187k 1%", "0402", note="FB-делитель: 0.6*(1+187/10)=11.82 В")
P("R4", "10k 1%", "0402")
P("C6", "22uF 25V polymer/tantalum low-profile", "tbd", note="выход boost", flags=["tbd"])
P("C7", "100nF X7R 25V", "0603")
# ---------- Z3 драйвер соленоида ----------
P("Q1", "SI2302", "SOT-23-3", "C351399", "ключ соленоида (Vgs max 8 В)")
P("D2", "SS14", "SMA", "C2480", "flyback")
P("R7", "10k", "0402", note="fail-safe подтяжка GATE, менять запрещено")
# ---------- Z4 V1 (заморожен) ----------
P("U2", "TLC555IDR", "SOIC-8", "C6987")
P("R9", "100k", "0402", note="POR")
P("C8", "1uF X7R", "0402")
P("R6", "220", "0402")
P("R1", "1k", "0402", note="фильтр тракта срыва — топология предположительная (A1)", flags=["tbd"])
P("C3", "100nF", "0402", note="фильтр тракта срыва (A1)", flags=["tbd"])
P("R5", "10k", "0402", note="подтяжка контакта спуска")
P("R11", "1M", "0402")
P("R12", "220k", "0402", note="RT: 1.1*220k*100n=24.2 мс. ЗНАЧЕНИЕ ПРЕДПОЛОЖЕНО (A2)", flags=["tbd"])
P("C9", "100nF", "0402", note="CT (A2)", flags=["tbd"])
P("C5", "10nF", "0402", note="CONTROL, стандартная обвязка 555 (A3)", flags=["tbd"])
P("C23", "100nF", "0402", note="блокировочный VCC555, добавлен в v1.2")
# ---------- Z5 V2 always-on ----------
P("U5", "ATtiny1616-MNR", "QFN-20 3x3", "C507118")
P("C10", "1uF X7R", "0402")
P("C11", "100nF X7R", "0402")
P("R10", "1M", "0402", note="v1.2: 10k -> 1M (ограничение фантомного тока через клампы МК)")
P("R16", "220k", "0402", note="v1.2: bleeder V2PWR — не даёт V2PWR всплывать в положении I")
P("R13", "1M", "0402", note="ADC делитель")
P("R14", "1M", "0402", note="ADC делитель")
P("C12", "100nF", "0402", note="узел делителя, sample&hold")
P("R15", "220", "0402", note="R_MG")
P("R17", "100k", "0402", note="v1.2: pull-down узла SENSE (был 10k)")
P("R18", "10k", "0402", note="nRF TX -> МК RX")
P("R19", "10k", "0402", note="МК TX -> nRF RX")
P("SW1", "TACT 4x4", "SMD", note="MODE")
# ---------- ключ MATCH/TRAIN, Q3/Q4 ----------
P("Q3", "AO3401A", "SOT-23-3", "C15127", "P-МОП: Source=VCC_IN (12 В)")
P("Q4", "SI2302", "SOT-23-3", "C351399", "v1.2: N-МОП, драйвер затвора Q3; открывается только при V2PWR на ключе")
P("R20", "100k", "0402", note="R_UP: исток Q3 -> затвор")
P("R21", "47k", "0402", note="R_DN: затвор Q3 -> сток Q4. Vgs(Q3)=-12*100/147=-8.2 В")
# ---------- Z6 switched-домен ----------
P("U3", "AP63203WU-7 (3.3 В buck, Vin 3.8-32 В)", "TSOT-26", "", "v1.2: ЗАМЕНА ME6211C33 (Vin max 6.5 В < 12 В!). Пины/L/Cboot сверить с даташитом", flags=["tbd"])
P("L2", "10uH shielded Isat>=1.5A", "4x4", note="по даташиту U3", flags=["tbd"])
P("C13", "100nF X7R 25V", "0402", note="Cboot")
P("C14", "10uF X7R 25V", "0805", note="Cin buck")
P("C15", "22uF X5R 10V", "0805", note="Cout buck")
P("R22", "100k", "0402", note="EN U3 <- VIN (токоограничение)")
P("R23", "100k", "0402", note="v1.2: bleeder V3V3 — гарантирует ~0 В в MATCH при любых утечках UART")
P("U4", "ME6211C18M5G-N", "SOT-23-5", "C236671", "Vin 3.3 В — в пределах 6.5 В")
P("C16", "1uF X7R", "0402")
P("C17", "1uF X7R", "0402")
P("U6", "nRF52811-QCAA-R", "QFN-32 5x5", "C559461", "DEC/DCC обвязка — по референсу Nordic (TBD)", flags=["tbd"])
P("Y1", "NX1612SA-32MHZ", "1612-4P", "C910049", flags=["tbd"])
P("C21", "12pF", "0402", note="нагрузочный, по даташиту кристалла", flags=["tbd"])
P("C22", "12pF", "0402", note="нагрузочный, по даташиту кристалла", flags=["tbd"])
P("J1", "U.FL-R-SMT-1(10)", "SMD", "C88373", "проверить сборку JLC")
P("MATCH", "pi-match L/C/C (TBD)", "0402", note="по референсу Nordic", flags=["tbd"])

# ---------- площадки (в BOM не идут) ----------
PADS = {
 "P_BATP":"BAT_P","P_BATN":"GND",
 "P_SWA1":"VBAT_D","P_SWA2":"VBAT_SW",
 "P_SWB1":"VBAT_SW","P_SWB2":"VCC555",
 "P_SWC1":"VBAT_SW","P_SWC2":"V2PWR",
 "P_R6OUT":"R6_OUT","P_MG":"MG","P_GATE":"GATE",
 "P_SF1":"TSG","P_SF2":"VBAT_SW",
 "P_SOLA":"SOL_A","P_SOLB":"VCC_IN",
 "P_VCCIN":"VCC_IN",
 "P_S_V3V3":"V3V3","P_S_V1V8":"V1V8","P_S_GND":"GND",
 "P_SDA":"SDA","P_SCL":"SCL","P_HXSCK":"HX_SCK","P_HXDOUT":"HX_DOUT",
 "P_PPGINT":"PPG_INT","P_BMIINT":"BMI_INT","P_RSV":"RSV",
 "P_V_V3V3":"V3V3","P_V_GND":"GND","P_VIBEN":"VIBRO_EN",
 "P_UPDI":"UPDI","P_PV2PWR":"V2PWR","P_PGND1":"GND",
 "P_SWDIO":"SWDIO","P_SWDCLK":"SWDCLK","P_NRST":"NRST",
 "P_PV3V3":"V3V3_SENSE","P_PGND2":"GND",
 "P_KEYCOM":"V2PWR","P_KEYSENSE":"SENSE",
 "P_AT1":"AT_SPARE1","P_AT2":"AT_SPARE2","P_AT3":"AT_SPARE3",
 "P_AT4":"AT_SPARE4","P_AT5":"AT_SPARE5","P_AT6":"AT_SPARE6",
 "P_NRF1":"NRF_SPARE1","P_NRF2":"NRF_SPARE2","P_NRF3":"NRF_SPARE3","P_NRF4":"NRF_SPARE4",
 "P_XV2PWR":"V2PWR","P_XGND":"GND",
}
for ref in PADS:
    P(ref, "pad", "pad", flags=["pad"])

# ---------- пины микросхем ----------
IC_PINS = {
 "U1": ["SW","GND","FB","EN","IN","NC"],
 "U2": ["GND","TRIG","OUT","RESET","CONT","THRES","DISCH","VDD"],
 "U3": ["FB","EN","VIN","GND","SW","BST"],
 "U4": ["VIN","GND","CE","VOUT","NC"],
 "U5": ["VDD","GND","PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7",
        "PB0","PB1","PB2","PB3","PB4","PB5","PC0","PC1","PC2","PC3"],
 "U6": ["VDD","GND","XC1","XC2","ANT","SWDIO","SWDCLK","NRESET","UART_TX","UART_RX",
        "SDA","SCL","HX_SCK","HX_DOUT","PPG_INT","BMI_INT","VIBRO_EN","RSV",
        "SPARE1","SPARE2","SPARE3","SPARE4"],
 "Q1": ["G","S","D"], "Q3": ["G","S","D"], "Q4": ["G","S","D"],
 "Y1": ["1","2","3","4"], "J1": ["SIG","GND"],
 "D1": ["A","K"], "D2": ["A","K"], "D3": ["A","K"],
}
STRICT = {"U1","U2","U3","U4","U5","Q1","Q3","Q4","D1","D2","D3","Y1","J1"}  # все пины обязаны быть в цепях/NC
NC_PINS = {("U1","NC"),("U4","NC"),
           ("U5","PC0"),("U5","PC1"),("U5","PC2"),("U5","PC3")}  # PC0-3: свободны, прошивка = вход с подтяжкой

# ---------- цепи ----------
NETS = {
 "GND": ["C1.2","C2.2","C4.2","U1.GND","R4.2","C6.2","C7.2","Q1.S","R7.2","R5.2","C3.2",
         "C8.2","C5.2","C9.2","C23.2","U2.GND","C10.2","C11.2","U5.GND","R14.2","C12.2",
         "R17.2","Q4.S","SW1.2","C14.2","C15.2","U3.GND","R23.2","U4.GND","C16.2","C17.2",
         "U6.GND","Y1.2","Y1.4","C21.2","C22.2","J1.GND","R11.2"],
 "BAT_P": ["D1.A"],
 "VBAT_D": ["D1.K"],
 "VBAT_SW": ["C1.1","C2.1","C4.1","U1.IN","U1.EN","L1.1"],
 "SW": ["U1.SW","L1.2","D3.A"],
 "VCC_IN": ["D3.K","C6.1","C7.1","R3.1","Q3.S","R20.1","D2.K"],
 "FB": ["U1.FB","R3.2","R4.1"],
 "SOL_A": ["Q1.D","D2.A"],
 "GATE": ["Q1.G","R7.1"],
 "U2_OUT": ["U2.OUT","R6.1"], "R6_OUT": ["R6.2"],
 "VCC555": ["U2.VDD","R9.1","R12.1","R11.1","C23.1"],
 "TSG": ["R5.1","R1.1","R10.1"],
 "TRIG": ["R1.2","C3.1","U2.TRIG"],
 "U2_RESET": ["R9.2","C8.1","U2.RESET"],
 "U2_CONT": ["C5.1","U2.CONT"],
 "U2_TIMING": ["R12.2","C9.1","U2.THRES","U2.DISCH"],
 "TSG_MOD": ["R10.2","U5.PA6"],
 "V2PWR": ["U5.VDD","C10.1","C11.1","R13.1","R16.1"],
 "V2PWR_BLEED": [],  # R16.2 -> GND (см. ниже)
 "VBAT_ADC": ["R13.2","R14.1","C12.1","U5.PA2"],
 "MG_OUT": ["U5.PB0","R15.1"], "MG": ["R15.2"],
 "SENSE": ["R17.1","U5.PA7","Q4.G"],
 "G3": ["Q3.G","R20.2","R21.1"],
 "Q4D": ["R21.2","Q4.D"],
 "V12_SW": ["Q3.D","C14.1","U3.VIN","R22.1"],
 "U3_EN": ["R22.2","U3.EN"],
 "BUCK_SW": ["U3.SW","L2.1","C13.1"],
 "BUCK_BST": ["C13.2","U3.BST"],
 "V3V3": ["L2.2","U3.FB","C15.1","U4.VIN","U4.CE","C16.1","R23.1","U6.VDD"],
 "V1V8": ["U4.VOUT","C17.1"],
 "MODE": ["U5.PA4","SW1.1"],
 "UPDI": ["U5.PA0"],
 "UART_TX_AT": ["U5.PB2","R19.1"], "UART_RX_NRF": ["R19.2","U6.UART_RX"],
 "UART_TX_NRF": ["U6.UART_TX","R18.1"], "UART_RX_AT": ["R18.2","U5.PB3"],
 "AT_SPARE1": ["U5.PA1"], "AT_SPARE2": ["U5.PA3"], "AT_SPARE3": ["U5.PA5"],
 "AT_SPARE4": ["U5.PB1"], "AT_SPARE5": ["U5.PB4"], "AT_SPARE6": ["U5.PB5"],
 "SDA": ["U6.SDA"], "SCL": ["U6.SCL"], "HX_SCK": ["U6.HX_SCK"], "HX_DOUT": ["U6.HX_DOUT"],
 "PPG_INT": ["U6.PPG_INT"], "BMI_INT": ["U6.BMI_INT"], "RSV": ["U6.RSV"],
 "VIBRO_EN": ["U6.VIBRO_EN"],
 "SWDIO": ["U6.SWDIO"], "SWDCLK": ["U6.SWDCLK"], "NRST": ["U6.NRESET"],
 "NRF_SPARE1": ["U6.SPARE1"], "NRF_SPARE2": ["U6.SPARE2"],
 "NRF_SPARE3": ["U6.SPARE3"], "NRF_SPARE4": ["U6.SPARE4"],
 "XTAL1": ["U6.XC1","Y1.1","C21.1"], "XTAL2": ["U6.XC2","Y1.3","C22.1"],
 "ANT_RAW": ["U6.ANT","MATCH.1"], "ANT_J": ["MATCH.2","J1.SIG"],
}
# R16.2 (bleeder V2PWR) -> GND
NETS["GND"].append("R16.2")
del NETS["V2PWR_BLEED"]
# V3V3_SENSE — только контрольный вывод для программатора (не точка подачи питания)
NETS["V3V3"].append("P_PV3V3.1")
# площадки присоединяем к цепям
for pad, net in PADS.items():
    if net == "V3V3_SENSE":
        continue
    NETS.setdefault(net, []).append(f"{pad}.1")
NETS["BAT_P"].append("P_BATP.1") if "P_BATP.1" not in NETS["BAT_P"] else None

# ---------- напряжения ----------
NET_VMAX = {"BAT_P":3.2,"VBAT_D":3.2,"VBAT_SW":3.2,"VCC555":3.2,"V2PWR":3.2,
            "VCC_IN":12.0,"V12_SW":12.0,"SW":12.5,"V3V3":3.3,"V1V8":1.8,"Q4D":12.0,
            "GATE":3.2,"R6_OUT":3.2,"U2_OUT":3.2,"MG":3.2,"MG_OUT":3.2,"TSG":3.2,
            "TSG_MOD":3.2,"SENSE":3.2,"G3":12.0}
PIN_ABSMAX = {("U4","VIN"):6.5,("U4","CE"):6.5,("U4","VOUT"):6.5,
              ("U3","VIN"):32.0,("U3","SW"):32.0,("U1","SW"):28.0,
              ("U2","VDD"):15.0,("Q1","G"):8.0,("Q4","G"):8.0,("Q4","D"):20.0,
              ("Q3","S"):30.0,("Q3","D"):30.0,("U5","VDD"):5.5,("U6","VDD"):3.6,
              ("U5","PA6"):3.6,("U5","PA7"):5.5}
