# Hanggent Comic - AI Agent 漫剧生成平台

<div align="center">

<img src="./doc/logo.png" width="200" alt="Hanggent Comic Logo" />

**基于多智能体协作的漫剧创作平台，让创意变成现实**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178c6.svg)](https://www.typescriptlang.org/)

### ⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！


</div>

---

## 📖 项目简介

Hanggent Comic 是一个基于 AI Agent 的智能漫剧生成平台，通过多智能体协作流程，将用户的创意故事自动转化为完整的视频作品。每个 Agent 专注于特定任务（剧本创作、角色设计、分镜绘制、视频生成等），协同完成从创意到成品的全流程。

### ✨ 核心特性

- 🤖 **多智能体协作** - 8 个专业 AI Agent 分工协作完成创作流程
- 🎬 **智能剧本创作** - Director 和 Scriptwriter Agent 自动生成角色、场景和分镜脚本
- 🎨 **角色形象生成** - Character Artist Agent 基于描述生成一致性角色图像
- 🖼️ **分镜图生成** - Storyboard Artist Agent 为每个镜头生成精美的分镜首帧
- 🎥 **视频自动生成** - Video Generator Agent 支持文生视频和图生视频两种模式
- 🔄 **实时反馈系统** - WebSocket 实时推送各 Agent 的生成进度
- 🎯 **精准重生成** - Review Agent 处理用户反馈，支持对单个内容进行重新生成

---

## 📋 更新日志

### 2026.02.03

- ✨ **无限画布** - 将项目画布替换为 tldraw 无限画布，支持自由拖动、缩放各个卡片（剧本、角色、分镜、视频）
- ⚙️ **配置管理** - 新增前端环境变量配置界面，支持在线修改数据库、LLM、图像、视频服务配置

---

## 🎯 应用场景

![首页](./doc/screenshot_20260203_203942.png)

### 创作流程

1. **创建项目** - 输入故事创意、风格偏好
2. **AI 生成** - 多智能体协作生成完整内容
3. **实时预览** - 查看角色、分镜和视频生成进度
4. **精细调整** - 对不满意的内容进行重新生成
5. **导出作品** - 获取完整的视频作品

![无限画布](./doc/screenshot_20260203_203917.png)

![配置管理](./doc/screenshot_20260203_203930.png)

---

## 🏗️ 技术架构

### 后端技术栈

- **框架**: FastAPI + SQLModel
- **数据库**: PostgreSQL (异步 asyncpg)
- **缓存**: Redis (用于跨进程信号共享)
- **AI 服务**:
  - Claude Agent SDK (剧本创作)
  - OpenAI 兼容接口 (图像生成)
  - 豆包视频服务 / OpenAI 兼容接口 (视频生成)
- **实时通信**: WebSocket
- **图像处理**: Pillow

### 前端技术栈

- **框架**: React 18 + TypeScript
- **路由**: React Router v7
- **状态管理**: Zustand
- **数据请求**: TanStack Query
- **样式**: Tailwind CSS + DaisyUI
- **构建工具**: Vite
- **测试**: Vitest + Playwright

### 多智能体协作流程

```
用户输入
    ↓
OnboardingAgent (需求分析)
    ↓
DirectorAgent (导演规划)
    ↓
ScriptwriterAgent (剧本创作)
    ↓
CharacterArtistAgent (角色图生成)
    ↓
StoryboardArtistAgent (分镜图生成)
    ↓
VideoGeneratorAgent (视频生成)
    ↓
VideoMergerAgent (视频拼接)
    ↓
ReviewAgent (用户反馈处理)
```

---

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

**适合快速体验和生产部署**

> 💡 **默认使用 GitHub 预构建镜像**，无需本地构建，启动更快！

1. **配置环境变量**

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填写必要的 API 密钥
```

**必须配置的项目：**
- `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` - LLM 服务
- `IMAGE_API_KEY` - 图像生成服务
- `VIDEO_PROVIDER` - 视频服务提供商（openai 或 doubao）
- `DOUBAO_API_KEY` - 豆包视频服务密钥（如果选择 doubao）

**⚠️ Docker 部署特别注意：**

如果图像/视频服务运行在宿主机上，需要修改服务地址：

```env
# ❌ 错误：容器内 localhost 指向容器自己
IMAGE_BASE_URL=http://localhost:8000

# ✅ 正确：使用 host.docker.internal 访问宿主机
IMAGE_BASE_URL=http://host.docker.internal:8000

# ✅ 或使用宿主机实际 IP
IMAGE_BASE_URL=http://192.168.1.100:8000

# ✅ 或使用在线服务（推荐）
IMAGE_BASE_URL=https://api.modelscope.cn
```

**如果图像/视频服务也在 Docker 中：**

1. 修改 `docker-compose.yml`，让后端加入图像服务的网络：

```yaml
services:
  backend:
    networks:
      - default
      - your_image_service_network  # 图像服务的网络名

networks:
  your_image_service_network:
    external: true
```

2. 在 `docker-compose.yml` 的 `environment` 中配置服务地址：

```yaml
environment:
  IMAGE_BASE_URL: http://your_container_name:port
  VIDEO_BASE_URL: http://your_container_name:port
```

**注意：** `DATABASE_URL` 和 `REDIS_URL` 会被 Docker Compose 自动配置，无需手动修改。

2. **启动服务**

```bash
# 使用 GitHub 预构建镜像（推荐）
docker-compose up -d

# 或者本地构建镜像（适合开发调试）
docker-compose -f docker-compose.dev.yml up -d
```

3. **访问应用**

- 前端界面：http://localhost:15173
- API 文档：http://localhost:18765/docs

**常见操作：**

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 修改配置后重启
docker-compose restart backend

# 更新到最新镜像
docker-compose pull
docker-compose up -d

# 停止服务
docker-compose down
```

---

### 方式二：本地开发部署

**适合开发调试**

#### 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **PostgreSQL**: 14+
- **Redis**: 6+
- **FFmpeg**: 4.0+ (用于视频拼接和处理)

#### 后端部署

1. **克隆项目**

```bash
git clone https://github.com/Xeron2000/openOii.git
cd openOii/backend
```

2. **安装依赖**

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

3. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

**关键配置项：**

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/openoii

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM 服务 (Claude Agent SDK)
ANTHROPIC_BASE_URL=https://your-proxy.example.com
ANTHROPIC_AUTH_TOKEN=your_proxy_token

# 图像生成服务
IMAGE_BASE_URL=https://api.openai.com/v1
IMAGE_API_KEY=your_image_api_key

# 视频服务提供商 (选择 openai 或 doubao)
VIDEO_PROVIDER=doubao

# 豆包视频服务 (如果选择 doubao)
DOUBAO_API_KEY=your_doubao_api_key
```

4. **启动服务**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 18765
```

#### 前端部署

1. **进入前端目录**

```bash
cd ../frontend
```

2. **安装依赖**

```bash
pnpm install
```

3. **配置环境**

```bash
# 修改 vite.config.ts 中的后端地址（如需要）
```

4. **启动开发服务器**

```bash
pnpm dev
```

5. **访问应用**

打开浏览器访问 `http://localhost:15173`

---

## 🔧 API 文档

启动后端服务后，访问以下地址查看完整 API 文档：

- **Swagger UI**: `http://localhost:18765/docs`
- **ReDoc**: `http://localhost:18765/redoc`

---

## 🧪 测试

### 后端测试

```bash
cd backend
pytest                    # 运行所有测试
pytest --cov             # 生成覆盖率报告
```

### 前端测试

```bash
cd frontend
pnpm test                # 单元测试
pnpm test:ui             # 测试 UI
pnpm test:coverage       # 覆盖率报告
pnpm e2e                 # E2E 测试
```

---

## 🎨 生成模式说明

### 图像生成模式

#### 文生图 (Text-to-Image)

纯文本描述生成分镜图，适合快速原型。

```env
ENABLE_IMAGE_TO_IMAGE=false
```

#### 图生图 (Image-to-Image)

使用角色图作为参考生成分镜首帧，提升人物一致性。

```env
ENABLE_IMAGE_TO_IMAGE=true
```

**注意：** 图生图模式需要图像服务支持 Image-to-Image 功能。魔搭目前没有图生图模型，人物一致性会稍差。

### 视频生成模式

#### 文生视频 (Text-to-Video)

纯文本描述生成视频，适合快速原型。

```env
ENABLE_IMAGE_TO_VIDEO=false
```

#### 图生视频 (Image-to-Video)

使用角色图和分镜图作为参考，提升人物一致性。

```env
ENABLE_IMAGE_TO_VIDEO=true
VIDEO_IMAGE_MODE=reference  # 或 first_frame
```

**模式说明：**
- `first_frame`: 仅使用分镜首帧作为参考
- `reference`: 拼接角色图和分镜图作为参考（推荐）

---

## 🔌 支持的 AI 服务

### LLM 服务

- **Anthropic Claude** (直连或中转)
- **智谱 GLM** (通过 Anthropic 兼容接口)

### 图像生成

- 任何 OpenAI 兼容的图像生成接口
- **魔搭** (推荐，国内可用,只是没有图生图的模型人物一致性会差一点) - [https://modelscope.cn](https://modelscope.cn)

### 视频生成

- **豆包视频服务** (火山引擎 Ark API) - 推荐
- 任何 OpenAI 兼容的视频生成接口

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 开发规范

### 代码风格

- **后端**: 使用 Ruff 进行代码格式化和检查
- **前端**: 遵循 TypeScript 严格模式

### 提交规范

遵循 Conventional Commits 规范：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具链相关
```

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [React](https://react.dev/) - 用户界面库
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python) - AI 智能体开发
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的 CSS 框架
- [DaisyUI](https://daisyui.com/) - Tailwind CSS 组件库
- [Linux.do](https://linux.do/) - 强烈推荐！高质量技术社区，感谢佬友们的公益站和热心支持 ❤️

---

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 📝 提交 [Issue](https://github.com/Xeron2000/openOii/issues)
- 💬 [Telegram](https://t.me/xeron23)
- 📧 [Email](mailto:xeron2333@gmail.com)

---

<div align="center">

**用 AI 创造无限可能 🚀**

Made with ❤️ by Hanggent Comic Team

</div>
