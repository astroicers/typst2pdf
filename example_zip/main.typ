#let today = "2025 年 05 月 18 日"

#set page(margin: 2.5cm)
#set text(font: "Noto Sans CJK TC", size: 11pt, lang: "zh")
#set heading(level: 1)
#set heading(level: 2)

= 安全掃描報告

撰寫日期：#today

== 一、摘要

本報告根據 OWASP ZAP 的自動化掃描結果整理而成。

== 二、掃描結果

#table(
  columns: 4,
  [
    [*漏洞名稱*], [*風險等級*], [*URL*], [*修補建議*],
    ["跨站腳本攻擊（XSS）"], ["高"], ["https://example.com/search"], ["請對使用者輸入進行編碼。"]
  ]
)
