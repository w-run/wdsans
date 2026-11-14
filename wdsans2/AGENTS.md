# AGENTS.md — w-box 工作区约定

本文件供 AI Agent 在本机（w-box）操作 `/workspace` 时遵守。

---

## 1. 磁盘分工（核心规则）

本机有两块盘，**用途严格区分**：

| 盘 | 挂载点 | 类型 | 容量 | 可用 | 用途 |
|---|---|---|---|---|---|
| SSD（KINGSTON SA400，SATA） | `/` | xfs | 69G | ~43G | **代码、服务、工具链** |
| HDD（ST3500418AS，2009 年） | `/data` | ext4 | 458G | ~434G | **可重建的大体积产物** |

**判断依据不是“哪个大”，而是“丢了会怎样”：**

- 丢了要重写 / 服务会挂 → 放 `/`（SSD）
- 丢了能重新生成 / 不影响服务 → 放 `/data`（HDD）

### 为什么不能把所有东西都搬到 /data

实测数据（本机）：

| 项目 | SSD | HDD |
|---|---|---|
| 顺序读 | — | 128 MB/s |
| 冷读 5000 个小文件 | **0.222s** | **0.325s**（慢 46%） |

`/data` 是老机械盘，**随机访问小文件明显更慢**，且属于**单点故障源**（SMART 数据有重置痕迹、固件 CC34 属希捷固件门批次）。因此凡是“代码”和“服务运行路径”，一律不放 `/data`。

---

## 2. 允许、应当指向 /data 的内容

以下属于**可重建产物**，高占用，应放到 `/data`：

| 类型 | 典型目录 | 建议位置 |
|---|---|---|
| Rust 构建产物 | `target/` | `/data/build-cache/<项目名>-target/` |
| Node 依赖 | `node_modules/` | `/data/build-cache/<项目名>-node_modules/` |
| 打包输出 | `dist/`、`build/`、`out/` | `/data/build-cache/<项目名>-dist/` |
| 容器镜像缓存 | — | `/data/cache/` |
| 临时同步 / 中间数据 | — | `/data/scratch/` |
| 大数据集、参考源码 | — | `/data/meuos/reference/` 等既有目录 |

**统一放在 `/data/build-cache/` 下，按项目名建子目录。**

---

## 3. 禁止放到 /data 的内容

**绝对不要把以下内容指向 `/data`：**

| 内容 | 原因 |
|---|---|
| 任何 git 工作区 / 源码 | 掉盘会导致代码丢失、git 操作失败 |
| `.nvm/versions/`（node 本体） | `box-webroot`、`easyrouter` 等**生产服务**运行时依赖它 |
| `.rustup/toolchains/`（编译器） | 掉盘后所有 Rust 构建直接失败 |
| `.cargo/bin/` | 在 PATH 中，是 rustup 代理入口，移走会断链 |
| `/workspace/static/` | 公网 web root（`box.w-run.net`），服务依赖 |
| 任何 systemd 服务 ExecStart/WorkingDirectory 指向的路径 | 掉盘即服务中断 |

> 判断口径：**路径是否出现在 `/etc/systemd/system/*.service` 里，或是否在 `$PATH` 中。** 是则留 SSD。

---

## 4. 如何正确重定向构建产物

### ✅ 推荐：`CARGO_TARGET_DIR` 或项目内 `.cargo/config.toml`

```bash
# 方式 A：环境变量（临时/脚本内）
CARGO_TARGET_DIR=/data/build-cache/<项目名>-target cargo build

# 方式 B：项目内持久化（推荐，写进项目后 agent 后续自动生效）
mkdir -p .cargo
printf '[build]\ntarget-dir = "/data/build-cache/<项目名>-target"\n' > .cargo/config.toml
```

### ❌ 不要用软链接指 target

**实测结论（本机验证）：`cargo clean` 会删掉 `target` 软链接本身**，之后构建**静默回落到本地盘**，占满根分区且无任何报错：

```
$ cargo clean
$ ls -ld target      # 软链接已消失
$ cargo build        # 产物静默写回本地盘 → 根分区被占满
```

`CARGO_TARGET_DIR` 和 `.cargo/config.toml` 不存在此问题：`clean` 后路径依然有效，产物始终落在指定位置。

### Node 项目

`pnpm` / `npm` **没有**官方的 `node_modules` 位置重定向。推荐做法：把 **store**（真正的包实体、最占空间的部分）放到 `/data`，`node_modules` 本体留在项目内用硬链接复用——既省空间，又不影响工具链解析。

**可靠方式（本机验证）：在项目根目录写 `.npmrc`**

```bash
printf 'store-dir=/data/cache/pnpm-store\n' >> .npmrc
pnpm config get store-dir     # 应输出 /data/cache/pnpm-store
```

> ⚠️ 不要用 `pnpm config set store-dir ... --global`：本机全局 bin 目录 `/root/.local/share/pnpm/bin` 不在 `PATH` 中，该命令会直接报错。

---

