<p align="center">
  <a href="https://github.com/Spenhouet/confluence-markdown-exporter"><img src="https://raw.githubusercontent.com/Spenhouet/confluence-markdown-exporter/b8caaba935eea7e7017b887c86a740cb7bf99708/logo.png" alt="confluence-markdown-exporter"></a>
</p>
<p align="center">
  <em>Confluence 页面导出为 Markdown 的团队定制版使用说明。</em>
</p>

## README 怎么看

这个仓库的 README 重点回答四件事：

1. 日常导出时应该执行什么命令
2. 首次安装时应该怎么装
3. 团队当前推荐的默认配置与使用约束是什么
4. 出现常见报错时应该先检查什么

如果你只是想把 Confluence 内容导出到本地 Markdown，优先看本文的「日常使用」与「导出命令」。

本文已经内置了安装、认证、JSON 配置和推荐 `export` 片段，不需要依赖额外文档才能完成 setup。

外部 skill 文档仍可作为 Agent 场景下的补充参考，但 README 本身应该保证普通读者单独阅读也能完成配置。

## 适用场景

工具命令：`confluence-markdown-exporter`，简写 `cf-export`。

常见用途：

- 导出单页
- 导出页面及全部子页面
- 导出整个 Space
- 导出全部 Space
- 将 Wiki 内容同步到本地 Markdown 目录

如果你的目标是“本地 Markdown 再发布回 Wiki”，那不是本文场景，应该看 `doc-to-wiki` 相关流程。

## 日常使用

### 日常流程

推荐按下面的顺序执行：

1. 先确认导出目标：`page id`、页面 URL、或 `SPACE_KEY`
2. 从下表选择对应子命令直接导出
3. 如果失败，再按本文的「常见问题排查」判断是安装问题、认证问题还是参数问题

> [!TIP]
> 日常使用默认假定环境已经安装完成，且认证与导出配置已经准备好。

> [!IMPORTANT]
> 使用 Cursor 等 Agent 工具时，不要在 sandbox 模式中执行本工具。sandbox 模式下可能读不到已配置文件，进而出现“未登录”或配置缺失类报错。

### 导出命令

在已配置默认输出目录，或显式传入 `--output-path` 的前提下：

| 场景 | 命令 |
|------|------|
| 单页 | `confluence-markdown-exporter pages <page-id或url> --output-path ./out` |
| 页面及全部子页 | `confluence-markdown-exporter pages-with-descendants <page-id或url> --output-path ./out` |
| 单个 Space | `confluence-markdown-exporter spaces <SPACE_KEY> --output-path ./out` |
| 全部 Space | `confluence-markdown-exporter all-spaces --output-path ./out` |

示例：

```sh
cf-export pages 645208921 --output-path ./out
cf-export pages-with-descendants "https://company.atlassian.net/wiki/spaces/AAA/pages/645208921/demo" --output-path ./out
cf-export spaces LIBRA --output-path ./out
```

如需进一步确认参数：

```sh
cf-export --help
cf-export pages --help
cf-export pages-with-descendants --help
```

### 日常排错分流

先判断问题类型，再决定该检查哪一段配置：

| 现象 | 下一步 |
|------|--------|
| 命令不存在、import 失败、Python 依赖错误 | 看下文「环境要求」和「安装方式」 |
| 401/403、首次配置、需要改认证或 JSON | 看下文「一次性配置」 |
| 不确定该用哪个子命令 | 回到上面的导出命令表，或执行 `--help` |
| 缺少 page id / url / space key | 先补齐导出目标，再执行命令 |

## 安装与一次性配置

### 原则

- 本团队使用 **fork 版本**，不要把 PyPI 官方包当成唯一来源
- 日常导出成功后，不要反复打开安装文档

推荐安装源：

```sh
pip install "git+https://github.com/JaysonAlbert/confluence-markdown-exporter.git"
```

不要使用下面这种方式作为唯一安装或升级手段，否则容易切回 PyPI 官方包：

```sh
pip install confluence-markdown-exporter
pip install confluence-markdown-exporter --upgrade
```

### 环境要求

- Python `3.10+`
- 已安装 `pip`
- 已安装 `git`

### 安装方式

任选其一，推荐使用虚拟环境：

