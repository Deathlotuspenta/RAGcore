# RAGcore 桌面应用打包

Mac `.app` 与 Windows 安装目录的构建、分发与使用说明。

## 架构

```
RAGcore.app (Mac) / RAGcore-win-x64 (Win)
├── launcher.py          # 启动器：启 uvicorn、开浏览器、显示状态窗口
├── python/              # 内置 Python + 依赖（用户无需安装）
├── backend/
│   ├── server/          # FastAPI 后端
│   └── models/          # BGE 模型（只读，随更新替换）
└── frontend/dist/       # 预构建前端

用户数据（外置，更新不丢失）
  Mac:     ~/Library/Application Support/RAGcore/
  Win:     %APPDATA%\RAGcore/
           ├── storage/   # SQLite + Chroma
           ├── .env       # API Key 等配置
           └── logs/      # 运行日志
```

双击图标 → 状态窗口弹出 → 后台 uvicorn（约 2–5 秒）→ 自动打开浏览器。关闭状态窗口即停止服务。

---

## 用户安装

无需安装 Python。详见 [用户安装说明.txt](用户安装说明.txt)（会随发布 zip 一并提供）。

| 平台 | 下载 | 操作 |
|------|------|------|
| Mac Apple 芯片 | `RAGcore-mac-arm64.zip` | 解压 → `.app` 拖入「应用程序」→ 双击 |
| Mac Intel | `RAGcore-mac-x64.zip` | 同上 |
| Windows x64 | `RAGcore-win-x64-setup.exe` 或绿色目录 | 安装 / 解压 → 双击 `RAGcore.vbs` |

1. 弹出 **RAGcore 状态窗口**（表示后台在运行）
2. 浏览器打开 http://127.0.0.1:8765
3. 注册登录 →「设置」填 DeepSeek API Key → 导入笔记 → 问答

首次导入或 RAG 问答会加载本地 BGE 模型（约 30 秒），网页本身数秒即可用。

---

## 维护者：构建发布包

### 前置条件

- Node.js（构建前端）
- Python 3.11+（仅构建机需要，用于创建内置 venv）
- `backend/models/bge-small-zh-v1.5` 已就位
- `backend/models/bge-reranker-base`（缺失时脚本自动下载）
- 联网（首次构建安装 torch 等依赖）
- 每个包约 **3–4 GB**

Mac Apple 芯片 / Intel / Windows **需分别在对应系统上各打一版**。

### Mac

```bash
bash packaging/mac/build-app.sh
```

产出（在 `dist/`）：

- `RAGcore-mac-arm64.app` 或 `RAGcore-mac-x64.app`（按本机架构）
- 同名 `.zip`（内含 `.app` + `安装说明.txt`）

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File packaging\win\build-win.ps1
```

产出：`dist\RAGcore-win-x64\`

可选安装包（需 [Inno Setup](https://jrsoftware.org/isinfo.php)）：

```powershell
iscc packaging\win\installer.iss
# → dist\RAGcore-win-x64-setup.exe
```

### 发布清单

| 产物 | 构建环境 |
|------|----------|
| `RAGcore-mac-arm64.zip` | Apple 芯片 Mac |
| `RAGcore-mac-x64.zip` | Intel Mac |
| `RAGcore-win-x64-setup.exe` | Windows 10/11 x64 |

---

## 目录说明

```
packaging/
├── README.md              # 本文件
├── 用户安装说明.txt        # 随 zip 发给最终用户
├── launcher.py            # Mac / Win 共用启动器
├── mac/
│   ├── build-app.sh       # Mac 构建脚本
│   ├── Info.plist
│   └── ragcore            # .app 入口 shell
└── win/
    ├── build-win.ps1
    ├── RAGcore.cmd
    ├── RAGcore.vbs
    └── installer.iss
```

---

## 常见问题

**双击没反应？**  
查看 `~/Library/Application Support/RAGcore/logs/ragcore.err.log`（Win 为 `%APPDATA%\RAGcore\logs\`）。

**Mac 提示无法验证开发者？**  
系统设置 → 隐私与安全性 → 仍要打开。

**8765 端口被占用？**

```bash
lsof -ti:8765 | xargs kill
```

**修改启动器后要不要重新打包？**  
本机测试可手动复制 `launcher.py` 到 `.app/Contents/Resources/`；发给别人必须重新 `build-app.sh`。

---

## 开发者本地调试

不打包，直接从源码跑：

```bash
cd backend && pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000

cd frontend && npm install && npm run dev
```

或使用 `scripts/start-mac.command` / `scripts/start-win.bat`（需先配置 `backend/.venv`）。

详见项目根目录 [README.md](../README.md)。
