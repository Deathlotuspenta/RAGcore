# RAGcore Windows 打包教程

本文面向**维护者**：在 Windows 10/11 x64 上，将 RAGcore 打成可分发的绿色目录或安装包。最终用户无需安装 Python。

---

## 一、产物说明

| 产物 | 路径 | 用途 |
|------|------|------|
| 绿色版目录 | `dist\RAGcore-win-x64\` | 直接压缩为 zip 分发，用户解压后双击 `RAGcore.exe` |
| 安装包（可选） | `dist\RAGcore-win-x64-setup.exe` | Inno Setup 生成，带开始菜单与桌面快捷方式 |

绿色版目录结构：

```
dist/RAGcore-win-x64/
├── RAGcore.exe          # 用户入口（WinForms 状态面板）
├── launcher.py          # Mac 桌面包启动器（Windows 不使用）
├── 安装说明.txt          # 随包发给用户
├── python/              # 内置 Python 3.11 embed + 全部依赖
├── backend/
│   ├── server/          # FastAPI 后端
│   ├── models/          # BGE 嵌入与重排序模型
│   ├── .env.example
│   └── requirements-lock.txt
└── frontend/dist/       # 预构建前端静态资源
```

用户数据保存在 `%APPDATA%\RAGcore\`（更新或重装应用不会删除）。

---

## 二、环境准备

### 2.1 构建机要求

- **操作系统**：Windows 10/11，64 位（必须在 Windows 上构建，不能交叉编译）
- **磁盘空间**：至少 **8 GB** 可用（构建临时文件 + 约 3–4 GB 产物）
- **网络**：首次构建需下载 Python embed、pip 依赖（含 PyTorch），耗时约 **10–20 分钟**

### 2.2 必装软件

| 软件 | 用途 | 获取方式 |
|------|------|----------|
| Node.js 18+ | 构建前端 `npm run build` | https://nodejs.org/ |
| Git Bash 或 WSL | 缺失 reranker 时执行 `download_reranker.sh` | 随 Git for Windows 安装 |
| Inno Setup 6（可选） | 生成 `setup.exe` | https://jrsoftware.org/isinfo.php |

验证：

```powershell
node -v
npm -v
```

### 2.3 模型文件

构建前需确保嵌入模型已就位：

```
backend/models/bge-small-zh-v1.5/config.json   # 必须存在
backend/models/bge-reranker-base/              # 缺失时脚本自动下载
```

若缺少 `bge-small-zh-v1.5`，在项目根目录执行：

```powershell
pip install -U huggingface_hub
hf download BAAI/bge-small-zh-v1.5 --local-dir backend\models\bge-small-zh-v1.5
```

> 新版 Hugging Face CLI 使用 `hf download`（`huggingface-cli` 已废弃）。未登录时下载较慢，进度在动即正常，约 90MB 需耐心等待。

重排序模型缺失时，`build-win.ps1` 会调用：

```bash
bash backend/scripts/download_reranker.sh
```

需已安装 Git Bash，且 `bash` 在 PATH 中。

---

## 三、一键构建（绿色版）

在项目根目录打开 **PowerShell**，执行：

```powershell
powershell -ExecutionPolicy Bypass -File packaging\win\build-win.ps1
```

### 脚本做了什么

1. **构建前端**：`frontend` 下执行 `npm ci` / `npm install` 与 `npm run build`
2. **校验模型**：检查 BGE 模型；必要时下载 reranker
3. **下载 Python embed**：官方 `python-3.11.9-embed-amd64.zip`，启用 `site-packages`
4. **安装依赖**：通过 `get-pip.py` 安装 pip，再安装 `backend/requirements-lock.txt`
5. **组装目录**：复制 python、backend、frontend/dist，并编译 `RAGcore.exe` 到 `dist\RAGcore-win-x64\`

成功后会输出目录路径与大致体积（约 3–4 GB）。

### 本地试跑

```text
双击  dist\RAGcore-win-x64\RAGcore.exe
```

预期行为：

1. 弹出「RAGcore」状态窗口
2. 浏览器自动打开 http://127.0.0.1:8765
3. 关闭状态窗口即停止后台服务

日志位置：`%APPDATA%\RAGcore\logs\ragcore.err.log`

---

## 四、生成安装包（可选）

### 4.1 安装 Inno Setup

安装 [Inno Setup 6](https://jrsoftware.org/isinfo.php)，并将安装目录下的 `ISCC.exe` 加入 PATH，或使用完整路径调用。

### 4.2 编译

**先完成第三节的绿色版构建**，再执行：

```powershell
iscc packaging\win\installer.iss
```

产出：`dist\RAGcore-win-x64-setup.exe`

### 4.3 自定义安装包

编辑 `packaging\win\installer.iss`：

| 项 | 说明 |
|----|------|
| `MyAppVersion` | 版本号 |
| `AppId` | 应用唯一 GUID，大版本升级时一般保持不变 |
| `OutputBaseFilename` | 输出文件名 |
| `[Tasks]` / `[Icons]` | 桌面快捷方式等 |

安装后默认入口为 `RAGcore.exe`，工作目录为安装目录。

---

## 五、发布清单

向用户分发时建议包含：

| 文件 | 说明 |
|------|------|
| `RAGcore-win-x64-setup.exe` | 安装版（推荐不熟悉解压的用户） |
| 或 `RAGcore-win-x64.zip` | 绿色版（将整个 `dist\RAGcore-win-x64` 目录打 zip） |
| `packaging\用户安装说明.txt` | 已自动复制为包内 `安装说明.txt` |

**注意**：Mac 包需在 macOS 上单独构建，Windows 包不能替代。

---

## 六、相关文件说明

```
packaging/win/
├── README.md           # 本教程
├── build-win.ps1       # 主构建脚本
├── build-launcher.ps1  # 编译 RAGcore.exe
├── RagcoreApp.cs       # Windows 桌面启动器源码
└── installer.iss       # Inno Setup 安装脚本