```sh
python3 -m venv .venv
source .venv/bin/activate

# 方式 A：直接从团队 fork 安装
pip install "git+https://github.com/JaysonAlbert/confluence-markdown-exporter.git"

# 方式 B：克隆后本地可编辑安装
git clone https://github.com/JaysonAlbert/confluence-markdown-exporter.git
cd confluence-markdown-exporter
pip install -e .
```

升级建议：

- 如果是 Git 安装，直接按同一 Git 源重新安装
- 如果是本地克隆，先 `git pull`，再执行 `pip install -e .`

### 验证安装

```sh
confluence-markdown-exporter --help
cf-export --help
```

### 团队环境约束

当前团队默认约束如下：

- Python 版本以仓库 `pyproject.toml` 为准，当前要求 `3.10+`
- Confluence 实例为 **Server 7.4.5**
- 认证方式使用 **用户名 + 密码**
- 交互文案里显示的 `API Token`，在当前 Server 场景下实际填写的是登录密码
- `connection_config.use_v2_api` 必须为 `false`

### 一次性配置

#### 认证字段怎么填

执行 `confluence-markdown-exporter config` 时，界面里的三项按下面理解：

| 提示项 | 含义 |
|--------|------|
| `Instance URL` | Confluence 根地址，保留尾部 `/` |
| `Username (email)` | 登录名或邮箱 |
| `API Token` | 在当前 Server 7.4.5 场景下填写登录密码 |

对应 JSON 键为：

- `auth.confluence.url`
- `auth.confluence.username`
- `auth.confluence.api_token`

#### 配置文件位置

- macOS 默认位置：`~/Library/Application Support/confluence-markdown-exporter/app_data.json`
- 如果需要自定义位置，可设置：

```sh
export CME_CONFIG_PATH=/path/to/custom_config.json
```

安全注意：

- 配置文件里包含密码，不要提交到 Git
- 不要在聊天、日志或文档里回显真实密码

#### Agent 配置约束

- 如果由 Agent 协助配置，优先直接编辑 JSON 文件
- 不要让 Agent 代操作交互式 TUI 菜单
- 如果文件已存在，只改必要键，保留用户已有路径和非目标配置

#### 连接配置

- `connection_config.use_v2_api` 必须设为 `false`
- 内网 HTTP 或自签证书场景下，再按需调整 `verify_ssl`

### 推荐配置

如果你要配置导出布局，优先使用下面这组团队推荐值：

```json
{
  "export": {
    "output_path": "../your-export-dir",
    "page_href": "relative",
    "page_path": "{space_name}/{homepage_title}/{ancestor_titles}/{page_title}-{page_id}.md",
    "attachment_href": "relative",
    "attachment_path": "{page_parent_path}/{page_title}/{attachment_file_id}{attachment_extension}",
    "include_document_title": true,
    "include_yaml_frontmatter": true
  }
}
```

#### 首次配置时需要的信息

如果是第一次配置，至少需要准备：

1. `Instance URL`
2. `Username (email)`
3. 登录密码，写入 `auth.confluence.api_token`
4. 可选的 `output_path`

### 常见问题排查

| 现象 | 处理 |
|------|------|
| 401/403 | 核对 URL、用户名、密码是否正确写入 `auth.confluence.api_token`，并确认账号有权限 |
| 404 / API 不匹配 | 确认 `connection_config.use_v2_api` 为 `false` |
| 附件路径异常 | 检查 `export.attachment_path` 是否使用了团队推荐格式 |
| 命令找不到 | 重新确认虚拟环境是否已激活，或重新执行安装命令 |

## 输出结构

导出后的目录通常类似：

```sh
output_path/
└── MYSPACE/
   ├── MYSPACE.md
   └── MYSPACE/
      ├── My Confluence Page.md
      └── My Confluence Page/
         ├── My nested Confluence Page.md
         └── Another one.md
```

实际路径结构受 `export.page_path` 与 `export.attachment_path` 配置影响。

## 功能概览

这个工具支持：

- Confluence 页面导出为 Markdown
- 单页、子树、单 Space、全站导出
- 标题、段落、列表、表格、链接、图片、代码块等常见元素转换
- 宏、任务列表、告警块、frontmatter 等增强能力
- 图片与附件链接处理
- 默认跳过未变化页面，仅增量重导
- draw.io、PlantUML、Markdown Extensions 等常见插件内容支持

