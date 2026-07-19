"""
每日知识故事邮件发送系统
通过 GitHub Actions 每天定时运行，根据星期几调用 DeepSeek API 生成不同学科的故事。
"""
import os
import sys
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================
# 星期 ↔ 学科映射
# ============================================================
WEEKDAY_SUBJECT = {
    0: ("周一", "经济学"),
    1: ("周二", "心理学"),
    2: ("周三", "物理学"),
    3: ("周四", "生物学"),
    4: ("周五", "历史学"),
    5: ("周六", "数学"),
    6: ("周日", "文学"),
}

# ============================================================
# 各学科知识领域（每次随机选一个，确保多样性）
# ============================================================
SUBJECT_TOPICS = {
    "经济学": [
        "纳什均衡与博弈论", "科斯定理与交易成本", "蒙代尔不可能三角",
        "期权定价的Black-Scholes模型", "有效市场假说", "比较优势理论",
        "索洛增长模型", "明斯基金融不稳定假说", "阿罗不可能定理",
        "信息不对称与柠檬市场", "李嘉图等价", "IS-LM模型",
        "边际效用革命", "帕累托最优", "赫克歇尔-俄林模型",
    ],
    "心理学": [
        "认知失调理论", "斯坦福监狱实验与情境力量", "习得性无助",
        "米尔格拉姆服从实验", "峰终定律", "双加工理论",
        "依恋理论", "拖延的心理学机制", "达克效应",
        "心流理论", "锚定效应", "前景理论",
        "自我决定理论", "刻板印象威胁", "镜像神经元与共情",
    ],
    "物理学": [
        "麦克斯韦方程组", "量子纠缠与贝尔不等式", "广义相对论的时空弯曲",
        "热力学第二定律与熵", "希格斯机制", "量子场论基础",
        "超导的BCS理论", "杨-米尔斯规范场论", "重整化群",
        "自旋玻璃与复本方法", "拓扑绝缘体", "AdS/CFT对偶",
    ],
    "生物学": [
        "CRISPR-Cas9基因编辑", "化学渗透假说", "细胞凋亡的信号通路",
        "表观遗传学", "神经可塑性", "内共生产假说",
        "免疫检查点与癌症治疗", "微生物组学", "端粒与衰老",
        "光遗传学", "蛋白质折叠的能量景观", "群体遗传学的Hardy-Weinberg平衡",
    ],
    "历史学": [
        "年鉴学派与长时段理论", "大分流：东西方经济分化", "布罗代尔的地中海世界",
        "汤因比的文明兴衰论", "费尔南德·布罗代尔的三层时间", "东方专制主义与水利社会",
        "全球史视角下的哥伦布大交换", "托马斯·库恩的科学革命结构",
        "霍布斯鲍姆的漫长的19世纪", "军事革命论", "年鉴学派心态史",
    ],
    "数学": [
        "哥德尔不完备定理", "黎曼猜想与素数分布", "伽罗瓦理论与群论",
        "庞加莱猜想与几何化", "傅里叶分析与调和分析", "信息熵与编码理论",
        "蒙日-安培方程", "朗兰兹纲领", "代数拓扑的同调论",
        "随机过程与马尔可夫链", "复分析与黎曼曲面", "范畴论",
    ],
    "文学": [
        "巴赫金的复调理论", "接受美学与读者反应批评", "解构主义与德里达",
        "陌生化理论：什克洛夫斯基", "叙事学：热奈特的叙事话语", "互文性理论",
        "后殖民文学理论：赛义德的东方学", "女性主义文学批评",
        "现代主义小说的意识流", "符号学与罗兰·巴特", "生态批评",
    ],
}

import random


# ============================================================
# DeepSeek API 故事生成
# ============================================================
def generate_story_via_deepseek(subject: str) -> str:
    """调用 DeepSeek API 生成故事。失败抛出异常。"""
    from openai import OpenAI

    api_key = os.environ["DEEPSEEK_API_KEY"]

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    # 从主题池中随机选一个
    topics = SUBJECT_TOPICS.get(subject, [subject])
    topic = random.choice(topics)

    print(f"🎲 今日选题: {topic}")

    system_prompt = f"""你是一位精通寓教于乐的故事大师和各领域的知识专家。
你的任务是将一个硬核的{subject}知识转化为引人入胜的故事。今日的具体主题是：{topic}。

严格要求：
1. 故事长度1000-2000字（中文）
2. 用一句话总结核心知识点，将其巧妙融入情节之中
3. 故事必须聚焦于知识本身：发现过程背景 → 核心理论内容 → 后续发展与影响 → 实际应用及例子
4. 难度至少为大学本科或研究生水平，不要简化概念
5. 主角使用第二人称"你"，其他人物只用职业称呼（如"你的导师""一位统计物理学家"）
6. 故事结尾必须包含三部分（用分隔线隔开）：
   - 📌 一句话知识点
   - 💡 启发
   - 🔧 如何在工作和生活中应用
7. 引入部分相对弱化，重点放在知识本身。不要虚构情感故事，要专注于理论和思想。

请直接输出故事，不要加任何前缀说明如"好的，以下是今天的故事"。"""

    user_prompt = f"请为今天的{subject}专栏创作一篇知识故事。选题：{topic}。"

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        max_tokens=4000,
    )

    story = response.choices[0].message.content
    if not story:
        raise RuntimeError("DeepSeek API 返回空内容")

    print(f"✅ DeepSeek 故事生成成功 ({len(story)} 字符)")
    return story.strip()


# ============================================================
# 邮件发送
# ============================================================
def send_email(subject_line: str, body: str) -> bool:
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    sender = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    receiver = os.environ.get("TO_EMAIL", "threebodyhack@gmail.com")

    if not sender or not password:
        print("❌ 邮件配置不完整：缺少 SMTP_USERNAME 或 SMTP_PASSWORD")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject_line

    # 纯文本 + HTML 双版本
    html_body = f"""<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
      max-width: 680px; margin: 0 auto; padding: 20px; line-height: 1.85;
      color: #333; background: #fafaf8;">
  <div style="background: #fff; border-radius: 8px; padding: 32px;
       box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
    {body.replace(chr(10), '<br>')}
  </div>
  <div style="text-align: center; margin-top: 24px; font-size: 12px;
       color: #aaa;">
    每日知识故事 · 由 DeepSeek 生成 · 通过 GitHub Actions 自动发送
  </div>
</body>
</html>"""

    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())
        print(f"✅ 邮件已发送至 {receiver}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


# ============================================================
# 主流程
# ============================================================
def main():
    today = datetime.date.today()
    weekday = today.weekday()  # 0=周一, ..., 6=周日
    day_name, subject = WEEKDAY_SUBJECT[weekday]

    print(f"📅 今天是 {today} {day_name} → 学科: {subject}")

    # 调用 DeepSeek 生成故事
    story = generate_story_via_deepseek(subject)

    # 构建邮件
    subject_line = f"【{day_name}·{subject}】每日知识故事 — {today}"

    signature = f"""

━━━━━━━━━━━━━━━━━━━━
📬 每日知识故事 · {day_name} {subject}
📅 {today}  |  生成: DeepSeek
━━━━━━━━━━━━━━━━━━━━"""

    full_body = story + signature

    # 发送
    success = send_email(subject_line, full_body)

    if not success:
        print("邮件发送环节失败，请检查配置。")
        sys.exit(1)

    print("🎉 完成！")


if __name__ == "__main__":
    main()
