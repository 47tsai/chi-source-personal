# Chi Source Personal

個人使用的 AltStore / SideStore Source，收錄自己感興趣的小眾 App、ACG、遊戲相關工具與 Tweaks。

## 專案狀態

目前已搬入 Chi Source 的基本更新器、來源驗證、測試與 GitHub Actions CI 架構。這是初始化骨架，尚未完成個人源的 App 清單、來源識別資訊與正式部署設定。

- **Source 尚未部署**，請勿將此專案加入 AltStore / SideStore。
- 自動更新流程暫時停用，避免沿用主源的 App 清單或來源網址。
- 主源：[`chi-source`](https://github.com/tsai97216/chi-source)

## 開發

```bash
pip install -r requirements.txt
python -m pytest -q
python -m py_compile update_source.py validate_source.py
```