### 支持的 Markdown 元素

- Headings
- Paragraphs
- Lists
- Tables
- Bold / italic / underline
- Links
- Images
- Code blocks
- Tasks
- Alerts
- Front matter
- Mermaid
- PlantUML

## 配置项速查

大多数日常导出不需要手动修改配置；只有在需要调整输出结构、链接形式、frontmatter 或连接参数时，再查看此表。

| Key                                   | Description                                                                                                           | Default                                                             |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| export.output_path                    | The directory where all exported files and folders will be written. Used as the base for relative and absolute links. | ./ (current working directory)                                      |
| export.parallel_downloads             | Number of parallel workers for downloading and exporting pages.                                                       | 5                                                                   |
| export.page_href                      | How to generate links to pages in Markdown. Options: `relative` or `absolute`.                                       | relative                                                            |
| export.page_path                      | Path template for exported pages.                                                                                     | `{space_name}/{homepage_title}/{ancestor_titles}/{page_title}.md`   |
| export.attachment_href                | How to generate links to attachments in Markdown. Options: `relative` or `absolute`.                                 | relative                                                            |
| export.attachment_path                | Path template for attachments.                                                                                        | `{space_name}/attachments/{attachment_file_id}{attachment_extension}` |
| export.page_breadcrumbs               | Whether to include breadcrumb links at the top of the page.                                                           | True                                                                |
| export.filename_encoding              | Character mapping for filename encoding.                                                                              | Default mappings for forbidden characters.                          |
| export.filename_length                | Maximum length of filenames.                                                                                          | 255                                                                 |
| export.include_document_title         | Whether to include the document title in the exported markdown file.                                                  | True                                                                |
| export.include_yaml_frontmatter       | Prepend YAML frontmatter with page metadata.                                                                          | False                                                               |
| export.skip_unchanged                 | Skip exporting pages that have not changed since last export.                                                         | True                                                                |
| export.cleanup_stale                  | Delete local files for removed or relocated pages after export.                                                       | True                                                                |
| export.lockfile_name                  | Name of the lock file used to track exported pages.                                                                   | `confluence-lock.json`                                              |
| export.existence_check_batch_size     | Number of page IDs per batch when checking page existence during cleanup.                                             | 250                                                                 |
| connection_config.backoff_and_retry   | Enable automatic retry with exponential backoff.                                                                      | True                                                                |
| connection_config.backoff_factor      | Multiplier for exponential backoff.                                                                                   | 2                                                                   |
| connection_config.max_backoff_seconds | Maximum seconds to wait between retries.                                                                              | 60                                                                  |
| connection_config.max_backoff_retries | Maximum number of retry attempts.                                                                                     | 5                                                                   |
| connection_config.retry_status_codes  | HTTP status codes that trigger a retry.                                                                               | `[413, 429, 502, 503, 504]`                                         |
| connection_config.verify_ssl          | Whether to verify SSL certificates for HTTPS requests.                                                                | True                                                                |
| connection_config.use_v2_api          | Enable Confluence REST API v2 endpoints.                                                                              | False                                                               |
| auth.confluence.url                   | Confluence instance URL.                                                                                              | `""`                                                                |
| auth.confluence.username              | Confluence username/email.                                                                                            | `""`                                                                |
| auth.confluence.api_token             | Confluence API token, or the team server password in current Server usage.                                            | `""`                                                                |
| auth.confluence.pat                   | Confluence Personal Access Token.                                                                                     | `""`                                                                |
| auth.jira.url                         | Jira instance URL.                                                                                                    | `""`                                                                |
| auth.jira.username                    | Jira username/email.                                                                                                  | `""`                                                                |
| auth.jira.api_token                   | Jira API token.                                                                                                       | `""`                                                                |
| auth.jira.pat                         | Jira Personal Access Token.                                                                                           | `""`                                                                |

### 目标系统适配

如果你要为特定 Markdown 平台优化输出，可参考下面的方向：

#### Obsidian

- 建议关闭 `export.include_document_title`
- 如不需要冗余导航，可关闭 `export.page_breadcrumbs`

#### Azure DevOps Wiki

- `export.attachment_href` 使用 `absolute`
- 根据 ADO 约束调整 `export.attachment_path`
- 需要时收紧 `export.filename_encoding` 与 `export.filename_length`

