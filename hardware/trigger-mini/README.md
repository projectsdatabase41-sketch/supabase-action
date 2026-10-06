# Плата «Мини» v1.2 (24×50 мм)

- `design.py` — компоненты и цепи (единственный источник правды)
- `check.py` — ERC, лимиты напряжений, модель логики положений 0/I/II × ключ
- `build.py` — генерирует `out/bom.csv`, `out/netlist.json`, `out/nets.md`
- `CHANGES_v1.2.md` — что исправлено относительно v1.1 и что открыто

Запуск: `python3 build.py && python3 check.py`
