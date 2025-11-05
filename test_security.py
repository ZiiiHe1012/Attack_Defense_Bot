"""
安全检测系统批量集成测试脚本
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

from main import process_query, conversation_manager


class SecurityBatchTester:
    """安全检测系统批量集成测试"""

    def __init__(self, test_data_path=None):
        if test_data_path is None:
            # 默认：当前文件同级目录下的 test_data/test_cases.json
            test_data_path = Path(__file__).parent / "test_data" / "test_cases.json"

        self.test_data_path: Path = Path(test_data_path)
        self.test_cases = self._load_test_cases()
        self.results = []
        self.summary = {}

    def _load_test_cases(self):
        """加载测试用例"""
        try:
            with open(self.test_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cases = data.get("test_cases", [])
            print(f"从 {self.test_data_path} 加载测试用例 {len(cases)} 条")
            return cases
        except Exception as e:
            print(f"加载测试用例失败: {e}")
            print(f"尝试的路径: {self.test_data_path}")
            return []

    def run_integration_tests(self, limit=None):
        """运行集成测试（两轮判断）"""
        total_cases = len(self.test_cases) if limit is None else min(limit, len(self.test_cases))

        print("=" * 80)
        print("安全检测系统测试 - 集成测试模式（两轮判断）")
        print("=" * 80)
        print(f"测试用例数量: {total_cases}")
        print("说明：每个用例执行两轮判断，第二轮结果作为最终判定\n")

        self.results = []
        passed_count = 0

        for idx, case in enumerate(self.test_cases[:total_cases], start=1):
            case_id = case.get("id", f"case_{idx}")
            desc = case.get("description", "")
            query = case.get("query", "")
            expected_block = bool(case.get("expected_block", False))

            print("-" * 80)
            print(f"[{idx}/{total_cases}] 用例 {case_id} - {desc}")
            print(f"  查询内容 : {query}")
            print(f"  期望行为 : {'拦截' if expected_block else '通过'}")

            try:
                # 每个用例开始前，清空历史，保证用例之间互不影响
                conversation_manager.clear()

                # 第一轮判断：无上下文
                print("  第一轮判断: 调用 process_query（无历史）...")
                result_round1 = process_query(query)

                # 第二轮判断：在第一轮的对话基础上再次调用
                print("  第二轮判断: 调用 process_query（带历史）...")
                result_round2 = process_query(query)

                # 最终以第二轮结果为准
                final_result = result_round2
                actual_block = not final_result.get("success", False)

                print(f"  实际行为 : {'拦截' if actual_block else '通过'}")

                passed = (actual_block == expected_block)
                if passed:
                    print("  结果     : ✓ PASS")
                    passed_count += 1
                else:
                    print("  结果     : ✗ FAIL")
                    if actual_block and not expected_block:
                        print("  说明     : 误报 (应放行却拦截)")
                    elif (not actual_block) and expected_block:
                        print("  说明     : 漏报 (应拦截却放行)")
                    err = final_result.get("error", "")
                    if err:
                        print(f"  拦截原因 : {err}")

                self.results.append(
                    {
                        "id": case_id,
                        "description": desc,
                        "query": query,
                        "expected_block": expected_block,
                        "actual_block": actual_block,
                        "passed": passed,
                        # 保留两轮结果，不覆盖
                        "round1": {
                            "success": result_round1.get("success", False),
                            "error": result_round1.get("error", ""),
                            "logs": result_round1.get("logs", []),
                        },
                        "round2": {
                            "success": result_round2.get("success", False),
                            "error": result_round2.get("error", ""),
                            "logs": result_round2.get("logs", []),
                        },
                    }
                )

            except Exception as e:
                print("  结果     : ✗ ERROR")
                print(f"  异常     : {e}")
                self.results.append(
                    {
                        "id": case_id,
                        "description": desc,
                        "query": query,
                        "expected_block": expected_block,
                        "actual_block": None,
                        "passed": False,
                        "error": str(e),
                    }
                )

        # 统计与汇总
        total = len(self.results)
        pass_rate = (passed_count / total * 100) if total > 0 else 0.0

        false_positive = 0  # 误报：应放行却拦截
        false_negative = 0  # 漏报：应拦截却放行

        for r in self.results:
            if not r.get("passed", False):
                actual_block = r.get("actual_block")
                if actual_block is None:
                    continue
                if r.get("expected_block") is False and actual_block is True:
                    false_positive += 1
                elif r.get("expected_block") is True and actual_block is False:
                    false_negative += 1

        print("\n集成测试摘要")
        print("-" * 80)
        print(f"  通过用例数 : {passed_count}/{total} ({pass_rate:.1f}%)")
        print(f"  误报数     : {false_positive}")
        print(f"  漏报数     : {false_negative}")

        self.summary = {
            "total_cases": total,
            "passed": passed_count,
            "pass_rate": pass_rate,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def save_results(self, output_dir=None):
        """保存测试结果到 JSON 文件，不覆盖历史结果"""
        if output_dir is None:
            output_dir = Path(__file__).parent

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = output_dir / f"test_results_integration_{ts}.json"

        payload = {
            "summary": self.summary,
            "results": self.results,
        }

        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存至: {out_file}")
        except Exception as e:
            print(f"\n保存测试结果失败: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="安全检测系统批量集成测试脚本")
    parser.add_argument(
        "--test-data",
        type=str,
        default=None,
        help="测试用例 JSON 路径，默认为 ./test_data/test_cases.json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="仅测试前 N 条用例（调试用）",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    test_data_path = Path(args.test_data) if args.test_data is not None else None

    tester = SecurityBatchTester(test_data_path=test_data_path)
    if not tester.test_cases:
        print("没有加载到任何测试用例，退出。")
        sys.exit(1)

    tester.run_integration_tests(limit=args.limit)
    tester.save_results()


if __name__ == "__main__":
    main()