## Repository Scripts

仓库内 `scripts/` 目录还包含一组维护脚本，主要服务于 Gliffy 相关的补导与修复流程，不属于日常 CLI 主路径。

### Gliffy Maintenance Workflow

这组脚本主要解决三类问题：

- 找出已经导出的 Markdown 中仍缺少 Gliffy 本地产物的页面
- 把真正的 Gliffy 页面和普通 PNG 截图区分开
- 只重导受影响页面，而不是整站重导

推荐顺序：

1. 扫描本地导出目录，生成候选页面列表
2. 用线上 Confluence 元数据校验候选列表
3. 仅重导校验通过的页面

### 1. Scan exported Markdown for affected pages

使用 `scripts/scan_gliffy_affected_pages.py` 扫描现有导出目录，找出看起来不完整的页面。

它当前会在以下情况下标记页面：

- 页面包含 Gliffy 源附件，但缺少导出的本地预览图
- 页面仍引用远端 `/download/attachments/...png`，且未找到本地 Gliffy 导出
- 页面包含 Gliffy 源附件，但导出 Markdown 没有引用完整

示例：

```sh
python3 scripts/scan_gliffy_affected_pages.py ./libra-confluence --output /tmp/gliffy-affected-pages.json
```

输出：

- 写入 `--output` 指定的 JSON 汇总文件
- `affected_page_count`
- `pages[]`，其中包含 `page_id`、title、markdown path、attachment directory 与命中原因

### 2. Verify which candidates are real Gliffy pages

使用 `scripts/verify_gliffy_candidates.py` 进一步减少误报。脚本会从 Confluence 读取页面内容，校验它是否真的包含 Gliffy 相关元数据或标记。

典型检查包括：

- attachment comments 中含 `GLIFFY`
- 页面 body 中含 `gliffy-container`
- export view 中存在 Gliffy 标记

示例：

```sh
uv run python scripts/verify_gliffy_candidates.py /tmp/gliffy-affected-pages.json --output /tmp/gliffy-verified-pages.json
```

输出：

- `verified_pages[]`
- `rejected_pages[]`
- requested、verified、rejected 的汇总统计

### 3. Re-export only affected pages

使用 `scripts/reexport_gliffy_affected_pages.py` 将受影响页面批量重导回既有导出目录。

适用场景：

- Gliffy 支持补上后，需要修复旧导出结果
- 只需修复部分页面
- 希望得到可恢复、逐页的重导结果

示例：

```sh
uv run python scripts/reexport_gliffy_affected_pages.py /tmp/gliffy-verified-pages.json --output-root ./libra-confluence
```

常用参数：

- `--limit N`：先对前 `N` 页做 smoke test
- 输入既可以是原始扫描结果，也可以是校验后的结果

输出：

- stdout 中的 JSON 汇总
- 每页 success / failure 明细
- `requested_count`、`exported_count`、`failed_count`

### Example end-to-end flow

```sh
python3 scripts/scan_gliffy_affected_pages.py ./libra-confluence --output /tmp/gliffy-affected-pages.json
uv run python scripts/verify_gliffy_candidates.py /tmp/gliffy-affected-pages.json --output /tmp/gliffy-verified-pages.json
uv run python scripts/reexport_gliffy_affected_pages.py /tmp/gliffy-verified-pages.json --output-root ./libra-confluence
```

### Notes

- 这些脚本是仓库维护辅助工具，不属于发布后的 CLI 接口
- `verify_gliffy_candidates.py` 与 `reexport_gliffy_affected_pages.py` 需要有效的 Confluence 凭据
- 扫描脚本可以先基于本地导出文件与 lockfile 运行

## Known Issues

1. 部分 Confluence Server 版本或配置下，附件 file ID 可能缺失。默认附件路径依赖该字段，必要时请改用 `{attachment_id}` 或 `{attachment_title}`。参考：https://github.com/Spenhouet/confluence-markdown-exporter/issues/39
2. 如果 Confluence Server 位于代理或 VPN 后，可能出现连接问题。参考：https://github.com/Spenhouet/confluence-markdown-exporter/issues/38

## Contributing

如需参与贡献，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

本工具基于 [MIT License](LICENSE) 开源发布。