## 5. 空间占用检查（操作前必做）

创建大数据目录前，先确认目标盘余量：

```bash
df -h / /data
du -sh --exclude=target --exclude=node_modules /workspace/*   # 真实代码体积
```

**当前水位参考**：`/` 26G/69G（38%），`/data` 25G/458G（6%）。

若发现 `/` 使用率超过 **70%**，应先排查高占用来源：

```bash
du -x -sh /* 2>/dev/null | sort -rh | head -10
du -sh /tmp/* 2>/dev/null | sort -rh | head -10
```

---

## 6. 清理前的强制检查

**删除任何目录前，必须按顺序确认：**

1. **是否已被 git 记录？**
   ```bash
   git -C <path> status --porcelain        # 有输出 = 有未提交改动，禁止直接删
   git -C <path> log --oneline @{u}..      # 有输出 = 有未推送提交
   ```

2. **是否是无远端的本地仓？**
   ```bash
   git -C <path> remote get-url origin     # 报错 = 无远端，删了无法恢复
   ```

3. **是否为可重新获取的第三方内容？**
   第三方源码（有 `.git` 且有远端）、官方 tarball、包缓存 → 可删，记住来源即可。

4. **删除超过 1G 的内容，先归档再删：**
   ```bash
   tar czf /data/archive/<名称>-$(date +%Y%m%d).tar.gz -C <父目录> <目录>
   gzip -t /data/archive/<名称>-*.tar.gz && echo OK   # 校验通过再删
   ```

---

## 7. 本机已知的历史坑（避免重复踩）

| 坑 | 教训 |
|---|---|
| U 盘做数据盘 | 之前 `/data` 是 aigo U330，**会掉盘**，曾专门写过 udev + timer 自动重挂脚本。现已换内置 SATA 盘，相关机制已停用并归档在 `/root/archive-udisk-automount/` |
| 软链接指 target | `cargo clean` 会删软链接 → 静默回落本地盘（见 §4） |
| 孤儿 git 工作树 | `/data/meuos/worktrees` 曾有 128 个目录，`.git` 指向的目标早已不存在，白占 12G。已归档清理。**用 `git worktree list` 核实，不要凭目录名猜** |
| 打包时误含密钥 | 曾把 `/root/.ssh` 下 7 个私钥打进备份包上传云盘。**打包必须显式排除 `id_*`、`ssh_*`、`*.pem`、`*.key`、`credentials*`** |
| 备份放在同一块盘 | 归档文件不要只留在 `/data`，那块盘坏了会一起丢。重要归档应上传云盘（`aliyunpan upload <file> /w-box`） |

---

## 8. 服务清单（改动路径前必读）

以下服务**开机自启且正在运行**，路径硬编码在 unit 文件里，**不要移动它们指向的目录**：

| 服务 | 路径 |
|---|---|
| `box-webroot` | `/workspace/static`（公网 web root） |
| `tui-dash` | `/workspace/tui-dash` |
| `esimd` / `smsd` | `/workspace/sms/esimd` |
| `ml307-atport` / `ml307r-netlock` | `/workspace/sms/bin` |

改动前先查：

```bash
grep -rl "/workspace\|/data" /etc/systemd/system/*.service
systemctl is-enabled <服务名>    # 确认是否自启
```

改动后必须验证：

```bash
systemctl --failed --no-legend    # 应为空
```

---

## 9. 备份出口

云盘已登录（13.77TB，已用 3.39TB），CLI 为 `aliyunpan`：

```bash
aliyunpan ls /w-box                        # 查看已有备份
aliyunpan upload <本地文件> /w-box          # 上传
```

**大文件上传务必脱离 SSH 会话**，否则连接中断会导致上传失败：

```bash
setsid nohup aliyunpan upload <文件> /w-box > /tmp/up.log 2>&1 < /dev/null &
```

---

## 10. 磁盘健康检查

```bash
smartctl -d sat -H -A /dev/sdb      # 机械盘健康
smartctl -d sat -A /dev/sda         # 系统 SSD（SSD_Life_Left、Reallocated_Event_Count）
```

**关注指标**：`Reallocated_Sector_Ct`、`Current_Pending_Sector`、`Offline_Uncorrectable`、`UDMA_CRC_Error_Count` 应恒为 0；任一非 0 或增长需警惕。

⚠️ `/dev/sdb` 的 SMART `Power_On_Hours` 曾被重置（与 `Head_Flying_Hours`、`Total_LBAs_Read` 数值矛盾），**不能据此判断盘的新旧**，只能靠故障计数判断健康度。

---

## 附：快速决策表

新产生一个目录/文件时，问自己：

```
是代码或 git 仓库吗？          → 是 → /（SSD）
是服务运行依赖的路径吗？        → 是 → /（SSD）
能靠一条命令重新生成吗？        → 是 → /data（HDD）
体积 > 500MB 吗？              → 是 → /data（HDD）
以上都不确定                  → 留 /（SSD），并记录到此处
```
