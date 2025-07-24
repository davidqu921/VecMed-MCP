#!/bin/bash
unset EMAIL
export EMAIL="q2977991823@gmail.com"

# 创建输出目录
mkdir -p xml_batches

# 初始化批次编号
i=0

# 遍历所有分批后的pmid文件
for f in pmid_batch_*; do
    echo "⏳ 抓取 $f -> xml_batches/batch_$i.xml"
    
    # 如果已存在就跳过（防止中断后重复）
    if [ -f "xml_batches/batch_$i.xml" ]; then
        echo "✅ 批次 $i 已存在，跳过"
        ((i++))
        continue
    fi

    # 执行抓取
    cat "$f" | epost -db pubmed | efetch -format xml > "xml_batches/batch_$i.xml"

    echo "✅ 保存 xml_batches/batch_$i.xml"
    
    # 休眠防止IP限速
    sleep 1

    ((i++))
done

echo "🎉 全部抓取完毕"
