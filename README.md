# Chi Source Personal

AltStore / SideStore Source。

## Source

```text
https://ipap.chi.qzz.io
```

<!-- AUTO-UPDATE-APPS:START -->
## Apps 更新狀態

- **最近自動檢查：** 2026-10-15 11:39:51（UTC+8）
- **最近內容更新：** 2026-10-15 07:45:26（UTC+8）

| App | 原倉庫 | 狀態 | 最新版本 | 版本日期 | 上次更新 |
| --- | --- | --- | --- | --- | --- |
| **[SpooferPro Pokemon GO](https://spooferpro.com)** | SpooferPro | **Updated** | 0.433.0 | 2026-10-14 | **2026-10-15** |
| **[Animeko](https://github.com/maxchang3/ani-altstore-source)** | openani | Unchanged | 6.3.0 | 2026-10-13 | 2026-10-13 |
| **[Kazumi](https://github.com/ChouChiu/Kazumi-AltStore-Source)** | Predidit | **Updated** | 2.3.9 | 2026-10-14 | **2026-10-15** |
| **[Aidoku](https://github.com/Aidoku/Aidoku)** | Skitty | Unchanged | 0.9 | 2026-09-03 | 2026-09-03 |
| **[Photos Backup](https://github.com/g8row/PhotosBackup)** | g8row | **Updated** | 0.3.7 | 2026-09-20 | **2026-10-14** |
| **[AirCard-iOS](https://github.com/Mak5er/AirCard-iOS)** | Mak5er | **Updated** | 1.3.2 | 2026-10-04 | **2026-10-14** |
| **[EnsWilde](https://github.com/YangJiiii/EnsWilde)** | YangJiiii | **Updated** | 3.1.3 | 2026-02-25 | **2026-10-14** |
| **[StikDebug](https://github.com/StephenDev0/StikDebug)** | StephenDev0 | **Updated** | 3.1.14 | 2026-10-12 | **2026-10-14** |

<!-- AUTO-UPDATE-APPS:END -->

<!-- AUTO-UPDATE-STATUS-TIMES:START -->
<!-- {"AirCard-iOS": "2026-10-14 20:03:50", "EnsWilde": "2026-10-14 20:03:50", "Kazumi": "2026-10-15 04:30:15", "Photos Backup": "2026-10-14 20:03:50", "SpooferPro Pokemon GO": "2026-10-15 07:45:26", "StikDebug": "2026-10-14 20:03:50"} -->
<!-- AUTO-UPDATE-STATUS-TIMES:END -->

## 開發

```bash
pip install -r requirements.txt
python -m pytest -q
python update_source.py
python update_source.py --app Animeko
python validate_source.py
```
