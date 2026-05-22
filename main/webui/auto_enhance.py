#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebUI 自动化增强脚本
持续监控、分析和优化WebUI
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class WebUIAutoEnhancer:
    """WebUI 自动化增强器"""

    def __init__(self, webui_dir: str = None):
        self.webui_dir = Path(webui_dir) if webui_dir else Path(__file__).parent
        self.screenshots_dir = self.webui_dir / "screenshots"
        self.enhancements_log = self.webui_dir / "enhancements_log.jsonl"
        self.screenshots_dir.mkdir(exist_ok=True)

    def run_audit(self) -> Dict[str, Any]:
        """运行Playwright审计"""
        try:
            result = subprocess.run(
                ["python", "playwright_automation.py"],
                cwd=self.webui_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                # 查找最新的审计报告
                audit_reports = sorted(self.screenshots_dir.glob("audit_report_*.json"))
                if audit_reports:
                    with open(audit_reports[-1], "r", encoding="utf-8") as f:
                        return json.load(f)
            return {"error": "审计失败"}
        except Exception as e:
            return {"error": str(e)}

    def analyze_enhancement_opportunities(self, audit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析增强机会"""
        opportunities = []

        # 性能分析
        performance = audit_data.get("performance", {})
        load_time = performance.get("loadTime", 0)

        if load_time > 500:
            opportunities.append({
                "type": "performance",
                "priority": "high",
                "title": "优化加载性能",
                "description": f"当前加载时间 {load_time}ms，建议优化到 300ms 以下",
                "actions": [
                    "启用代码分割和懒加载",
                    "压缩和优化静态资源",
                    "使用CDN加速"
                ]
            })
        elif load_time > 300:
            opportunities.append({
                "type": "performance",
                "priority": "medium",
                "title": "进一步优化性能",
                "description": f"当前加载时间 {load_time}ms，可以进一步优化",
                "actions": [
                    "优化关键渲染路径",
                    "减少阻塞资源"
                ]
            })

        # 功能分析
        features = audit_data.get("features", [])
        passed_features = sum(1 for f in features if f.get("status") == "pass")
        total_features = len(features)

        if passed_features < total_features:
            opportunities.append({
                "type": "functionality",
                "priority": "high",
                "title": "修复失败的功能测试",
                "description": f"{total_features - passed_features} 个功能测试失败",
                "actions": [
                    "检查相关代码逻辑",
                    "修复交互问题",
                    "增强错误处理"
                ]
            })

        # 视觉增强建议
        opportunities.append({
            "type": "visual",
            "priority": "low",
            "title": "添加视觉特效",
            "description": "增强用户视觉体验",
            "actions": [
                "添加粒子动画效果",
                "实现3D卡片效果",
                "增强过渡动画"
            ]
        })

        # 数据可视化
        opportunities.append({
            "type": "analytics",
            "priority": "medium",
            "title": "增强数据可视化",
            "description": "添加更多图表和统计",
            "actions": [
                "添加实时Token使用图表",
                "实现Agent活动热力图",
                "添加成本趋势分析"
            ]
        })

        return opportunities

    def generate_enhancement_plan(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成增强计划"""
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda x: priority_order.get(x["priority"], 3))

        plan = {
            "timestamp": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "high_priority": sum(1 for o in opportunities if o["priority"] == "high"),
            "medium_priority": sum(1 for o in opportunities if o["priority"] == "medium"),
            "low_priority": sum(1 for o in opportunities if o["priority"] == "low"),
            "opportunities": opportunities,
            "recommended_actions": self._get_recommended_actions(opportunities)
        }

        return plan

    def _get_recommended_actions(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """获取推荐操作"""
        actions = []

        # 高优先级操作
        high_priority_ops = [o for o in opportunities if o["priority"] == "high"]
        if high_priority_ops:
            actions.append("🔥 立即处理高优先级问题:")
            for op in high_priority_ops:
                actions.append(f"  • {op['title']}")

        # 中优先级操作
        medium_priority_ops = [o for o in opportunities if o["priority"] == "medium"]
        if medium_priority_ops:
            actions.append("📈 本周处理中优先级改进:")
            for op in medium_priority_ops[:3]:
                actions.append(f"  • {op['title']}")

        # 低优先级操作
        low_priority_ops = [o for o in opportunities if o["priority"] == "low"]
        if low_priority_ops:
            actions.append("💡 考虑未来增强:")
            for op in low_priority_ops[:2]:
                actions.append(f"  • {op['title']}")

        return actions

    def log_enhancement(self, plan: Dict[str, Any]):
        """记录增强计划"""
        with open(self.enhancements_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(plan, ensure_ascii=False) + "\n")

    def run_continuous_enhancement(self, interval_minutes: int = 30):
        """运行持续增强"""
        print(f"🚀 WebUI 自动化增强器启动")
        print(f"⏰ 检测间隔: {interval_minutes} 分钟")
        print(f"📁 工作目录: {self.webui_dir}")
        print("=" * 60)

        while True:
            try:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始增强周期...")

                # 运行审计
                print("📊 运行性能审计...")
                audit_data = self.run_audit()

                if "error" in audit_data:
                    print(f"⚠️  审计失败: {audit_data['error']}")
                    time.sleep(interval_minutes * 60)
                    continue

                # 分析机会
                print("🔍 分析增强机会...")
                opportunities = self.analyze_enhancement_opportunities(audit_data)

                # 生成计划
                print("📋 生成增强计划...")
                plan = self.generate_enhancement_plan(opportunities)

                # 输出报告
                print(f"\n📈 发现 {plan['total_opportunities']} 个增强机会")
                print(f"   高优先级: {plan['high_priority']}")
                print(f"   中优先级: {plan['medium_priority']}")
                print(f"   低优先级: {plan['low_priority']}")

                if plan['recommended_actions']:
                    print(f"\n💡 推荐操作:")
                    for action in plan['recommended_actions']:
                        print(f"  {action}")

                # 记录
                self.log_enhancement(plan)

                print(f"\n✅ 增强周期完成")
                print(f"⏰ 下次检测: {interval_minutes} 分钟后")
                print("=" * 60)

            except KeyboardInterrupt:
                print("\n\n👋 自动化增强器已停止")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

            # 等待下一个周期
            time.sleep(interval_minutes * 60)

    def run_once(self) -> Dict[str, Any]:
        """运行一次增强分析"""
        print("📊 运行性能审计...")
        audit_data = self.run_audit()

        if "error" in audit_data:
            return {"error": audit_data["error"]}

        print("🔍 分析增强机会...")
        opportunities = self.analyze_enhancement_opportunities(audit_data)

        print("📋 生成增强计划...")
        plan = self.generate_enhancement_plan(opportunities)

        self.log_enhancement(plan)

        return plan

def main():
    import argparse

    parser = argparse.ArgumentParser(description="WebUI 自动化增强器")
    parser.add_argument("--continuous", "-c", action="store_true", help="持续运行模式")
    parser.add_argument("--interval", "-i", type=int, default=30, help="检测间隔（分钟）")
    parser.add_argument("--webui-dir", "-d", type=str, help="WebUI 目录路径")

    args = parser.parse_args()

    enhancer = WebUIAutoEnhancer(args.webui_dir)

    if args.continuous:
        enhancer.run_continuous_enhancement(args.interval)
    else:
        plan = enhancer.run_once()
        print("\n" + "=" * 60)
        print("📋 增强计划摘要:")
        print("=" * 60)
        print(json.dumps(plan, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
