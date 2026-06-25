# RAG 入门笔记

> 个人知识库测试文档，用于验证解析、语义分块、向量化和检索。

## 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种把**外部知识库**和**大语言模型**结合的技术。

基本流程分为两步：

1. **检索（Retrieval）**：根据用户问题，从知识库中找到最相关的文档片段。
2. **生成（Generation）**：把检索到的片段作为上下文，让 LLM 生成有依据的回答。

RAG 的核心优势是：模型不需要把所有知识都背进参数里，可以随时更新知识库，并且回答可以标注来源。

## Embedding 与向量库

Embedding 是把文本转换成一串数字（向量）的过程。语义相近的文本，向量在空间中距离更近。

本项目使用的 embedding 模型是 **BAAI/bge-small-zh-v1.5**，适合中文场景，可以在本地免费运行。

向量库（如 ChromaDB）负责存储：

- 每个 chunk 的向量
- chunk 的原文
- 元数据（笔记 ID、标题、块序号等）

搜索时，先把用户问题转成向量，再在向量库里找最相似的几个 chunk。

## 分块策略

长文档不能直接整篇 embedding，需要先切成较小的 chunk。

常见策略包括：

- **固定长度切分**：按字符数切，实现简单。
- **递归字符切分**：优先在段落、句号等边界切，避免把句子拦腰截断。
- **语义切分（SemanticChunker）**：计算相邻句子的 embedding 相似度，在话题切换处切分。

语义切分适合结构混乱、话题混杂的笔记，但切分阶段也需要调用 embedding 模型，成本更高。

## Docker 部署备忘

生产环境常用 Docker 容器化部署应用。

基本步骤：

```bash
docker build -t notes-kb .
docker run -p 8000:8000 notes-kb
```

多服务场景推荐使用 **docker compose**，一条命令启动 API、向量库挂载目录和数据库。

部署前注意检查：环境变量中的 API Key、ChromaDB 持久化目录、上传文件大小限制。

## 项目进度

- [x] 配置中心 config.py
- [x] 语义分块 chunker.py
- [x] 本地向量化 embedding_local.py
- [ ] 文件解析 parser.py
- [ ] 知识库入库 kb_manager.py
- [ ] 向量检索 retriever.py

下一步：读取本文件 → 分块 → embed → 写入 ChromaDB，然后用「什么是 RAG」这类问题做搜索测试。
