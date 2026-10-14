# Chi Source Personal

AltStore / SideStore Source。

## Source

```text
https://raw.githubusercontent.com/tsai97216/chi-source-personal/main/apps.json
```

<!-- AUTO-UPDATE-APPS:START -->
## Apps 更新狀態

- **最近自動檢查：** 尚未檢查
- **最近內容更新：** 尚未更新

| App | 原倉庫 | 狀態 | 最新版本 | 版本日期 | 上次更新 |
| --- | --- | --- | --- | --- | --- |
| **[SpooferPro Pokemon GO](https://github.com/SpooferPro)** | SpooferPro | Pending | 0.431.1 | 2026-10-12 | 2026-10-12 |
| **[Animeko](https://github.com/maxchang3/ani-altstore-source)** | openani | Pending | 6.3.0 | 2026-10-13 | 2026-10-13 |
| **[Kazumi](https://github.com/ChouChiu/Kazumi-AltStore-Source)** | Predidit | Pending | 2.3.8 | 2026-10-07 | 2026-10-07 |
| **[Aidoku](https://github.com/Aidoku/Aidoku)** | Skitty | Pending | 0.9 | 2026-09-03 | 2026-09-03 |

<!-- AUTO-UPDATE-APPS:END -->

<!-- AUTO-UPDATE-STATUS-TIMES:START -->
<!-- {} -->
<!-- AUTO-UPDATE-STATUS-TIMES:END -->

## 開發

```bash
pip install -r requirements.txt
python -m pytest -q
python update_source.py
python update_source.py --app Animeko
python validate_source.py
```
