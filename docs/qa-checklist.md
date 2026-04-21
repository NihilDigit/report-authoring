# 阶段 5 · QA 清单

不过完这份清单**不要**把 docx 交给用户。

## 自动检查

### 生成 PDF 预览
```bash
soffice --headless --convert-to pdf output.docx --outdir /tmp
pdftoppm -jpeg -r 100 /tmp/output.pdf /tmp/preview
```

### 扫残留占位符
```bash
python -m markitdown output.docx | grep -iE "{{IMG|TODO|XXX|此处|占位|lorem"
```
任何输出都是问题，必须清理。

### 检查图片关系完整
```bash
# 确保 document.xml 里引用的每个 rId 都在 rels 里有定义
python ${SKILL_DIR}/scripts/check_rels.py output.docx   # 未实现时用 unpack 手查
```

## 人工检查（清单）

### 内容
- [ ] 标题、学号、姓名、教师等固定字段正确
- [ ] 每个章节正文完整，没漏节
- [ ] 表格里的文字没有错位（python-docx 有时会吃掉表格 cell 边界）
- [ ] 代码运行日志中的时间戳、数值与上下文文字一致

### 图片
- [ ] 每张图居中
- [ ] Caption 编号连续（图 2-1、2-2…，没跳号）
- [ ] Caption 描述准确（不与图无关）
- [ ] 没有残留「（此处插入…截图）」的占位文字
- [ ] 代码图字号统一（pom.xml 那种短图没被拉大）
- [ ] 图没跨页撕裂（特别是大图）
- [ ] 没有图片堆叠导致的文字漏掉

### 排版
- [ ] 正文字号统一（五号）
- [ ] 行距统一（1.5 倍）
- [ ] 首行缩进一致
- [ ] 英文与中文衔接处空格习惯一致
- [ ] 脚注 / 参考文献 / 页眉页脚（如果模板有）

### 兼容性
- [ ] 在 LibreOffice / WPS / Word 打开都不炸（至少 LibreOffice 能渲染）
- [ ] 打印预览能正常分页
- [ ] 字体嵌入（中文宋体、Consolas）实际显示正确

## HITL 收尾

即使清单全过，**让用户亲自打开 docx 再过一遍**。Agent 不能代替最终审阅。
