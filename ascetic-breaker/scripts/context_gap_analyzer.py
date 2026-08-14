#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
苦行僧破执术 - 上下文缺口分析脚本 v2 (Context Gap Analyzer) for Claude Code

分析任务描述和已有上下文，识别信息缺口、评分并推荐获取方式。
v2 新增：缺口影响评分、获取方式路由（含domain-research委托建议）、JSON输出、复查循环。

用法:
    python context_gap_analyzer.py --task "任务描述" --context "已有上下文"
    python context_gap_analyzer.py --task "任务" --context "上下文" --json
    python context_gap_analyzer.py --interactive
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class Gap:
    """表示一个信息缺口"""
    category: str          # 缺口类别 (A版本/B API/C数据/D领域/E现有资产)
    description: str       # 缺口描述
    impact: str            # 影响程度: 高/中/低
    acquisition: str       # 获取方式: 本Skill直接检索/委托domain-research/Glob-Grep/向用户确认
    acquisition_detail: str # 具体获取建议
    priority: int          # 检索优先级: 0=P0(本地), 1=P1(官方文档), 2=P2(GitHub/SO), 3=P3(博客), 4=委托


# 缺口检测规则
GAP_RULES = {
    "代码开发": [
        {
            "patterns": ["csv", "excel", "xlsx", "json文件", "xml", "yaml文件", "数据文件", "读取文件"],
            "category": "C-数据输入",
            "description": "未明确输入数据的格式、编码和结构",
            "impact": "高",
            "acquisition": "Glob-Grep",
            "acquisition_detail": "用Glob搜索数据文件，Read查看样例数据确认编码和结构",
            "priority": 0
        },
        {
            "patterns": ["库", "依赖", "package", "import", "require", "pip", "npm", "gem"],
            "category": "A-版本兼容",
            "description": "未明确可用的依赖库和版本",
            "impact": "高",
            "acquisition": "Glob-Grep",
            "acquisition_detail": "用Glob搜索requirements.txt/package.json/go.mod等依赖文件",
            "priority": 0
        },
        {
            "patterns": ["api", "接口", "endpoint", "请求", "调用", "rest", "http"],
            "category": "B-API接口",
            "description": "API签名、认证方式或版本不明确",
            "impact": "高",
            "acquisition": "本Skill直接检索",
            "acquisition_detail": "WebSearch + WebFetch查官方文档，提取API签名、参数、认证方式",
            "priority": 1
        },
        {
            "patterns": ["错误", "报错", "error", "exception", "bug", "异常", "traceback", "crash"],
            "category": "B-错误诊断",
            "description": "需要搜索错误信息以找到成熟解决方案",
            "impact": "高",
            "acquisition": "本Skill直接检索",
            "acquisition_detail": "WebSearch搜索完整错误信息，优先Stack Overflow和GitHub Issues",
            "priority": 2
        },
        {
            "patterns": ["函数", "工具", "util", "helper", "复用", "已有", "之前写过"],
            "category": "E-现有资产",
            "description": "未检查项目内是否已有可复用的函数/模块",
            "impact": "中",
            "acquisition": "Glob-Grep",
            "acquisition_detail": "用Grep搜索项目内已有实现，Glob搜索utils/helpers目录",
            "priority": 0
        },
        {
            "patterns": ["配置", "config", "设置", "环境变量", "env"],
            "category": "E-现有资产",
            "description": "未检查项目配置文件和环境变量",
            "impact": "中",
            "acquisition": "Glob-Grep",
            "acquisition_detail": "用Glob搜索配置文件(.env, config.*, settings.*)",
            "priority": 0
        },
        {
            "patterns": ["测试", "test", "单元测试", "pytest", "jest"],
            "category": "E-现有资产",
            "description": "未了解项目测试框架和测试模式",
            "impact": "低",
            "acquisition": "Glob-Grep",
            "acquisition_detail": "用Glob搜索test目录，Grep搜索现有测试用例了解模式",
            "priority": 0
        },
    ],
    "调研分析": [
        {
            "patterns": ["行业", "市场", "规模", "趋势", "现状", "格局", "份额"],
            "category": "D-领域知识",
            "description": "需要最新的行业数据，预训练知识可能过时",
            "impact": "高",
            "acquisition": "委托domain-research",
            "acquisition_detail": "委托domain-research多平台检索最新行业报告、统计数据和市场分析",
            "priority": 4
        },
        {
            "patterns": ["政策", "法规", "规定", "标准", "监管", "合规"],
            "category": "D-领域知识",
            "description": "需要确认最新的政策法规变化",
            "impact": "高",
            "acquisition": "委托domain-research",
            "acquisition_detail": "委托domain-research检索政府官网和权威来源的最新政策法规",
            "priority": 4
        },
        {
            "patterns": ["对比", "比较", "vs", "选型", "哪个好", "区别"],
            "category": "D-领域知识",
            "description": "需要多维度对比信息",
            "impact": "中",
            "acquisition": "委托domain-research",
            "acquisition_detail": "委托domain-research多平台检索对比评测和用户反馈",
            "priority": 4
        },
        {
            "patterns": ["最新", "2024", "2025", "2026", "近期", "最近"],
            "category": "D-领域知识",
            "description": "时效性要求高，需要最新信息",
            "impact": "高",
            "acquisition": "委托domain-research",
            "acquisition_detail": "委托domain-research检索近12个月的最新内容",
            "priority": 4
        },
    ],
    "方案设计": [
        {
            "patterns": ["架构", "设计", "方案", "系统设计", "技术选型"],
            "category": "D-领域知识",
            "description": "未检索是否有成熟的架构模式或开源方案",
            "impact": "高",
            "acquisition": "委托domain-research",
            "acquisition_detail": "委托domain-research检索GitHub高star项目、技术博客和最佳实践",
            "priority": 4
        },
        {
            "patterns": ["性能", "并发", "规模", "吞吐量", "延迟", "qps"],
            "category": "D-领域知识",
            "description": "缺少性能基准数据和规模要求",
            "impact": "高",
            "acquisition": "本Skill直接检索",
            "acquisition_detail": "WebSearch搜索性能基准测试报告和官方性能文档",
            "priority": 1
        },
        {
            "patterns": ["开源", "库", "框架", "组件", "中间件"],
            "category": "B-API接口",
            "description": "未调研成熟开源方案",
            "impact": "中",
            "acquisition": "本Skill直接检索",
            "acquisition_detail": "WebSearch搜索GitHub，WebFetch查看README和star数",
            "priority": 2
        },
    ],
}

