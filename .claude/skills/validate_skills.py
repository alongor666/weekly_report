#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills 验证工具
检查所有skills是否符合Claude Code最佳实践
"""

from pathlib import Path
import yaml
import re

class SkillValidator:
    """Skills验证器"""

    def __init__(self, skills_dir="."):
        self.skills_dir = Path(skills_dir)
        self.results = []

    def validate_all(self):
        """验证所有skills"""
        print("🔍 开始验证Skills...")
        print("=" * 60)

        # 查找所有SKILL.md文件
        skill_files = list(self.skills_dir.rglob("SKILL.md"))

        if not skill_files:
            print("❌ 未找到任何SKILL.md文件")
            return False

        print(f"✅ 发现 {len(skill_files)} 个skill文件\n")

        all_passed = True
        for skill_file in skill_files:
            passed = self.validate_skill(skill_file)
            if not passed:
                all_passed = False

        # 打印总结
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ 所有Skills验证通过！")
        else:
            print("⚠️  部分Skills存在问题，请查看上方详情")

        return all_passed

    def validate_skill(self, skill_file):
        """验证单个skill"""
        skill_name = skill_file.parent.name
        print(f"📋 验证: {skill_name}")

        passed = True
        issues = []

        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 检查YAML frontmatter
        if not content.startswith('---'):
            issues.append("❌ 缺少YAML frontmatter")
            passed = False
        else:
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                try:
                    frontmatter = yaml.safe_load(yaml_match.group(1))

                    # 检查name字段
                    if 'name' not in frontmatter:
                        issues.append("❌ 缺少name字段")
                        passed = False
                    else:
                        name = frontmatter['name']
                        if len(name) > 64:
                            issues.append(f"❌ name长度{len(name)}超过64字符")
                            passed = False
                        if not re.match(r'^[a-z0-9-]+$', name):
                            issues.append("❌ name格式不正确（应为小写字母+数字+连字符）")
                            passed = False

                    # 检查description字段
                    if 'description' not in frontmatter:
                        issues.append("❌ 缺少description字段")
                        passed = False
                    else:
                        desc = frontmatter['description']
                        if len(desc) > 1024:
                            issues.append(f"❌ description长度{len(desc)}超过1024字符")
                            passed = False
                        if len(desc) == 0:
                            issues.append("❌ description为空")
                            passed = False

                except yaml.YAMLError as e:
                    issues.append(f"❌ YAML格式错误: {e}")
                    passed = False

        # 2. 检查文件行数
        line_count = len(content.split('\n'))
        if line_count > 500:
            issues.append(f"⚠️  文件行数{line_count}超过建议的500行")
            # 不标记为失败，只是警告

        # 3. 检查必要章节
        required_sections = ['核心功能', '立即使用']
        for section in required_sections:
            if f'## {section}' not in content and f'# {section}' not in content:
                issues.append(f"⚠️  建议添加「{section}」章节")

        # 4. 检查reference目录
        reference_dir = skill_file.parent / 'reference'
        if reference_dir.exists():
            ref_files = list(reference_dir.glob('*.md'))
            print(f"  ✅ 参考文档: {len(ref_files)}个")
        else:
            print(f"  ℹ️  无参考文档目录")

        # 5. 检查scripts目录
        scripts_dir = skill_file.parent / 'scripts'
        if scripts_dir.exists():
            script_files = list(scripts_dir.glob('*.py'))
            print(f"  ✅ 工具脚本: {len(script_files)}个")
        else:
            print(f"  ℹ️  无脚本目录")

        # 打印问题
        if issues:
            for issue in issues:
                print(f"  {issue}")

        if passed:
            print(f"  ✅ 验证通过")
        else:
            print(f"  ❌ 验证失败")

        print()
        return passed

    def check_structure(self):
        """检查整体目录结构"""
        print("\n📁 检查目录结构...")
        print("=" * 60)

        # 检查README.md
        readme = self.skills_dir / "README.md"
        if readme.exists():
            print("✅ 总索引: README.md 存在")
        else:
            print("⚠️  建议创建 README.md 总索引")

        # 统计skills
        skill_dirs = [d for d in self.skills_dir.iterdir()
                     if d.is_dir() and (d / "SKILL.md").exists()]

        print(f"✅ Skills总数: {len(skill_dirs)}")

        # 检查每个skill的完整性
        for skill_dir in skill_dirs:
            print(f"\n📦 {skill_dir.name}:")

            # 检查SKILL.md
            if (skill_dir / "SKILL.md").exists():
                print("  ✅ SKILL.md")
            else:
                print("  ❌ 缺少SKILL.md")

            # 检查reference/
            if (skill_dir / "reference").exists():
                ref_count = len(list((skill_dir / "reference").glob("*.md")))
                print(f"  ✅ reference/ ({ref_count}个文档)")
            else:
                print("  ℹ️  无reference/")

            # 检查scripts/
            if (skill_dir / "scripts").exists():
                script_count = len(list((skill_dir / "scripts").glob("*.py")))
                print(f"  ✅ scripts/ ({script_count}个脚本)")
            else:
                print("  ℹ️  无scripts/")


def main():
    """主函数"""
    import sys

    # 获取skills目录路径
    if len(sys.argv) > 1:
        skills_dir = sys.argv[1]
    else:
        skills_dir = Path(__file__).parent

    validator = SkillValidator(skills_dir)

    # 验证所有skills
    all_passed = validator.validate_all()

    # 检查目录结构
    validator.check_structure()

    # 返回结果
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
