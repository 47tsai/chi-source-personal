# Chi Source Personal

個人興趣向的 AltStore / SideStore Source，收錄 ACG、小眾 App 與自己想保留的工具。

## Source

```text
https://raw.githubusercontent.com/tsai97216/chi-source-personal/main/apps.json
```

## 上游來源

本專案會定期同步以下公開 AltStore Source，並合併成單一的 `apps.json`：

- SpooferPro
- OpenAni / Animeko
- Kazumi
- Aidoku

同步時會保留上游版本、下載網址與 App 權限資訊；遇到重複的 Bundle ID 時，依 `sources.json` 的順序保留第一個來源。任一上游來源無法取得或資料格式不正確時，同步會失敗，不會以不完整資料覆蓋現有清單。

## 開發

```bash
pip install -r requirements.txt
python -m pytest -q
python update_source.py
python validate_source.py
```

GitHub Actions 會在主分支更新、每六小時排程及手動觸發時同步來源。
