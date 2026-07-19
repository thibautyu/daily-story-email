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
# 各学科知识领域（共约 50 个/学科，配合状态追踪确保不重复）
# ============================================================
SUBJECT_TOPICS = {
    "经济学": [
        "纳什均衡与博弈论", "科斯定理与交易成本", "蒙代尔不可能三角",
        "期权定价的Black-Scholes模型", "有效市场假说", "比较优势理论",
        "索洛增长模型", "明斯基金融不稳定假说", "阿罗不可能定理",
        "信息不对称与柠檬市场", "李嘉图等价", "IS-LM模型",
        "边际效用革命", "帕累托最优", "赫克歇尔-俄林模型",
        "菲利普斯曲线与滞胀", "拉弗曲线与供给侧经济学", "托宾q理论",
        "凯恩斯乘数效应", "货币数量论", "理性预期革命",
        "时间不一致性与中央银行独立性", "格罗斯曼-斯蒂格利茨悖论",
        "赫伯特·西蒙的有限理性", "阿马蒂亚·森的能力方法",
        "马克思的剩余价值理论", "熊彼特的创造性破坏", "哈耶克的自发秩序",
        "庇古税与外部性内部化", "斯托尔珀-萨缪尔森定理", "巴拉萨-萨缪尔森效应",
        "蒙代尔-弗莱明模型", "三元悖论的实证检验", "泰勒规则",
        "卢卡斯批判", "Fama-French三因子模型", "CAPM资本资产定价模型",
        "无套利定价原理", "MM定理", "委托代理问题",
        "公共选择理论", "寻租行为", "荷兰病与资源诅咒",
        "中等收入陷阱", "库兹涅茨倒U曲线", "丁伯根法则",
        "最优货币区理论", "债务-通缩螺旋", "大稳健",
    ],
    "心理学": [
        "认知失调理论", "斯坦福监狱实验与情境力量", "习得性无助",
        "米尔格拉姆服从实验", "峰终定律", "双加工理论",
        "依恋理论", "拖延的心理学机制", "达克效应",
        "心流理论", "锚定效应", "前景理论",
        "自我决定理论", "刻板印象威胁", "镜像神经元与共情",
        "巴纳姆效应与冷读术", "基本归因错误", "确认偏误",
        "斯坦福棉花糖实验与延迟满足", "从众效应的阿施实验", "旁观者效应",
        "光环效应", "损失厌恶", "框架效应",
        "可得性启发", "代表性启发", "沉没成本谬误",
        "计划谬误", "逆火效应", "虚假共识效应",
        "替代性创伤与共情疲劳", "创伤后成长", "正念与注意力网络",
        "执行功能的神经基础", "工作记忆的多成分模型", "情绪调节策略",
        "社会认同理论", "群体极化", "接触假说",
        "恐怖管理理论", "自我效能感", "防御性悲观",
        "黑暗三人格", "自恋的双元模型", "心理韧性",
        "心理理论的ToM范式", "互惠利他主义", "公平感与最后通牒博弈",
    ],
    "物理学": [
        "麦克斯韦方程组", "量子纠缠与贝尔不等式", "广义相对论的时空弯曲",
        "热力学第二定律与熵", "希格斯机制", "量子场论基础",
        "超导的BCS理论", "杨-米尔斯规范场论", "重整化群",
        "自旋玻璃与复本方法", "拓扑绝缘体", "AdS/CFT对偶",
        "费曼路径积分", "薛定谔方程与波函数坍缩", "EPR悖论",
        "黑洞热力学与霍金辐射", "宇宙暴胀理论", "暗物质与暗能量",
        "标准模型与费米子代", "中微子振荡", "CP对称性破缺",
        "量子霍尔效应", "分数量子霍尔效应", "斯格明子",
        "朗道费米液体理论", "安德森局域化", "莫特绝缘体",
        "拓扑序与任意子", "张量网络与多体纠缠", "量子纠错码",
        "引力波探测原理", "事件视界望远镜", "彭罗斯宇宙监督假设",
        "全息原理", "弦论的对偶性", "大N展开",
        "统计力学中的遍历性", "涨落耗散定理", "Onsager倒易关系",
        "非线性动力学与混沌", "孤子", "贝里相位",
        "卡西米尔效应", "跃迁辐射", "同步辐射",
        "等离子体物理与聚变", "量子Zeno效应", "弱测量与弱值",
    ],
    "生物学": [
        "CRISPR-Cas9基因编辑", "化学渗透假说", "细胞凋亡的信号通路",
        "表观遗传学", "神经可塑性", "内共生产假说",
        "免疫检查点与癌症治疗", "微生物组学", "端粒与衰老",
        "光遗传学", "蛋白质折叠的能量景观", "群体遗传学的Hardy-Weinberg平衡",
        "DNA损伤应答网络", "细胞周期调控与检查点", "程序性细胞死亡与坏死性凋亡",
        "干细胞与再生医学", "诱导多能干细胞(iPSC)", "器官发生与形态发生素梯度",
        "肠道-脑轴", "昼夜节律的分子机制", "睡眠与记忆巩固",
        "肠道菌群与免疫发育", "癌细胞的Warburg效应", "血管新生与肿瘤微环境",
        "轴突导向分子机制", "突触修剪与发育", "小胶质细胞与神经退行",
        "适应性免疫与V(D)J重组", "主要组织相容性复合体MHC", "过敏反应的免疫学基础",
        "进化发育生物学(Evo-Devo)", "同源异形盒基因", "趋同进化",
        "群体瓶颈与遗传漂变", "中性演化理论", "性选择的Fisher失控模型",
        "水平基因转移", "古菌与真核生物起源", "病毒与宿主共进化",
        "生物信息学与序列比对算法", "系统发育树构建", "单细胞测序技术",
        "冷冻电镜的结构生物学", "蛋白质-蛋白质相互作用网络", "合成生物学回路",
    ],
    "历史学": [
        "年鉴学派与长时段理论", "大分流：东西方经济分化", "布罗代尔的地中海世界",
        "汤因比的文明兴衰论", "全球史视角下的哥伦布大交换", "托马斯·库恩的科学革命结构",
        "霍布斯鲍姆的漫长的19世纪", "军事革命论", "东方专制主义与水利社会",
        "年鉴学派心态史", "微观史学与奶酪与虫", "福柯的知识考古学",
        "爱德华·吉本的罗马帝国衰亡史", "斯宾格勒的西方的没落", "马克·布洛赫的封建社会",
        "埃里克·霍布斯鲍姆的年代四部曲", "后殖民史学", "底层研究学派",
        "记忆史学与记忆之场", "跨国史与全球微观史", "大西洋史",
        "环境史与人类世", "情感史", "身体史",
        "蒙古帝国的世界史意义", "丝绸之路的跨文化史", "印度洋贸易网络",
        "黑死病的社会经济后果", "印刷术与宗教改革", "科学革命的社会语境",
        "启蒙运动的多重面相", "法国大革命的史学争论", "英国工业革命的原因",
        "大西洋奴隶贸易", "明治维新的比较史", "冷战史的新档案研究",
        "去殖民化过程", "1968年的全球革命", "新自由主义的历史起源",
        "中国的改革开放", "数字史学", "口述史方法论",
        "性别史的兴起", "量化史学与计量经济史", "帝国主义比较研究",
    ],
    "数学": [
        "哥德尔不完备定理", "黎曼猜想与素数分布", "伽罗瓦理论与群论",
        "庞加莱猜想与几何化", "傅里叶分析与调和分析", "信息熵与编码理论",
        "蒙日-安培方程", "朗兰兹纲领", "代数拓扑的同调论",
        "随机过程与马尔可夫链", "复分析与黎曼曲面", "范畴论",
        "椭圆曲线与模形式", "类域论", "代数几何的概形理论",
        "微分拓扑的Morse理论", "辛几何与几何量子化", "指标定理",
        "Sobolev空间与偏微分方程", "变分法", "最优传输",
        "随机微积分与Black-Scholes", "大偏差理论", "随机矩阵理论",
        "组合数学的极值图论", "加性组合", "代数数论",
        "Diophantine逼近", "遍历理论", "动力系统与KAM理论",
        "偏序集与Möbius反演", "表示论", "李代数",
        "k-理论", "代数K-理论", "Hodge理论",
        "复几何的Calabi-Yau流形", "镜像对称", "Donaldson理论",
        "完美空间与p进几何", "几何群论", "低维拓扑",
        "纽结理论", "四色定理的计算机证明", "计算复杂性理论",
        "密码学与零知识证明", "压缩感知", "小波分析",
    ],
    "文学": [
        "巴赫金的复调理论", "接受美学与读者反应批评", "解构主义与德里达",
        "陌生化理论：什克洛夫斯基", "叙事学：热奈特的叙事话语", "互文性理论",
        "后殖民文学理论：赛义德的东方学", "女性主义文学批评",
        "现代主义小说的意识流", "符号学与罗兰·巴特", "生态批评",
        "神话-原型批评：诺斯罗普·弗莱", "精神分析文学批评：拉康", "新历史主义",
        "俄国形式主义", "布拉格结构主义", "英美新批评的细读法",
        "对话理论", "狂欢化诗学", "时空体理论",
        "隐含读者理论", "叙事聚焦", "元小说",
        "反讽理论", "文学场域：布迪厄", "霸权理论：葛兰西",
        "世界文学与歌德", "影响的焦虑：哈罗德·布鲁姆", "误读理论",
        "翻译研究", "比较文学", "世界体系与世界文学",
        "先锋派艺术", "荒诞派戏剧", "魔幻现实主义",
        "存在主义小说", "后现代主义的特征", "元叙事",
        "文学经典的建构", "口头传统与书面文学", "抒情诗理论",
        "文学达尔文主义", "认知文学研究", "数字人文与远读",
        "自由间接引语", "叙事不可靠性", "后人类叙事",
        "创伤理论", "身体政治", "怪异理论",
        "情动转向", "动物研究", "后批评",
    ],
}

