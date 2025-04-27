#!/bin/bash
# 评论监控脚本
# 可以添加到crontab中定期执行，例如每天晚上10点执行：
# 0 22 * * * /home/nkuwiki/nkuwiki-shell/nkuwiki/comment_monitor.sh

# 设置工作目录
WORK_DIR="/home/nkuwiki/nkuwiki-shell/nkuwiki"
LOG_DIR="${WORK_DIR}/logs"
REPORT_DIR="${WORK_DIR}/reports"

# 创建日志和报告目录
mkdir -p ${LOG_DIR}
mkdir -p ${REPORT_DIR}

# 设置日志文件
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/comment_monitor_${TIMESTAMP}.log"

# 记录开始时间
echo "开始执行评论监控 - $(date)" > ${LOG_FILE}

# 进入工作目录
cd ${WORK_DIR}

# 运行评论报告脚本
echo "正在生成评论分析报告..." >> ${LOG_FILE}
python3 comment_report.py >> ${LOG_FILE} 2>&1
REPORT_STATUS=$?

# 检查脚本执行状态
if [ ${REPORT_STATUS} -eq 0 ]; then
    echo "评论分析报告生成成功" >> ${LOG_FILE}
    
    # 查找最新的报告文件
    LATEST_REPORT=$(ls -t ${REPORT_DIR}/comment_report_*.txt | head -1)
    
    # 检查敏感评论
    SENSITIVE_COUNT=$(grep -c "敏感评论" ${LATEST_REPORT})
    NORMAL_SENSITIVE_COUNT=$(grep -c "状态: 正常" ${LATEST_REPORT})
    
    echo "共发现 ${SENSITIVE_COUNT} 条敏感评论，其中 ${NORMAL_SENSITIVE_COUNT} 条状态为正常" >> ${LOG_FILE}
    
    # 如果正常状态的敏感评论超过10条，发送警告
    if [ ${NORMAL_SENSITIVE_COUNT} -gt 10 ]; then
        echo "警告：发现大量未处理的敏感评论，请及时审核！" >> ${LOG_FILE}
        # 这里可以添加发送邮件或其他通知的命令
    fi
else
    echo "评论分析报告生成失败，错误码: ${REPORT_STATUS}" >> ${LOG_FILE}
fi

# 记录结束时间
echo "评论监控执行完成 - $(date)" >> ${LOG_FILE}

# 保留30天的日志和报告文件
find ${LOG_DIR} -name "comment_monitor_*.log" -mtime +30 -delete
find ${REPORT_DIR} -name "comment_report_*.txt" -mtime +30 -delete

exit ${REPORT_STATUS} 