# 通用模糊词检测
VAGUENESS_PATTERNS = ["应该是", "大概", "可能", "也许", "通常", "一般来说", "估计", "差不多"]

# 通用版本检测
VERSION_PATTERNS = ["版本", "version", "v2", "v3", "哪个版本", "兼容"]


def detect_task_type(task, context):
    """检测任务类型"""
    text = (task + " " + context).lower()
    types = []

    code_keywords = ["代码", "程序", "脚本", "函数", "编程", "开发", "bug", "error",
                     "python", "javascript", "java", "api", "csv", "json", "code",
                     "script", "function", "class", "import", "库", "依赖", "报错"]
    research_keywords = ["分析", "调研", "研究", "行业", "市场", "趋势", "报告",
                         "现状", "对比", "research", "analysis", "market", "了解"]
    design_keywords = ["设计", "架构", "方案", "系统", "选型", "design", "architecture",
                       "pattern", "system", "技术选型"]

    if any(kw in text for kw in code_keywords):
        types.append("代码开发")
    if any(kw in text for kw in research_keywords):
        types.append("调研分析")
    if any(kw in text for kw in design_keywords):
        types.append("方案设计")

    return types if types else ["通用"]


def analyze_gaps(task, context):
    """分析上下文缺口"""
    gaps = []
    text = (task + " " + context).lower()
    task_types = detect_task_type(task, context)

    for task_type in task_types:
        if task_type in GAP_RULES:
            for rule in GAP_RULES[task_type]:
                if any(kw in text for kw in rule["patterns"]):
                    gaps.append(Gap(
                        category=rule["category"],
                        description=rule["description"],
                        impact=rule["impact"],
                        acquisition=rule["acquisition"],
                        acquisition_detail=rule["acquisition_detail"],
                        priority=rule["priority"]
                    ))

    if any(kw in text for kw in VAGUENESS_PATTERNS):
        gaps.append(Gap(
            category="B-API接口",
            description="上下文中使用了模糊表述（'应该是''大概'等），关键事实需要验证",
            impact="高",
            acquisition="本Skill直接检索",
            acquisition_detail="WebSearch + WebFetch查证官方文档，替换模糊表述",
            priority=1
        ))

    if any(kw in text for kw in VERSION_PATTERNS):
        gaps.append(Gap(
            category="A-版本兼容",
            description="涉及版本信息但未明确具体版本号",
            impact="高",
            acquisition="Glob-Grep",
            acquisition_detail="Glob搜索依赖文件确认版本，或WebFetch查版本兼容文档",
            priority=0
        ))

    seen = set()
    unique_gaps = []
    for gap in gaps:
        key = (gap.category, gap.description)
        if key not in seen:
            seen.add(key)
            unique_gaps.append(gap)

    unique_gaps.sort(key=lambda g: g.priority)
    return unique_gaps


