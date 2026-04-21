# 坑合集

按报告撰写流程的位置分类。每个坑格式：**触发条件 / 表现 / 解决 / 原因**。写新报告遇到新坑就加到这里。

## OOXML / docx 打包

### `<w:pPr>` 子元素顺序错导致 validation 失败
- **触发**：手写 pPr 时把 `<w:shd>` 放到 `<w:ind>` 之后
- **表现**：`pack.py` 报 `Element '...shd': This element is not expected. Expected is one of (...)`
- **解决**：按 schema 顺序重排。常用片段的正确顺序：
  ```
  pStyle → keepNext → keepLines → numPr → pBdr → shd → tabs →
  autoSpaceDE → autoSpaceDN → adjustRightInd → snapToGrid →
  spacing → ind → contextualSpacing → jc → textAlignment → rPr
  ```
- **原因**：OOXML schema 对 pPr 子元素强制排序，不像 HTML 可随意排布

### WPS 模板带 broken reference 导致 pack 失败
- **触发**：模板是 WPS 保存的，含某些绝对路径 `settings.xml.rels`
- **表现**：`CRITICAL: These errors will cause the document to appear corrupt. Broken references MUST be fixed`
- **解决**：`pack.py --validate false`，Word/LibreOffice 仍能正常打开
- **原因**：WPS 在 rels 里存了 Windows 本地 `C:\...` 路径，非 WPS 环境找不到也无实际影响

### 同 rId 被多个 drawing 引用时跨块正则误替换
- **触发**：用正则 `<wp:extent ...>[\s\S]*?r:embed="rId205"[\s\S]*?<a:ext ...>` 替换尺寸
- **表现**：rId205 的 a:ext 改了，但前一个 drawing（如 rId204）的 wp:extent 被误改
- **解决**：先用 `<w:drawing>...</w:drawing>` 整块提取，在块内改 cx/cy
  ```python
  drawing_pat = re.compile(r'<w:drawing>[\s\S]*?</w:drawing>')
  xml = drawing_pat.sub(lambda m: replace_inside_block(m.group(0)), xml)
  ```
- **原因**：非贪婪 `*?` 仍会跨过相邻 drawing 到目标 rId，捕获组包含了错误的起点

### 图片 cx/cy 要同步两处
- **触发**：只改了 `<wp:extent>` 忘了改 `<a:ext>`
- **表现**：Word 里图显示尺寸不对、或出现拉伸
- **解决**：同一 drawing 内的两处 cx/cy 必须相同。用正则 `cx="\d+" cy="\d+"` 全替
- **原因**：wp:extent 决定行内布局尺寸，a:ext 在 spPr 里决定图形实际尺寸

### Content Types 缺 png/jpg
- **触发**：新手动建 docx，`[Content_Types].xml` 里没声明图片类型
- **表现**：Word 打开提示文件损坏
- **解决**：确保里面有 `<Default Extension="png" ContentType="image/png"/>` 等
- **原因**：zip 内所有文件都要在 Content_Types 里有条目（Default extension 或 Override）

## 工具链版本

### protoc 和 protobuf-java 版本不匹配
- **触发**：系统 protoc 34.x 但 pom.xml 里 protobuf-java 4.29.x
- **表现**：Java 编译报 `cannot find symbol method getMessageType(int)` 等 API 不存在错误
- **解决**：protobuf-java 升到和 protoc **对齐或更新**的版本（libprotoc 34.x → protobuf-java 4.34.x）
- **原因**：protoc 生成的代码调用了新版运行库 API，老运行库没实现

### JDK 17 移除了 javax.annotation
- **触发**：用 Thrift 或老代码生成器，JDK 版本 ≥ 9
- **表现**：编译报 `package javax.annotation does not exist`
- **解决**：pom.xml 加依赖
  ```xml
  <dependency>
    <groupId>javax.annotation</groupId>
    <artifactId>javax.annotation-api</artifactId>
    <version>1.3.2</version>
  </dependency>
  ```
- **原因**：JDK 9 的模块化把 `javax.annotation` 从标准库移出到独立 artifact

### silicon 不认某些语言别名
- **触发**：`silicon --language protobuf` / `--language thrift` / `--language text`
- **表现**：`[error] Unsupported language: ...`
- **解决**：用 silicon 认识的名字
  | 语言 | silicon 用名 |
  |---|---|
  | Protocol Buffers | `proto`（不是 protobuf） |
  | Apache Thrift | 无原生支持，用 `cpp`（语法相近） |
  | 纯文本/目录树/ASCII 图 | 用 `ini`（不是 text/txt/plain） |
- **原因**：silicon 的语言表是 syntect 的 `.sublime-syntax` 子集

### silicon 默认字体不支持中文
- **触发**：代码注释含中文
- **表现**：大量 `[warning] No font found for character '中'`，渲染出来是方块
- **解决**：`--font "Maple Mono NF CN"` 或其它带 CJK 的等宽字体
- **原因**：silicon 只用主字体，不做 fallback

## 自动化 / 子进程

### alacritty 命令跑完立刻关窗来不及截图
- **触发**：`alacritty -e cmd` 跑完 cmd 就退出
- **表现**：niri screenshot-window 报「窗口不存在」
- **解决**：`alacritty -e bash -c "$cmd; sleep 999"`，外部截图后再 `kill $apid`
- **原因**：`-e` 是 exec 语义，程序退出窗口关闭

### Python stdout 块缓冲让后台进程日志丢失
- **触发**：`python script.py > log 2>&1 &` + 后面 `kill`
- **表现**：log 文件是空的或截断
- **解决**：启动加 `-u`：`python -u script.py > log 2>&1 &`
- **原因**：Python stdout 检测到非 TTY 后用块缓冲，kill 时缓冲未 flush

### 后台启动多进程 wait 阻塞
- **触发**：`bash -c "A & B & wait"` 传信号
- **表现**：`kill` 主 shell 没传给子进程，wait 永不返回
- **解决**：手动记 pid 并 `kill $PID`，必要时 `pkill -9 -f <pattern>` 兜底
- **原因**：shell 默认不把 signal forward 到子进程组

## Caption / 排版

### caption "并排"描述与实际"上下堆叠"不符
- **触发**：把两张图放同一 `<w:p>` 但合起来宽度超页，Word 自动换行成上下堆叠
- **表现**：caption 写「左：X 右：Y」但实际 X 在上 Y 在下
- **解决**：每图独立 `<w:p>`（禁止并排），各自独立 caption
- **原因**：Word 对 `<w:r>` 行内图的处理取决于可用宽度

### 图片按统一 cx 导致字号参差
- **触发**：所有图按 `cx = MAX_CX` 拉到页宽
- **表现**：短代码图字被放大 2 倍，长代码图正常；整份文档字号不一致
- **解决**：按像素密度 `cx = w_px × EMU_PER_PX`，超宽才截断
- **原因**：EMU 是绝对物理单位，同样的 cx 下像素数少 = 每像素占更大物理空间 = 字看起来更大