import random
import json

# ============================================================
# 状态追踪：确保每个学科的主题永不重复
# ============================================================
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "used_topics.json")

def load_used_topics() -> dict[str, list[str]]:
    """加载已用主题记录。"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_used_topics(used: dict[str, list[str]]) -> None:
    """保存已用主题记录。"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)

def pick_unused_topic(subject: str) -> str:
    """从主题池中选一个从未用过的。用完一轮自动重置。"""
    all_topics = SUBJECT_TOPICS.get(subject, [subject])
    used = load_used_topics()
    used_topics = used.get(subject, [])

    # 找出未使用的
    available = [t for t in all_topics if t not in used_topics]

    if not available:
        # 全部用过一轮，清空重置
        print(f"🔄 {subject} 全部 {len(all_topics)} 个主题已用完，开始新的一轮！")
        used_topics = []
        available = list(all_topics)

    # 随机选一个
    chosen = random.choice(available)
    used_topics.append(chosen)
    used[subject] = used_topics
    save_used_topics(used)

    remaining = len(all_topics) - len(used_topics)
    print(f"📊 {subject} 进度: {len(used_topics)}/{len(all_topics)} 已用, {remaining} 剩余")
    return chosen


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

    # 从主题池中选一个从未用过的
    topic = pick_unused_topic(subject)

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