packaging/
├── launcher.py         # Mac 桌面包启动器
└── 用户安装说明.txt     # 最终用户说明
```

### 启动链路

```
RAGcore.exe（WinForms 状态面板）
  → 后台启动 python\python.exe -m uvicorn
  → 健康检查通过后自动打开浏览器
  → 关闭窗口即停止服务
```

> Windows 内置 Python（embed）不含 tkinter，因此由原生 `RAGcore.exe` 提供状态面板，不再让用户双击 `.vbs` / `.cmd`。

修改 `RagcoreApp.cs` 后，需重新执行 `build-win.ps1`（或单独运行 `build-launcher.ps1`）才能体现在发布包中。

---

## 七、常见问题

### 构建失败：`frontend/dist 构建失败`

- 确认已安装 Node.js，且在 `frontend` 目录能手动执行 `npm run build`
- 查看 npm 报错，多为依赖或 TypeScript 编译问题

### 构建失败：`缺少 backend\models\bge-small-zh-v1.5`

- 按第二节下载并放置嵌入模型后再构建

### 构建失败：`bash` 找不到或 reranker 下载失败

- 安装 [Git for Windows](https://git-scm.com/download/win)
- 或手动下载 `bge-reranker-base` 到 `backend\models\bge-reranker-base\`

### 构建很慢或 pip 超时

- 首次安装 torch 等大包属正常，请保持网络畅通
- 可配置 pip 镜像（在脚本执行前设置环境变量或使用 pip.conf）

### 构建失败：`uvloop does not support Windows`

- `uvloop` 只支持类 Unix 系统，不支持 Windows
- `build-win.ps1` 会从 `requirements-lock.txt` 临时过滤 `uvloop` 后再安装依赖
- 若仍遇到该错误，请确认正在使用最新的 `packaging\win\build-win.ps1`

### 双击 `RAGcore.exe` 无反应或闪退

1. 查看 `%APPDATA%\RAGcore\logs\ragcore.err.log`
2. 确认 `python\python.exe` 与 `backend\server` 存在于安装目录
3. 若仅更新了启动器，可单独重编译：`powershell -ExecutionPolicy Bypass -File packaging\win\build-launcher.ps1 -OutExe dist\RAGcore-win-x64\RAGcore.exe`

### 端口 8765 被占用

```powershell
netstat -ano | findstr :8765
taskkill /PID <pid> /F
```

### 杀毒软件误报

内置 Python 与大量 .dll 可能触发启发式扫描。可对构建输出目录加白名单，或对安装包做代码签名（需自备证书）。

### 修改代码后如何验证

- **不打包**：用 `scripts\start-win.bat` 从源码启动（需 `backend\.venv`）
- **测启动器**：改 `packaging\launcher.py` 后复制到 `dist\RAGcore-win-x64\` 快速验证
- **正式发布**：必须重新运行 `build-win.ps1`

---

## 八、与 Mac 打包的关系

| 平台 | 脚本 | 产出 |
|------|------|------|
| Windows | `packaging\win\build-win.ps1` | `dist\RAGcore-win-x64\` |
| Mac | `packaging/mac/build-app.sh` | `dist/RAGcore-mac-*.app` |

共用 `packaging/launcher.py` 与用户数据外置策略；构建流程与产物格式不同，需分别在对应系统上执行。

更多跨平台说明见 [packaging/README.md](../README.md)。
