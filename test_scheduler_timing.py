#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import schedule
from datetime import datetime

def test_scheduler_timing():
    """测试调度器的时间间隔"""
    
    def test_job():
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}] 测试任务执行")
    
    print("开始测试调度器时间间隔...")
    print("设置任务每1分钟执行一次")
    
    # 设置任务每1分钟执行一次
    schedule.every(1).minutes.do(test_job).tag("test")
    
    # 记录开始时间
    start_time = time.time()
    execution_count = 0
    max_executions = 3  # 最多执行3次
    
    print("等待任务执行...")
    
    while execution_count < max_executions:
        schedule.run_pending()
        time.sleep(1)
        
        # 检查是否有新任务执行
        if hasattr(schedule, '_last_run') and schedule._last_run:
            execution_count += 1
            current_time = time.time()
            elapsed = current_time - start_time
            print(f"第{execution_count}次执行，耗时: {elapsed:.2f}秒")
    
    print("测试完成！")
    print("预期：每次执行间隔应该接近60秒")
    print("实际：请检查上面的时间间隔")

if __name__ == "__main__":
    test_scheduler_timing()
