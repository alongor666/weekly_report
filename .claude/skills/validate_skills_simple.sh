#!/bin/bash
# Skills 简易验证脚本

echo "🔍 验证Skills目录结构..."
echo "======================================"

# 检查总索引
if [ -f "README.md" ]; then
    echo "✅ 总索引: README.md 存在"
else
    echo "⚠️  建议创建 README.md"
fi

# 统计skills
skill_count=0
for dir in */; do
    if [ -f "${dir}SKILL.md" ]; then
        ((skill_count++))
    fi
done

echo "✅ Skills总数: $skill_count"
echo ""

# 检查每个skill
for dir in */; do
    # 跳过非目录
    [ ! -d "$dir" ] && continue

    skill_name="${dir%/}"

    # 跳过archive等特殊目录
    [[ "$skill_name" == "archive" ]] && continue

    # 检查SKILL.md
    if [ -f "${dir}SKILL.md" ]; then
        echo "📋 验证: $skill_name"

        # 检查文件行数
        line_count=$(wc -l < "${dir}SKILL.md")
        if [ $line_count -gt 500 ]; then
            echo "  ⚠️  文件行数${line_count}超过建议的500行"
        else
            echo "  ✅ 文件行数: ${line_count}行"
        fi

        # 检查YAML frontmatter
        if head -1 "${dir}SKILL.md" | grep -q "^---$"; then
            echo "  ✅ YAML frontmatter存在"

            # 检查name字段
            if grep -q "^name:" "${dir}SKILL.md"; then
                name_line=$(grep "^name:" "${dir}SKILL.md" | head -1)
                echo "  ✅ $name_line"
            else
                echo "  ❌ 缺少name字段"
            fi

            # 检查description字段
            if grep -q "^description:" "${dir}SKILL.md"; then
                echo "  ✅ description字段存在"
            else
                echo "  ❌ 缺少description字段"
            fi
        else
            echo "  ❌ 缺少YAML frontmatter"
        fi

        # 检查reference目录
        if [ -d "${dir}reference" ]; then
            ref_count=$(ls -1 "${dir}reference"/*.md 2>/dev/null | wc -l)
            echo "  ✅ reference/: ${ref_count}个文档"
        else
            echo "  ℹ️  无reference/目录"
        fi

        # 检查scripts目录
        if [ -d "${dir}scripts" ]; then
            script_count=$(ls -1 "${dir}scripts"/*.py 2>/dev/null | wc -l)
            echo "  ✅ scripts/: ${script_count}个脚本"
        else
            echo "  ℹ️  无scripts/目录"
        fi

        echo "  ✅ 验证通过"
        echo ""
    fi
done

echo "======================================"
echo "✅ Skills验证完成！"
