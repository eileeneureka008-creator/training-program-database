#!/usr/bin/env python
"""CLI 命令行查询界面"""
import cmd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATABASE_URL
from src.database.models import get_session
from src.queries.basic import (
    get_required_courses, get_course_info, get_total_credits,
    get_majors_by_course, get_school_plans_overview, search_courses,
    get_all_schools, get_all_majors
)
from src.queries.cross_compare import (
    compare_major_courses, compare_credits, compare_course_structure, list_common_courses
)
from src.nl2sql.engine import NL2SQLEngine


class CultivationCLI(cmd.Cmd):
    intro = """
╔══════════════════════════════════════════╗
║     培养方案数据库系统 - CLI 查询界面     ║
║  西南财经大学 & 上海财经大学 培养方案      ║
╚══════════════════════════════════════════╝
输入 help 查看命令列表，输入 quit 退出
"""
    prompt = "查询> "

    def __init__(self):
        super().__init__()
        self.session = get_session(DATABASE_URL)

    def do_quit(self, arg):
        """退出系统"""
        self.session.close()
        print("再见！")
        return True

    def do_exit(self, arg):
        """退出系统"""
        return self.do_quit(arg)

    # ── 查询命令 ──

    def do_schools(self, arg):
        """列出所有学院：schools"""
        schools = get_all_schools(self.session)
        print(f"\n{'大学':<16} {'学院':<12} ID")
        print("-" * 44)
        for s in schools:
            print(f"{s['university_name']:<16} {s['name']:<12} {s['id']}")

    def do_majors(self, arg):
        """列出所有专业：majors"""
        majors = get_all_majors(self.session)
        print(f"\n{'大学':<16} {'学院':<12} {'专业':<16} {'代码':<12} ID")
        print("-" * 64)
        for m in majors:
            print(f"{m['university_name']:<16} {m['school_name']:<12} {m['name']:<16} {m.get('code',''):<12} {m['id']}")

    def do_required(self, arg):
        """查询某专业必修课：required <专业名>  或  required id:<专业ID>"""
        major = self._find_major(arg)
        if not major:
            return
        courses = get_required_courses(self.session, major.id)
        print(f"\n【{major.name}】必修课列表（共 {len(courses)} 门）：")
        print(f"{'编号':<10} {'课程名称':<24} {'学分':<6} {'学时':<6} {'学期':<8} {'类别':<12}")
        print("-" * 72)
        for c in courses:
            print(f"{c['code']:<10} {c['name']:<24} {c['credits']:<6} {c['hours_total']:<6} 第{c['semester']}学期 {'':<2} {c['category']:<12}")

    def do_credits(self, arg):
        """查询某专业总学分：credits <专业名>  或  credits id:<专业ID>"""
        major = self._find_major(arg)
        if not major:
            return
        info = get_total_credits(self.session, major.id)
        print(f"\n【{info['major_name']}】学分统计：")
        print(f"  总学分要求: {info['total_credits_required']}")
        print(f"  必修学分合计: {info['required_credits_sum']}")
        print(f"  选修学分合计: {info['elective_credits_sum']}")
        print(f"\n  分类统计:")
        for cat in info['category_breakdown']:
            print(f"    {cat['category'] or '-'}: {cat['course_count']}门课, {cat['credits']}学分")

    def do_course(self, arg):
        """查询课程信息：course <课程名或编号>"""
        if not arg:
            print("请提供课程名或编号，如：course 高等数学")
            return
        # 先按名称搜索
        results = search_courses(self.session, arg.strip())
        if not results:
            print(f"未找到匹配的课程: {arg}")
            return
        # 取第一个匹配
        c = get_course_info(self.session, course_code=results[0]['code'])
        print(f"\n【{c['name']}】({c['name_en'] or ''})")
        print(f"  编号: {c['code']}")
        print(f"  学分: {c['credits']}")
        print(f"  理论学时: {c['hours_theory']} | 实践学时: {c['hours_practice']} | 总学时: {c['hours_total']}")
        print(f"  类型: {c['course_type']}")
        print(f"  描述: {c['description'] or '无'}")

        # 查询开设此课程的专业
        majors_info = get_majors_by_course(self.session, course_code=c['code'])
        if majors_info:
            print(f"\n  开设此课程的专业:")
            for m in majors_info:
                req = "必修" if m['is_required'] else "选修"
                print(f"    {m['university_name']} - {m['school_name']} - {m['major_name']} ({req})")

    def do_search(self, arg):
        """模糊搜索课程：search <关键词>"""
        if not arg:
            print("请提供搜索关键词")
            return
        results = search_courses(self.session, arg.strip())
        print(f"\n搜索【{arg}】结果（共 {len(results)} 条）：")
        print(f"{'编号':<10} {'课程名称':<24} {'学分':<6} {'学时':<6} {'类型':<8}")
        print("-" * 56)
        for c in results:
            print(f"{c['code']:<10} {c['name']:<24} {c['credits']:<6} {c['hours_total']:<6} {c['course_type'] or '':<8}")

    def do_school(self, arg):
        """查询学院概览：school <学院名>  或  school id:<学院ID>"""
        schools = get_all_schools(self.session)
        target = None
        if arg.startswith("id:"):
            sid = int(arg.split(":")[1])
            target = next((s for s in schools if s['id'] == sid), None)
        else:
            target = next((s for s in schools if arg.strip() in s['name']), None)

        if not target:
            print(f"未找到学院: {arg}")
            return

        info = get_school_plans_overview(self.session, target['id'])
        print(f"\n【{info['school_name']}】- {info['university_name']}")
        print(f"{'专业名称':<16} {'代码':<12} {'学位':<8} {'学制':<6} {'总学分':<8} {'必修课':<8} {'选修课':<8}")
        print("-" * 72)
        for m in info['majors']:
            print(f"{m['major_name']:<16} {m['code'] or '':<12} {m['degree_type'] or '':<8} {m['duration'] or '':<6} {m['total_credits']:<8} {m['required_courses_count']:<8} {m['elective_courses_count']:<8}")

    # ── 跨校对比命令 ──

    def do_compare(self, arg):
        """跨校对比专业：compare <专业名>  如：compare 金融学"""
        if not arg:
            print("请提供专业名，如：compare 金融学")
            return
        major_name = arg.strip()

        print(f"\n╔══ 跨校对比【{major_name}】══╗")

        # 课程对比
        result = compare_major_courses(self.session, major_name)
        if "error" in result:
            print(f"  {result['error']}")
        else:
            print(f"\n  课程设置对比:")
            print(f"    西南财经大学: {result['swufe_info']['course_count']}门课, 总学分{result['swufe_info']['total_credits']}")
            print(f"    上海财经大学: {result['sufe_info']['course_count']}门课, 总学分{result['sufe_info']['total_credits']}")
            print(f"    共同课程: {result['common_count']}门")
            print(f"    仅西财开设: {result['swufe_only_count']}门")
            print(f"    仅上财开设: {result['sufe_only_count']}门")

            if result['common_count'] > 0:
                print(f"\n  共同课程:")
                for c in result['common_courses'][:10]:
                    print(f"    {c['name']} (西财{c['swufe_credits']}学分 / 上财{c['sufe_credits']}学分)")
                if result['common_count'] > 10:
                    print(f"    ... 共{result['common_count']}门")

        # 学分对比
        credit_result = compare_credits(self.session, major_name)
        print(f"\n  学分对比:")
        for c in credit_result.get('comparisons', []):
            if 'error' in c:
                print(f"    {c['university']}: {c['error']}")
            else:
                print(f"    {c['university']}: 总{c['total_credits']}学分 (必修{c['required_credits']}/选修{c['elective_credits']})")
        if 'credit_difference' in credit_result:
            print(f"  学分差: {credit_result['credit_difference']}")
        print("╚" + "═" * 30 + "╝")

    # ── 自然语言查询 ──

    def do_ask(self, arg):
        """自然语言查询：ask <中文问题>  如：ask 金融学有哪些必修课"""
        if not arg:
            print("请提供查询语句，如：ask 金融学有哪些必修课")
            return
        engine = NL2SQLEngine(self.session)
        result = engine.execute(arg.strip())
        self._print_nl_result(result)

    # ── 帮助 ──

    def do_help(self, arg):
        """显示帮助"""
        help_text = """
╔══ 命令列表 ════════════════════════════════════════╗
║ 基础查询：                                           ║
║   schools        列出所有学院                        ║
║   majors         列出所有专业                        ║
║   required   <专业名|id:ID>   某专业必修课列表        ║
║   credits    <专业名|id:ID>   某专业总学分统计        ║
║   course     <课程名|编号>    课程详细信息            ║
║   search     <关键词>         模糊搜索课程            ║
║   school     <学院名|id:ID>   学院培养方案概览        ║
║                                                      ║
║ 跨校对比：                                           ║
║   compare    <专业名>         两校课程与学分对比       ║
║                                                      ║
║ 自然语言查询：                                       ║
║   ask        <中文问题>       自动识别意图查询        ║
║                                                      ║
║ 系统：                                               ║
║   help                       显示此帮助              ║
║   quit / exit                退出系统                ║
╚══════════════════════════════════════════════════════╝
"""
        print(help_text)

    def _find_major(self, arg):
        """解析专业参数，支持名称或 id: 前缀"""
        if not arg:
            print("请提供专业名或专业ID，如：required 金融学 或 required id:1")
            return None
        if arg.startswith("id:"):
            mid = int(arg.split(":")[1])
            from src.database.models import Major
            return self.session.query(Major).filter_by(id=mid).first()
        else:
            from src.database.models import Major
            return self.session.query(Major).filter_by(name=arg.strip()).first()

    def _print_nl_result(self, result):
        """格式化打印 NL 查询结果"""
        import json
        print(f"\n意图: {result.get('intent', 'unknown')}")
        if 'error' in result:
            print(f"错误: {result['error']}")
            if 'hint' in result:
                print(f"提示: {result['hint']}")
            if 'recognized_entities' in result:
                print(f"识别实体: {result['recognized_entities']}")
            return
        print(json.dumps(result.get('results', {}), ensure_ascii=False, indent=2))


def main():
    CultivationCLI().cmdloop()


if __name__ == "__main__":
    main()
