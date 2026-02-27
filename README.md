# CampusPulse
这是一款基于web框架的课堂实时评论管理程序
# Campus Pulse（Flask 原型）

一个轻量级的**基于课程的课堂互动**原型：

- 学生加入课程并发布**评论/问题**（可选择匿名）

- 讲师**查看**评论并**解答**问题，并可选择添加备注

- 学生动态**自动刷新**（每 3 秒轮询一次）

## 1) 运行（Windows / macOS / Linux）

> 仅使用：`Flask==2.3.3` + 内置的 `sqlite3`（无需额外数据库配置）。

### 选项 A：直接运行（推荐）

```bash

python app.py

```

然后打开：

- http://127.0.0.1:5000/

### 选项 B：（如果需要安装依赖项）

```bash

pip install -r requirements.txt

python app.py

```

## 2) 讲师密码

讲师默认密码为 `admin`。

您可以通过设置环境变量来更改它：

- Windows（PowerShell）：

```powershell

$env:CAMPUS_PULSE_ADMIN_PASSWORD="yourPassword" python app.py

```

- macOS/Linux：

```bash

CAMPUS_PULSE_ADMIN_PASSWORD="yourPassword" python app.py

```

## 3) 演示流程

1. 学生加入 **CS101**（预先创建的演示课程）→ 提交评论

2. 讲师登录 → 打开 **CS101** → 用备注解决评论

3. 学生在实时信息流中看到状态更新

## 4) 数据存储位置

SQLite 数据库文件自动创建在：

- `instance/campus_pulse.db`

## 5) 手动测试清单（用于您的课程作业证明）

- **US1 提交评论**：提交后，评论将显示在实时信息流中信息流

- **US2 查看确认**：提交后显示成功消息

- **US3 查看评论**：教师可以打开课程并查看所有评论

- **US4 解决评论**：教师将评论标记为已解决；学生可以看到状态

---

专为课程原型设计，不适用于生产环境安全。
# Campus Pulse (Flask prototype)

A lightweight **course-based classroom interaction** prototype:
- Students join a course and post **comments/questions** (optionally anonymous)
- Lecturers **view** comments and **resolve** them with an optional note
- Student feed **auto-refreshes** (polling every 3 seconds)

## 1) Run (Windows / macOS / Linux)

> Uses only: `Flask==2.3.3` + built-in `sqlite3` (no extra DB setup).

### Option A: Run directly (recommended)
```bash
python app.py
```

Then open:
- http://127.0.0.1:5000/

### Option B: (If you need to install deps)
```bash
pip install -r requirements.txt
python app.py
```

## 2) Lecturer password
Default lecturer password is `admin`.

You can change it by setting an environment variable:
- Windows (PowerShell):
```powershell
$env:CAMPUS_PULSE_ADMIN_PASSWORD="yourPassword"
python app.py
```
- macOS/Linux:
```bash
CAMPUS_PULSE_ADMIN_PASSWORD="yourPassword" python app.py
```

## 3) Demo flow
1. Student joins **CS101** (pre-created demo course) → submits a comment
2. Lecturer logs in → opens **CS101** → resolves the comment with a note
3. Student sees status update in the live feed

## 4) Where data is stored
SQLite DB file is created automatically at:
- `instance/campus_pulse.db`

## 5) Manual test checklist (for your coursework evidence)
- **US1 Submit comment**: after submit, the comment appears in the live feed
- **US2 View confirmation**: a success message is shown after submission
- **US3 View comments**: lecturer can open a course and view all comments
- **US4 Resolve comment**: lecturer marks a comment as resolved; student sees status

---
Built for coursework prototyping, not production security.