def validate_gaps(gaps, task, context):
    """复查缺口清单（Validator->Fix->Repeat）"""
    issues = []

    if "代码开发" in detect_task_type(task, context):
        if not any(g.category.startswith("E") for g in gaps):
            issues.append("建议检查项目内是否已有可复用代码（E类缺口）")

    for gap in gaps:
        if gap.category == "A-版本兼容" and ("版本" in context or "version" in context.lower()):
            issues.append("可能误报：'" + gap.description + "' - 上下文中似乎已提及版本信息")

    for gap in gaps:
        if gap.impact == "高" and gap.acquisition == "本Skill直接检索" and gap.priority > 2:
            issues.append("高影响缺口'" + gap.description + "'的检索优先级偏低，建议提高")

    return {
        "round": 1,
        "issues_found": len(issues),
        "issues": issues,
        "passed": len(issues) == 0
    }


def get_routing_summary(gaps):
    """汇总路由建议"""
    routing = {
        "delegate_domain_research": [],
        "direct_search": [],
        "local_search": [],
        "ask_user": []
    }

    for gap in gaps:
        if gap.acquisition == "委托domain-research":
            routing["delegate_domain_research"].append(gap.description)
        elif gap.acquisition == "本Skill直接检索":
            routing["direct_search"].append(gap.description)
        elif gap.acquisition == "Glob-Grep":
            routing["local_search"].append(gap.description)
        elif gap.acquisition == "向用户确认":
            routing["ask_user"].append(gap.description)

    return routing


