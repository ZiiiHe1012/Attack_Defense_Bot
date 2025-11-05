"""
安全检测系统批量测试脚本
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 根据实际情况导入
try:
    from main import process_query, conversation_manager
except ImportError:
    print("错误: 无法导入 main.py，请确保 main.py 在当前目录")
    sys.exit(1)


class SecurityBatchTester:
    """安全检测系统批量测试"""

    def __init__(self, test_data_path=None, output_dir=None):
        if test_data_path is None:
            test_data_path = Path(__file__).parent / "test_data" / "test_cases.json"

        self.test_data_path: Path = Path(test_data_path)
        self.test_cases = self._load_test_cases()
        self.results = []
        self.summary = {}
        
        # 设置输出目录和文件
        if output_dir is None:
            output_dir = Path(__file__).parent
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建带时间戳的输出文件
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.output_dir / f"test_results_v3_{ts}.json"
        
        # 初始化输出文件
        self._init_output_file()

    def _load_test_cases(self):
        """加载测试用例"""
        try:
            with open(self.test_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cases = data.get("test_cases", [])
            print(f"✓ 从 {self.test_data_path} 加载测试用例 {len(cases)} 条")
            return cases
        except FileNotFoundError:
            print(f"✗ 测试用例文件不存在: {self.test_data_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"✗ 测试用例 JSON 格式错误: {e}")
            return []
        except Exception as e:
            print(f"✗ 加载测试用例失败: {e}")
            return []
    
    def _init_output_file(self):
        """初始化输出文件"""
        initial_data = {
            "version": "3.0",
            "start_time": datetime.now().isoformat(timespec="seconds"),
            "status": "running",
            "summary": {},
            "results": []
        }
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            print(f"✓ 测试结果将实时保存至: {self.output_file}")
        except Exception as e:
            print(f"  无法创建输出文件: {e}")
    
    def _append_result(self, result_data):
        """追加单个测试结果到文件"""
        try:
            # 读取现有数据
            with open(self.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 追加新结果
            data["results"].append(result_data)
            data["last_update"] = datetime.now().isoformat(timespec="seconds")
            
            # 写回文件
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"    写入结果失败: {e}")
    
    def _update_summary(self):
        """更新测试摘要到文件"""
        try:
            # 读取现有数据
            with open(self.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 更新摘要
            data["summary"] = self.summary
            data["status"] = "completed"
            data["end_time"] = datetime.now().isoformat(timespec="seconds")
            
            # 写回文件
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  更新摘要失败: {e}")

    def run_tests(self, limit=None, verbose=False):
        """
        运行测试
        
        Args:
            limit: 仅测试前N条用例
            verbose: 是否显示详细日志
        """
        total_cases = len(self.test_cases) if limit is None else min(limit, len(self.test_cases))

        print("\n" + "=" * 80)
        print("安全检测系统测试 v3.0 - 真实环境测试（实时写入）")
        print("=" * 80)
        print(f"测试用例数量: {total_cases}")
        print("说明：")
        print("  • 每个用例调用一次 process_query()")
        print("  • process_query() 内部自动执行两轮检测")
        print("  • 真实反映生产环境的实际行为")
        print("  • 每个用例完成后立即写入结果文件\n")

        self.results = []
        passed_count = 0

        for idx, case in enumerate(self.test_cases[:total_cases], start=1):
            case_id = case.get("id", f"case_{idx}")
            desc = case.get("description", "")
            query = case.get("query", "")
            expected_block = bool(case.get("expected_block", False))

            print("-" * 80)
            print(f"[{idx}/{total_cases}] 用例 {case_id}")
            print(f"  描述     : {desc}")
            print(f"  查询     : {query}")
            print(f"  期望     : {' 拦截' if expected_block else ' 放行'}")

            try:
                # 每个用例开始前，清空历史
                conversation_manager.clear()

                # 调用 process_query（内部会自动两轮检测）
                result = process_query(query)
                
                # 获取最终判定结果
                actual_block = result.get("blocked", False)
                
                # 获取两轮检测的详细信息
                round1_blocked = result.get("round1_blocked", None)
                round2_blocked = result.get("round2_blocked", None)
                rounds_consistent = result.get("rounds_consistent", True)
                
                # 显示两轮检测情况
                if round1_blocked is not None and round2_blocked is not None:
                    print(f"  第1轮    : {' 拦截' if round1_blocked else ' 放行'}")
                    print(f"  第2轮    : {' 拦截' if round2_blocked else ' 放行'}")
                    if not rounds_consistent:
                        print(f"    两轮结果不一致")
                
                print(f"  最终     : {' 拦截' if actual_block else ' 放行'}")

                # 判断是否通过
                passed = (actual_block == expected_block)
                
                if passed:
                    print(f"  结果     : ✓ PASS")
                    passed_count += 1
                else:
                    print(f"  结果     : ✗ FAIL")
                    if actual_block and not expected_block:
                        print(f"  类型     : 误拦截 (False Positive)")
                        print(f"  说明     : 应该放行但被拦截了")
                    elif (not actual_block) and expected_block:
                        print(f"  类型     : 漏拦截 (False Negative)")
                        print(f"  说明     : 应该拦截但放行了")
                    
                    # 显示答案预览
                    answer = result.get("answer", "")
                    if answer:
                        preview = answer[:100] + "..." if len(answer) > 100 else answer
                        print(f"  回复预览 : {preview}")
                
                # 显示检测日志
                if verbose and result.get("logs"):
                    print("  检测日志:")
                    for log in result.get("logs", []):
                        status_icon = "✓" if log["status"] == "success" else "✗" if log["status"] == "fail" else "⚠" if log["status"] == "warning" else "ℹ"
                        print(f"    {status_icon} {log['step']}: {log['message']}")

                # 保存结果
                result_data = {
                    "id": case_id,
                    "query": query,
                    "expected": "拦截" if expected_block else "放行",
                    "actual": "拦截" if actual_block else "放行",
                    "passed": passed,
                }
                
                # 可选：添加失败原因（仅失败时）
                if not passed:
                    result_data["reason"] = "误拦截" if (actual_block and not expected_block) else "漏拦截"
                
                # 可选：添加两轮信息（仅不一致时）
                if round1_blocked is not None and round2_blocked is not None:
                    if not rounds_consistent:
                        result_data["detail"] = {
                            "round1": "拦截" if round1_blocked else "放行",
                            "round2": "拦截" if round2_blocked else "放行"
                        }
                
                self.results.append(result_data)
                
                # 实时写入结果
                self._append_result(result_data)

            except Exception as e:
                print(f"  结果     : ✗ ERROR")
                print(f"  异常     : {e}")
                import traceback
                if verbose:
                    traceback.print_exc()
                
                result_data = {
                    "id": case_id,
                    "query": query,
                    "expected": "拦截" if expected_block else "放行",
                    "actual": "ERROR",
                    "passed": False,
                    "error": str(e)
                }
                
                self.results.append(result_data)
                
                # 实时写入错误结果
                self._append_result(result_data)

        # 统计与汇总
        self._print_summary()
        
        # 更新最终摘要
        self._update_summary()

    def _print_summary(self):
        """打印测试摘要"""
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r.get("passed", False))
        pass_rate = (passed_count / total * 100) if total > 0 else 0.0

        false_positive = 0  # 误拦截
        false_negative = 0  # 漏拦截
        errors = 0  # 执行错误
        inconsistent = 0  # 两轮结果不一致

        for r in self.results:
            # 统计错误
            if r.get("actual") == "ERROR":
                errors += 1
                continue
            
            # 统计不一致的情况
            if "detail" in r:
                inconsistent += 1
            
            # 统计误拦截和漏拦截
            if not r.get("passed", False):
                reason = r.get("reason", "")
                if reason == "误拦截":
                    false_positive += 1
                elif reason == "漏拦截":
                    false_negative += 1

        print("\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        print(f"  总用例数      : {total}")
        print(f"  ✓ 通过        : {passed_count} ({pass_rate:.1f}%)")
        print(f"  ✗ 失败        : {total - passed_count - errors}")
        print(f"  ⚠ 执行错误    : {errors}")
        print()
        print(f"  误拦截 (FP)   : {false_positive} (应放行却拦截)")
        print(f"  漏拦截 (FN)   : {false_negative} (应拦截却放行)")
        print()
        print(f"  两轮不一致    : {inconsistent} (检测不稳定)")
        print()
        
        # 计算精确率和召回率
        total_should_block = sum(1 for r in self.results if r.get("expected") == "拦截")
        total_should_pass = sum(1 for r in self.results if r.get("expected") == "放行")
        
        if total_should_pass > 0:
            precision = ((total_should_pass - false_positive) / total_should_pass * 100)
            print(f"  放行准确率    : {precision:.1f}% ({total_should_pass - false_positive}/{total_should_pass})")
        
        if total_should_block > 0:
            recall = ((total_should_block - false_negative) / total_should_block * 100)
            print(f"  拦截准确率    : {recall:.1f}% ({total_should_block - false_negative}/{total_should_block})")
        
        print("=" * 80)

        self.summary = {
            "total": total,
            "passed": passed_count,
            "failed": total - passed_count - errors,
            "errors": errors,
            "pass_rate": f"{pass_rate:.1f}%",
            "false_positive": false_positive,
            "false_negative": false_negative,
            "inconsistent": inconsistent,
        }


    def print_failed_cases(self):
        """打印失败的用例详情"""
        failed_cases = [r for r in self.results if not r.get("passed", False) and r.get("actual") != "ERROR"]
        
        if not failed_cases:
            print("\n 所有用例都通过了！")
            return
        
        print("\n" + "=" * 80)
        print(f"失败用例详情 ({len(failed_cases)} 个)")
        print("=" * 80)
        
        for i, case in enumerate(failed_cases, 1):
            print(f"\n[{i}] {case['id']}")
            print(f"  查询: {case['query']}")
            print(f"  期望: {case['expected']}")
            print(f"  实际: {case['actual']}")
            print(f"  类型: {case.get('reason', '未知')}")
            
            # 显示两轮情况（如果有）
            if 'detail' in case:
                detail = case['detail']
                print(f"  第1轮: {detail['round1']}")
                print(f"  第2轮: {detail['round2']}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="安全检测系统批量测试脚本 v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_security_v3.py                    # 运行所有测试用例
  python test_security_v3.py --limit 10         # 只测试前10个用例
  python test_security_v3.py --verbose          # 显示详细日志
  python test_security_v3.py --show-failed      # 显示失败用例详情
        """
    )
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细的检测日志",
    )
    parser.add_argument(
        "--show-failed",
        action="store_true",
        help="显示失败用例的详细信息",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="测试结果保存目录，默认为当前目录",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    test_data_path = Path(args.test_data) if args.test_data is not None else None
    output_dir = Path(args.output_dir) if args.output_dir is not None else None

    print("\n 安全检测系统测试工具")
    print("=" * 80)
    
    tester = SecurityBatchTester(test_data_path=test_data_path, output_dir=output_dir)
    
    if not tester.test_cases:
        print("\n✗ 没有加载到任何测试用例，退出。")
        print("请确保测试用例文件存在：test_data/test_cases.json")
        sys.exit(1)

    tester.run_tests(limit=args.limit, verbose=args.verbose)
    
    if args.show_failed:
        tester.print_failed_cases()
    
    tester.save_results(output_dir=output_dir)
    
    # 返回退出码
    if tester.summary.get("passed", 0) == tester.summary.get("total_cases", 0):
        print("\n 所有测试通过！")
        sys.exit(0)
    else:
        print("\n  部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
