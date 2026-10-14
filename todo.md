# Chi Source Personal TODO

## Source 整合
- [x] 加入 SpooferPro、OpenAni / Animeko、Kazumi、Aidoku 四個上游來源
- [x] 建立通用來源合併器，保留版本與權限 metadata
- [x] 正規化不同來源的 screenshots 格式
- [x] 以 Bundle ID 去重，避免 AltStore Source 出現重複 App
- [x] 加入來源同步與 AltStore schema 驗證測試
- [x] 設定 GitHub Actions 定期同步及手動觸發
- [ ] 首次同步完成後確認 Actions 與產生的 apps.json
- [ ] 後續再決定是否補上 Personal 專用圖示