def format_report(task, context, gaps, validation):
    """格式化输出报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("  苦行僧破执术 - 上下文缺口分析报告 v2 (Claude Code)")
    lines.append("=" * 70)
    lines.append("")
    lines.append("任务描述: " + task)
    lines.append("上下文长度: " + str(len(context)) + " 字符")
    task_types = detect_task_type(task, context)
    lines.append("任务类型: " + ", ".join(task_types))
    lines.append("")

    if not gaps:
        lines.append("[OK] 未检测到明显的信息缺口，可以直接执行。")
        lines.append("")
        lines.append("提示: 仍建议在执行前快速确认:")
        lines.append("  1. 项目内是否已有可复用代码 (Glob/Grep)")
        lines.append("  2. 依赖版本是否兼容")
        lines.append("  3. 是否有最新的官方文档需要参考")
    else:
        high_count = sum(1 for g in gaps if g.impact == "高")
        med_count = sum(1 for g in gaps if g.impact == "中")
        low_count = sum(1 for g in gaps if g.impact == "低")
        lines.append("检测到 " + str(len(gaps)) + " 个信息缺口（高:" + str(high_count) + " 中:" + str(med_count) + " 低:" + str(low_count) + "）:")
        lines.append("")

        for i, gap in enumerate(gaps, 1):
            lines.append("  [" + str(i) + "] " + gap.category + " (影响: " + gap.impact + ", 优先级: P" + str(gap.priority) + ")")
            lines.append("      缺口: " + gap.description)
            lines.append("      获取: " + gap.acquisition)
            lines.append("      建议: " + gap.acquisition_detail)
            lines.append("")

        routing = get_routing_summary(gaps)
        lines.append("-" * 70)
        lines.append("资源获取路由:")
        if routing["delegate_domain_research"]:
            lines.append("  -> 委托 domain-research (" + str(len(routing["delegate_domain_research"])) + "个):")
            for item in routing["delegate_domain_research"]:
                lines.append("    - " + item)
        if routing["direct_search"]:
            lines.append("  -> 本Skill直接检索 (" + str(len(routing["direct_search"])) + "个):")
            for item in routing["direct_search"]:
                lines.append("    - " + item)
        if routing["local_search"]:
            lines.append("  -> 本地 Glob/Grep (" + str(len(routing["local_search"])) + "个):")
            for item in routing["local_search"]:
                lines.append("    - " + item)
        if routing["ask_user"]:
            lines.append("  -> 向用户确认 (" + str(len(routing["ask_user"])) + "个):")
            for item in routing["ask_user"]:
                lines.append("    - " + item)
        lines.append("")

        lines.append("-" * 70)
        lines.append("复查结果: " + ("通过" if validation["passed"] else "需关注"))
        if validation["issues"]:
            for issue in validation["issues"]:
                lines.append("  ! " + issue)
        lines.append("")

        lines.append("-" * 70)
        lines.append("下一步:")
        lines.append("  1. P0: 本地 Glob/Grep 搜索项目内已有资源")
        lines.append("  2. P1-P2: 本Skill用WebSearch/WebFetch定向检索官方文档/GitHub/SO")
        lines.append("  3. P4: 委托 domain-research 执行多平台调研")
        lines.append("  4. 检索后进入Step 3方案评分和交叉验证")
        lines.append("  5. 3轮检索无结果的缺口 -> Step 4中显式标注假设")

    lines.append("=" * 70)
    return "\n".join(lines)


def interactive_mode():
    """交互模式"""
    print("=" * 70)
    print("  苦行僧破执术 - 上下文缺口分析 v2（交互模式）")
    print("=" * 70)
    print()

    task = input("请输入任务描述: ").strip()
    if not task:
        print("错误: 任务描述不能为空")
        sys.exit(1)

    print()
    print("请输入已有上下文（输入空行结束）:")
    context_lines = []
    while True:
        line = input()
        if not line:
            break
        context_lines.append(line)
    context = "\n".join(context_lines)

    print()
    gaps = analyze_gaps(task, context)
    validation = validate_gaps(gaps, task, context)
    report = format_report(task, context, gaps, validation)
    print(report)


def main():
    parser = argparse.ArgumentParser(
        description="苦行僧破执术 - 上下文缺口分析工具 v2 (Claude Code)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python context_gap_analyzer.py --task "写一个CSV解析脚本" --context "用pandas"
  python context_gap_analyzer.py --task "分析新能源行业" --json
  python context_gap_analyzer.py --interactive
        """
    )
    parser.add_argument("--task", "-t", help="任务描述")
    parser.add_argument("--context", "-c", default="", help="已有上下文")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    if not args.task:
        parser.error("请提供 --task 参数或使用 --interactive 模式")

    gaps = analyze_gaps(args.task, args.context)
    validation = validate_gaps(gaps, args.task, args.context)

    if args.json:
        result = {
            "task": args.task,
            "context_length": len(args.context),
            "task_types": detect_task_type(args.task, args.context),
            "gaps": [asdict(g) for g in gaps],
            "validation": validation,
            "routing": get_routing_summary(gaps),
            "summary": {
                "total": len(gaps),
                "high": sum(1 for g in gaps if g.impact == "高"),
                "medium": sum(1 for g in gaps if g.impact == "中"),
                "low": sum(1 for g in gaps if g.impact == "低"),
                "delegate_to_domain_research": sum(1 for g in gaps if g.acquisition == "委托domain-research"),
                "direct_search": sum(1 for g in gaps if g.acquisition == "本Skill直接检索"),
                "local_search": sum(1 for g in gaps if g.acquisition == "Glob-Grep"),
            }
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        report = format_report(args.task, args.context, gaps, validation)
        print(report)


if __name__ == "__main__":
    main()
