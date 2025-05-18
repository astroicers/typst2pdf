// 滲透測試報告：範例模版
#set page(
  width: 21cm,
  height: 29.7cm,
  margin: (top: 2cm, bottom: 2cm, left: 3cm, right: 2.5cm),
  numbering: "1"
)

#show heading.where(level: 1): it => block(
  above: 1em,
  below: 0.8em,
  spacing: 0.5em
)[
  #set text(size: 14pt, weight: "bold")
  #it.body
]

#show heading.where(level: 2): it => block(
  above: 0.8em,
  below: 0.5em
)[
  #set text(size: 12pt, weight: "bold")
  #it.body
]

= 滲透測試報告

專案名稱：ACME Web Security Assessment \
測試期間：2025 年 3 月 10 日 至 2025 年 3 月 14 日 \
提交日期：2025 年 3 月 18 日 \
測試單位：CyberTest 安全實驗室

== 1. 簡介

本報告詳述針對 ACME 公司 Web 應用所進行的滲透測試過程與發現，目的在於識別並評估潛在資訊安全弱點，並提供改善建議以降低風險。

== 2. 測試範圍

- Web 應用主機：https://acme.test/
- 已授權測試帳號：#link("mailto:testuser@example.com")[`testuser@example.com`]

== 3. 測試方法

本次測試採用 *灰箱測試（Gray-box Testing）* 策略，並依據以下測試準則：

+ OWASP Top 10 (2021)
+ CWE/SANS Top 25
+ NIST SP 800-115

== 4. 測試結果摘要

#table(
  columns: 4,
  table.header(
    [編號], [弱點名稱], [風險等級], [狀態]
  ),
  ["VUL-001"], ["SQL Injection"], ["高"], ["未修補"],
  ["VUL-002"], ["敏感資料外洩"], ["中"], ["已修補"],
  ["VUL-003"], ["弱密碼政策"], ["低"], ["未修補"],
)

== 5. 弱點詳述

=== VUL-001 SQL Injection

- 描述： 可透過 login 請求注入惡意 SQL 指令。
- 位置： `/login` POST 請求中的 `username` 欄位。
- 證據：
  ```http
  POST /login HTTP/1.1
  Host: acme.test
  ...
  username=' OR 1=1 --
  ```
- 影響： 可繞過身份驗證，存取任意帳號。
- 建議修補方式： 實作參數化查詢，避免字串拼接查詢語句。

== 6. 結論與建議

測試顯示目標系統存在若干嚴重漏洞，建議盡速修補，並持續進行安全監測與教育訓練。

#quote(block: true, attribution: [*CyberTest 安全實驗室*])[
  資訊安全不是一次性的測試，而是持續性的承諾。
]
